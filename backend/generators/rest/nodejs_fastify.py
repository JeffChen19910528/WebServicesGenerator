import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from models import ServiceDefinition
from generators.base import BaseGenerator
from typing import Dict


JS_SCHEMA_TYPE = {
    "string": "string",
    "int": "integer",
    "float": "number",
    "boolean": "boolean",
    "date": "string",
    "datetime": "string",
}

JS_DEFAULT_MAP = {
    "string": "''",
    "int": "0",
    "float": "0.0",
    "boolean": "false",
    "date": "new Date().toISOString().split('T')[0]",
    "datetime": "new Date().toISOString()",
}

HTTP_TO_FASTIFY = {
    "GET": "get",
    "POST": "post",
    "PUT": "put",
    "DELETE": "delete",
    "PATCH": "patch",
}


def _json_schema_type(t: str) -> str:
    return JS_SCHEMA_TYPE.get(t.lower(), "object")


def _js_default(t: str) -> str:
    return JS_DEFAULT_MAP.get(t.lower(), "null")


def _fastify_path(path: str, method) -> str:
    """Convert {param} style to :param style for Fastify."""
    result = path
    for p in method.parameters:
        if p.location.value == "path":
            result = result.replace("{" + p.name + "}", f":{p.name}")
    return result


def _indent(text: str, spaces: int = 2) -> str:
    pad = " " * spaces
    return "\n".join(pad + line if line.strip() else line for line in text.splitlines())


class NodeJSFastifyGenerator(BaseGenerator):
    def __init__(self, service: ServiceDefinition):
        super().__init__(service)

    def generate(self) -> Dict[str, str]:
        files = {}
        files["package.json"] = self._gen_package_json()
        files["src/app.js"] = self._gen_app_js()
        files[f"src/routes/{self.pkg}.js"] = self._gen_routes()
        files[f"src/services/{self.pkg}Service.js"] = self._gen_service()
        files["README.md"] = self._gen_readme()
        return files

    def _gen_package_json(self) -> str:
        return f"""\
{{
  "name": "{self.pkg}",
  "version": "{self.service.version}",
  "description": "{self.service.description or self.service.service_name + ' Fastify REST API'}",
  "main": "src/app.js",
  "scripts": {{
    "start": "node src/app.js",
    "dev": "node --watch src/app.js"
  }},
  "dependencies": {{
    "@fastify/cors": "^9.0.1",
    "fastify": "^4.26.2"
  }}
}}
"""

    def _gen_app_js(self) -> str:
        return f"""\
'use strict';

const fastify = require('fastify')({{ logger: true }});
const cors = require('@fastify/cors');
const {self.pkg}Routes = require('./routes/{self.pkg}');

const PORT = process.env.PORT || 3000;
const HOST = process.env.HOST || '0.0.0.0';

async function start() {{
  await fastify.register(cors, {{
    origin: true,
  }});

  fastify.register({self.pkg}Routes, {{ prefix: '/api/{self.pkg.replace('_', '-')}' }});

  // Health check
  fastify.get('/health', async () => {{
    return {{ status: 'ok', service: '{self.service.service_name}', version: '{self.service.version}' }};
  }});

  try {{
    await fastify.listen({{ port: PORT, host: HOST }});
    console.log(`{self.service.service_name} API running on http://localhost:${{PORT}}`);
  }} catch (err) {{
    fastify.log.error(err);
    process.exit(1);
  }}
}}

start();
"""

    def _gen_routes(self) -> str:
        lines = [
            "'use strict';",
            "",
            f"const {self.pkg}Service = require('../services/{self.pkg}Service');",
            "",
            f"async function {self.pkg}Routes(fastify, options) {{",
        ]

        for method in self.service.methods:
            verb = HTTP_TO_FASTIFY.get(method.http_method.upper(), "get")
            route_path = _fastify_path(method.path, method)
            if not route_path.startswith("/"):
                route_path = "/" + route_path

            camel = method.name[0].lower() + method.name[1:]

            # Build JSON schema for the route
            schema_parts = []

            # Params schema
            path_params = [p for p in method.parameters if p.location.value == "path"]
            if path_params:
                props = ", ".join(
                    f"'{p.name}': {{ type: '{_json_schema_type(p.type)}' }}"
                    for p in path_params
                )
                required = [p.name for p in path_params if p.required]
                req_str = f", required: {str(required).replace(chr(39), chr(34))}" if required else ""
                schema_parts.append(f"params: {{ type: 'object', properties: {{ {props} }}{req_str} }}")

            # Querystring schema
            query_params = [p for p in method.parameters if p.location.value == "query"]
            if query_params:
                props = ", ".join(
                    f"'{p.name}': {{ type: '{_json_schema_type(p.type)}' }}"
                    for p in query_params
                )
                required = [p.name for p in query_params if p.required]
                req_str = f", required: {str(required).replace(chr(39), chr(34))}" if required else ""
                schema_parts.append(f"querystring: {{ type: 'object', properties: {{ {props} }}{req_str} }}")

            # Body schema
            body_params = [p for p in method.parameters if p.location.value == "body"]
            if body_params:
                if len(body_params) == 1 and not self._is_primitive(body_params[0].type):
                    schema_parts.append(f"body: {{ type: 'object', additionalProperties: true }}")
                else:
                    props = ", ".join(
                        f"'{p.name}': {{ type: '{_json_schema_type(p.type)}' }}"
                        for p in body_params
                    )
                    required = [p.name for p in body_params if p.required]
                    req_str = f", required: {str(required).replace(chr(39), chr(34))}" if required else ""
                    schema_parts.append(f"body: {{ type: 'object', properties: {{ {props} }}{req_str} }}")

            # Response schema
            rt = method.return_type
            if rt == "void":
                schema_parts.append("response: { 200: { type: 'object', properties: { success: { type: 'boolean' } } } }")
            elif self._is_primitive(rt):
                schema_parts.append(f"response: {{ 200: {{ type: 'object', properties: {{ result: {{ type: '{_json_schema_type(rt)}' }} }} }} }}")
            else:
                model_match = next((m for m in self.service.models if m.name == rt), None)
                if model_match:
                    props = ", ".join(
                        f"'{f.name}': {{ type: '{_json_schema_type(f.type)}' }}"
                        for f in model_match.fields
                    )
                    schema_parts.append(f"response: {{ 200: {{ type: 'object', properties: {{ {props} }} }} }}")
                else:
                    schema_parts.append("response: { 200: { type: 'object', additionalProperties: true } }")

            schema_str = ",\n        ".join(schema_parts)

            if method.description:
                lines.append(f"  // {method.description}")
            lines.append(f"  fastify.{verb}('{route_path}', {{")
            lines.append("    schema: {")
            if schema_str:
                lines.append(f"      {schema_str}")
            lines.append("    },")
            lines.append(f"    handler: async (request, reply) => {{")

            # Extract parameters
            for p in method.parameters:
                if p.location.value == "path":
                    lines.append(f"      const {p.name} = request.params.{p.name};")
                elif p.location.value == "query":
                    lines.append(f"      const {p.name} = request.query.{p.name};")
                elif p.location.value == "body":
                    lines.append(f"      const {p.name} = request.body?.{p.name} ?? request.body;")
                elif p.location.value == "header":
                    lines.append(f"      const {p.name} = request.headers['{p.name.lower()}'];")

            svc_args = ", ".join(p.name for p in method.parameters)
            lines.append(f"      return await {self.pkg}Service.{camel}({svc_args});")
            lines.append("    },")
            lines.append("  });")
            lines.append("")

        lines.append("}")
        lines.append("")
        lines.append(f"module.exports = {self.pkg}Routes;")
        return "\n".join(lines) + "\n"

    def _gen_service(self) -> str:
        lines = ["'use strict';", ""]

        for method in self.service.methods:
            camel = method.name[0].lower() + method.name[1:]
            param_names = [p.name for p in method.parameters]
            params_str = ", ".join(param_names)

            rt = method.return_type
            if rt == "void":
                return_val = "{ success: true }"
            elif self._is_primitive(rt):
                return_val = f"{{ result: {_js_default(rt)} }}"
            else:
                model_match = next((m for m in self.service.models if m.name == rt), None)
                if model_match:
                    fields = ", ".join(
                        f"{f.name}: {_js_default(f.type)}" for f in model_match.fields
                    )
                    return_val = f"{{ {fields} }}"
                else:
                    return_val = "{}"

            if method.description:
                lines.append(f"// {method.description}")
            lines.append(f"async function {camel}({params_str}) {{")
            lines.append(f"  return {return_val};")
            lines.append("}")
            lines.append("")

        # Exports
        lines.append("module.exports = {")
        for method in self.service.methods:
            camel = method.name[0].lower() + method.name[1:]
            lines.append(f"  {camel},")
        lines.append("};")
        return "\n".join(lines) + "\n"

    def _gen_readme(self) -> str:
        return f"""\
# {self.service.service_name} — Node.js Fastify REST API

{self.service.description or ''}

## Requirements

- Node.js >= 18
- npm

## Setup

```bash
npm install
```

## Running

```bash
# Development
npm run dev

# Production
npm start
```

The server starts on **http://localhost:3000**

## API Base URL

`http://localhost:3000/api/{self.pkg.replace('_', '-')}`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
{"".join(f"| {m.http_method} | {m.path} | {m.description or m.name} |" + chr(10) for m in self.service.methods)}\

## Health Check

```
GET /health
```
"""
