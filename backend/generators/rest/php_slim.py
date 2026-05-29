import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from models import ServiceDefinition, ParameterLocation
from generators.base import BaseGenerator
from typing import Dict


PHP_TYPE_MAP = {
    "string": "string",
    "int": "int",
    "float": "float",
    "boolean": "bool",
    "date": "string",       # ISO date string
    "datetime": "string",   # ISO datetime string
    "void": "void",
}


def _php_type(t: str) -> str:
    return PHP_TYPE_MAP.get(t.lower(), t)


def _php_default_value(t: str) -> str:
    lower = t.lower()
    if lower == "string":
        return '"ok"'
    elif lower == "int":
        return "0"
    elif lower == "float":
        return "0.0"
    elif lower == "boolean":
        return "true"
    elif lower == "date":
        return "(new \\DateTime())->format('Y-m-d')"
    elif lower == "datetime":
        return "(new \\DateTime())->format('Y-m-d\\\\TH:i:sP')"
    else:
        return "null"


def _pascal(name: str) -> str:
    import re
    parts = re.split(r'[_\-\s]+', name)
    return ''.join(p[0].upper() + p[1:] for p in parts if p)


def _camel(name: str) -> str:
    p = _pascal(name)
    return p[0].lower() + p[1:] if p else name


def _slim_http_method(http_method: str) -> str:
    return http_method.lower()


def _slim_route_path(path: str) -> str:
    # Slim uses {param} natively, same as the input format
    return path


def _action_class_name(method_name: str) -> str:
    return _pascal(method_name) + 'Action'


def _model_filename(model_name: str) -> str:
    import re
    s = re.sub(r'(?<!^)(?=[A-Z])', '_', model_name)
    return s


class PHPSlimGenerator(BaseGenerator):
    def __init__(self, service: ServiceDefinition):
        super().__init__(service)

    def generate(self) -> Dict[str, str]:
        files: Dict[str, str] = {}
        files["composer.json"] = self._composer_json()
        files["public/index.php"] = self._public_index_php()
        for method in self.service.methods:
            action_class = _action_class_name(method.name)
            files[f"src/Application/Actions/{self.class_name}/{action_class}.php"] = self._action_php(method, action_class)
        for model in self.service.models:
            files[f"src/Domain/Models/{model.name}.php"] = self._model_php(model)
        files["README.md"] = self._readme()
        return files

    def _composer_json(self) -> str:
        pkg_slug = self.pkg.replace('_', '-')
        description = self.service.description or f"{self.service.service_name} REST API"
        return (
            '{\n'
            f'    "name": "{pkg_slug}/{pkg_slug}",\n'
            f'    "description": "{description}",\n'
            '    "type": "project",\n'
            '    "require": {\n'
            '        "php": "^8.1",\n'
            '        "slim/slim": "^4.12",\n'
            '        "slim/psr7": "^1.6",\n'
            '        "php-di/php-di": "^7.0"\n'
            '    },\n'
            '    "require-dev": {\n'
            '        "phpunit/phpunit": "^10.0"\n'
            '    },\n'
            '    "autoload": {\n'
            '        "psr-4": {\n'
            '            "App\\\\": "src/"\n'
            '        }\n'
            '    },\n'
            '    "autoload-dev": {\n'
            '        "psr-4": {\n'
            '            "Tests\\\\": "tests/"\n'
            '        }\n'
            '    },\n'
            '    "scripts": {\n'
            '        "start": "php -S 0.0.0.0:8080 -t public"\n'
            '    }\n'
            '}\n'
        )

    def _public_index_php(self) -> str:
        action_uses = []
        route_registrations = []

        for method in self.service.methods:
            action_class = _action_class_name(method.name)
            action_uses.append(
                f'use App\\Application\\Actions\\{self.class_name}\\{action_class};'
            )
            slim_method = _slim_http_method(method.http_method)
            route_path = _slim_route_path(method.path)
            route_registrations.append(
                f"$app->{slim_method}('{route_path}', {action_class}::class);"
            )

        uses_block = '\n'.join(action_uses)
        routes_block = '\n'.join(f'    {r}' for r in route_registrations)

        return f"""<?php

declare(strict_types=1);

use DI\\ContainerBuilder;
use Slim\\Factory\\AppFactory;
use Slim\\Middleware\\ErrorMiddleware;
{uses_block}

require __DIR__ . '/../vendor/autoload.php';

// Build DI container
$containerBuilder = new ContainerBuilder();
$container = $containerBuilder->build();

// Create app
AppFactory::setContainer($container);
$app = AppFactory::create();

// Add middleware
$app->addRoutingMiddleware();
$app->addBodyParsingMiddleware();

$errorMiddleware = $app->addErrorMiddleware(true, true, true);

// Register routes
{routes_block}

$app->run();
"""

    def _action_php(self, method, action_class: str) -> str:
        namespace = f'App\\Application\\Actions\\{self.class_name}'

        # Build parameter reading logic
        param_lines = []
        for param in method.parameters:
            if param.location == ParameterLocation.PATH:
                param_lines.append(
                    f"        ${param.name} = $args['{param.name}'] ?? null;"
                )
            elif param.location == ParameterLocation.QUERY:
                param_lines.append(
                    f"        $queryParams = $request->getQueryParams();"
                )
                param_lines.append(
                    f"        ${param.name} = $queryParams['{param.name}'] ?? null;"
                )
            elif param.location == ParameterLocation.BODY:
                param_lines.append(
                    f"        $body = $request->getParsedBody();"
                )
                param_lines.append(
                    f"        ${param.name} = $body['{param.name}'] ?? null;"
                )
            elif param.location == ParameterLocation.HEADER:
                param_lines.append(
                    f"        ${param.name} = $request->getHeaderLine('{param.name}');"
                )

        # Suppress unused variable warnings via assignment to _
        suppress_lines = []
        for param in method.parameters:
            suppress_lines.append(f"        $_ = ${param.name};")

        params_block = '\n'.join(param_lines)
        suppress_block = '\n'.join(suppress_lines)

        if method.return_type.lower() == 'void':
            response_block = f"""        $data = [
            'message' => 'success',
            'method'  => '{method.name}',
        ];"""
        else:
            default_val = _php_default_value(method.return_type)
            response_block = f"""        $result = {default_val};
        $data = ['result' => $result];"""

        description = method.description or method.name

        return f"""<?php

declare(strict_types=1);

namespace {namespace};

use Psr\\Http\\Message\\ResponseInterface as Response;
use Psr\\Http\\Message\\ServerRequestInterface as Request;

/**
 * {description}
 *
 * Handles {method.http_method} {method.path}
 */
class {action_class}
{{
    public function __invoke(Request $request, Response $response, array $args): Response
    {{
{params_block}
{suppress_block}

{response_block}

        $response->getBody()->write(json_encode($data, JSON_PRETTY_PRINT));

        return $response
            ->withHeader('Content-Type', 'application/json')
            ->withStatus(200);
    }}
}}
"""

    def _model_php(self, model) -> str:
        namespace = 'App\\Domain\\Models'

        property_lines = []
        constructor_params = []
        constructor_assigns = []
        getter_lines = []
        to_array_lines = []

        for field in model.fields:
            php_type = _php_type(field.type)
            nullable = '' if field.required else '?'
            default = '' if field.required else ' = null'
            prop_name = _camel(field.name)

            property_lines.append(
                f'    private {nullable}{php_type} ${prop_name};'
            )
            constructor_params.append(
                f'{nullable}{php_type} ${prop_name}{default}'
            )
            constructor_assigns.append(
                f'        $this->{prop_name} = ${prop_name};'
            )

            getter_name = 'get' + _pascal(field.name)
            getter_lines += [
                f'    public function {getter_name}(): {nullable}{php_type}',
                '    {',
                f'        return $this->{prop_name};',
                '    }',
                '',
            ]
            to_array_lines.append(
                f"            '{field.name}' => $this->{prop_name},"
            )

        props_block = '\n'.join(property_lines)
        ctor_params_str = ', '.join(constructor_params)
        ctor_assigns_block = '\n'.join(constructor_assigns)
        getters_block = '\n'.join(getter_lines)
        to_array_block = '\n'.join(to_array_lines)

        return f"""<?php

declare(strict_types=1);

namespace {namespace};

class {model.name}
{{
{props_block}

    public function __construct({ctor_params_str})
    {{
{ctor_assigns_block}
    }}

{getters_block}
    public function toArray(): array
    {{
        return [
{to_array_block}
        ];
    }}

    public function jsonSerialize(): mixed
    {{
        return $this->toArray();
    }}
}}
"""

    def _readme(self) -> str:
        method_docs = []
        for m in self.service.methods:
            method_docs.append(
                f'- `{m.http_method} {m.path}` — {_action_class_name(m.name)}' +
                (f': {m.description}' if m.description else '')
            )
        routes_section = '\n'.join(method_docs) if method_docs else '- No routes defined.'

        action_tree_lines = []
        for m in self.service.methods:
            action_tree_lines.append(f'│       └── {_action_class_name(m.name)}.php')
        action_tree = '\n'.join(action_tree_lines) if action_tree_lines else '│       └── (none)'

        model_tree_lines = []
        for model in self.service.models:
            model_tree_lines.append(f'│   └── {model.name}.php')
        model_tree = '\n'.join(model_tree_lines) if model_tree_lines else '│   └── (none)'

        return f"""# {self.service.service_name}

{self.service.description or 'A REST API built with PHP and Slim 4.'}

**Version:** {self.service.version}

## Requirements

- PHP 8.1+
- Composer

## Getting Started

```bash
composer install
composer start
```

The server will start on port **8080**.

## Routes

{routes_section}

## Project Structure

```
.
├── composer.json
├── public/
│   └── index.php
└── src/
    ├── Application/
    │   └── Actions/
    │       └── {self.class_name}/
{action_tree}
    └── Domain/
        └── Models/
{model_tree}
```
"""
