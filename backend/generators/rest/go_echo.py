import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from models import ServiceDefinition, ParameterLocation
from generators.base import BaseGenerator
from typing import Dict


GO_TYPE_MAP = {
    "string": "string",
    "int": "int",
    "float": "float64",
    "boolean": "bool",
    "date": "time.Time",
    "datetime": "time.Time",
    "void": "",
}


def _go_type(t: str) -> str:
    return GO_TYPE_MAP.get(t.lower(), t)


def _needs_time(service: ServiceDefinition) -> bool:
    for method in service.methods:
        for param in method.parameters:
            if param.type.lower() in ("date", "datetime"):
                return True
        if method.return_type.lower() in ("date", "datetime"):
            return True
    for model in service.models:
        for field in model.fields:
            if field.type.lower() in ("date", "datetime"):
                return True
    return False


def _go_default_value(t: str) -> str:
    lower = t.lower()
    if lower == "string":
        return '"ok"'
    elif lower == "int":
        return "0"
    elif lower == "float":
        return "0.0"
    elif lower == "boolean":
        return "false"
    elif lower in ("date", "datetime"):
        return "time.Now()"
    else:
        return f"{t}{{}}"


def _echo_http_method(http_method: str) -> str:
    return http_method.upper()


def _echo_route_path(path: str) -> str:
    # Convert {param} style to :param style for Echo
    import re
    return re.sub(r"\{(\w+)\}", r":\1", path)


class GoEchoGenerator(BaseGenerator):
    def __init__(self, service: ServiceDefinition):
        super().__init__(service)

    def generate(self) -> Dict[str, str]:
        files: Dict[str, str] = {}
        files["go.mod"] = self._go_mod()
        files["main.go"] = self._main_go()
        files[f"handlers/{self.pkg}_handler.go"] = self._handlers_go()
        files[f"models/{self.pkg}_models.go"] = self._models_go()
        files["README.md"] = self._readme()
        return files

    def _go_mod(self) -> str:
        return f"""module github.com/{self.pkg}

go 1.21

require github.com/labstack/echo/v4 v4.11.4
"""

    def _main_go(self) -> str:
        lines = [
            'package main',
            '',
            'import (',
            f'\t"github.com/{self.pkg}/handlers"',
            '\t"github.com/labstack/echo/v4"',
            '\t"github.com/labstack/echo/v4/middleware"',
            ')',
            '',
            'func main() {',
            '\te := echo.New()',
            '',
            '\te.Use(middleware.Logger())',
            '\te.Use(middleware.Recover())',
            '',
        ]

        for method in self.service.methods:
            echo_method = _echo_http_method(method.http_method)
            route_path = _echo_route_path(method.path)
            func_name = method.name[0].upper() + method.name[1:]
            lines.append(
                f'\te.{echo_method}("{route_path}", handlers.{func_name}Handler)'
            )

        lines += [
            '',
            '\te.Start(":8080")',
            '}',
        ]
        return '\n'.join(lines) + '\n'

    def _handlers_go(self) -> str:
        needs_time = _needs_time(self.service)

        lines = [
            'package handlers',
            '',
            'import (',
            '\t"net/http"',
        ]
        if needs_time:
            lines.append('\t"time"')
        lines += [
            '\t"github.com/labstack/echo/v4"',
            ')',
            '',
        ]

        for method in self.service.methods:
            func_name = method.name[0].upper() + method.name[1:]
            lines += [
                f'// {func_name}Handler handles {method.http_method} {method.path}',
            ]
            if method.description:
                lines.append(f'// {method.description}')
            lines += [
                f'func {func_name}Handler(c echo.Context) error {{',
            ]

            # Parse parameters
            for param in method.parameters:
                go_type = _go_type(param.type)
                if param.location == ParameterLocation.PATH:
                    if go_type == 'string':
                        lines.append(f'\t{param.name} := c.Param("{param.name}")')
                    else:
                        lines.append(f'\t{param.name}Str := c.Param("{param.name}")')
                        lines.append(f'\t_ = {param.name}Str // parse as needed')
                        lines.append(f'\tvar {param.name} {go_type}')
                elif param.location == ParameterLocation.QUERY:
                    if go_type == 'string':
                        lines.append(f'\t{param.name} := c.QueryParam("{param.name}")')
                    else:
                        lines.append(f'\t{param.name}Str := c.QueryParam("{param.name}")')
                        lines.append(f'\t_ = {param.name}Str // parse as needed')
                        lines.append(f'\tvar {param.name} {go_type}')
                elif param.location == ParameterLocation.BODY:
                    lines.append(f'\tvar {param.name} {go_type if go_type else param.type}')
                    lines.append(f'\tif err := c.Bind(&{param.name}); err != nil {{')
                    lines.append(f'\t\treturn c.JSON(http.StatusBadRequest, map[string]string{{"error": err.Error()}})')
                    lines.append('\t}')
                elif param.location == ParameterLocation.HEADER:
                    lines.append(f'\t{param.name} := c.Request().Header.Get("{param.name}")')

            # Suppress unused variable warnings
            for param in method.parameters:
                if param.location != ParameterLocation.BODY:
                    lines.append(f'\t_ = {param.name}')

            # Build response
            if method.return_type.lower() == 'void':
                lines.append(
                    f'\treturn c.JSON(http.StatusOK, map[string]string{{"message": "success", "method": "{method.name}"}})'
                )
            else:
                default_val = _go_default_value(method.return_type)
                lines.append(f'\tresult := {default_val}')
                lines.append(f'\treturn c.JSON(http.StatusOK, map[string]interface{{}}{{"result": result}})')

            lines += ['}', '']

        return '\n'.join(lines) + '\n'

    def _models_go(self) -> str:
        needs_time = any(
            field.type.lower() in ('date', 'datetime')
            for model in self.service.models
            for field in model.fields
        )

        lines = [
            'package models',
            '',
        ]
        if needs_time:
            lines += ['import "time"', '']

        if not self.service.models:
            lines.append('// No models defined for this service.')

        for model in self.service.models:
            lines.append(f'// {model.name} represents the {model.name} data model.')
            lines.append(f'type {model.name} struct {{')
            for field in model.fields:
                go_type = _go_type(field.type)
                omitempty = ',omitempty' if not field.required else ''
                lines.append(
                    f'\t{field.name[0].upper() + field.name[1:]} {go_type} `json:"{field.name}{omitempty}" form:"{field.name}"`'
                )
            lines += ['}', '']

        return '\n'.join(lines) + '\n'

    def _readme(self) -> str:
        method_docs = []
        for m in self.service.methods:
            method_docs.append(
                f'- `{m.http_method} {m.path}` — {m.name}' + (f': {m.description}' if m.description else '')
            )

        routes_section = '\n'.join(method_docs) if method_docs else '- No routes defined.'

        return f"""# {self.service.service_name}

{self.service.description or 'A REST API built with Go and Echo.'}

**Version:** {self.service.version}

## Requirements

- Go 1.21+

## Getting Started

```bash
go mod tidy
go run main.go
```

The server will start on port **8080**.

## Routes

{routes_section}

## Project Structure

```
.
├── go.mod
├── main.go
├── handlers/
│   └── {self.pkg}_handler.go
└── models/
    └── {self.pkg}_models.go
```
"""
