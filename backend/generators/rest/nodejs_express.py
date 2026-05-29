import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from models import ServiceDefinition
from generators.base import BaseGenerator
from typing import Dict


JS_TYPE_DEFAULTS = {
    "string": "''",
    "int": "0",
    "float": "0.0",
    "boolean": "false",
    "date": "new Date().toISOString().split('T')[0]",
    "datetime": "new Date().toISOString()",
}

HTTP_TO_EXPRESS = {
    "GET": "get",
    "POST": "post",
    "PUT": "put",
    "DELETE": "delete",
    "PATCH": "patch",
}


def _js_default(t: str) -> str:
    return JS_TYPE_DEFAULTS.get(t.lower(), "null")


def _express_path(path: str, method) -> str:
    """Convert path with {param} style to :param style for Express."""
    result = path
    for p in method.parameters:
        if p.location.value == "path":
            result = result.replace("{" + p.name + "}", f":{p.name}")
    return result


class NodeJSExpressGenerator(BaseGenerator):
    def __init__(self, service: ServiceDefinition):
        super().__init__(service)

    def generate(self) -> Dict[str, str]:
        files = {}
        files["package.json"] = self._gen_package_json()
        files["src/app.js"] = self._gen_app_js()
        files[f"src/routes/{self.pkg}Routes.js"] = self._gen_routes()
        files[f"src/controllers/{self.pkg}Controller.js"] = self._gen_controller()
        for model in self.service.models:
            files[f"src/models/{model.name}.js"] = self._gen_model(model)
        files["README.md"] = self._gen_readme()
        return files

    def _gen_package_json(self) -> str:
        return f"""\
{{
  "name": "{self.pkg}",
  "version": "{self.service.version}",
  "description": "{self.service.description or self.service.service_name + ' REST API'}",
  "main": "src/app.js",
  "scripts": {{
    "start": "node src/app.js",
    "dev": "nodemon src/app.js"
  }},
  "dependencies": {{
    "body-parser": "^1.20.2",
    "cors": "^2.8.5",
    "express": "^4.18.2"
  }},
  "devDependencies": {{
    "nodemon": "^3.0.1"
  }}
}}
"""

    def _gen_app_js(self) -> str:
        return f"""\
const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const {self.pkg}Routes = require('./routes/{self.pkg}Routes');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({{ extended: true }}));

app.use('/api/{self.pkg.replace('_', '-')}', {self.pkg}Routes);

// Health check
app.get('/health', (req, res) => {{
  res.json({{ status: 'ok', service: '{self.service.service_name}', version: '{self.service.version}' }});
}});

// 404 handler
app.use((req, res, next) => {{
  res.status(404).json({{ error: 'Not Found', path: req.path }});
}});

// Error handler
app.use((err, req, res, next) => {{
  console.error(err.stack);
  res.status(err.status || 500).json({{
    error: err.message || 'Internal Server Error'
  }});
}});

app.listen(PORT, () => {{
  console.log(`{self.service.service_name} API server running on http://localhost:${{PORT}}`);
}});

module.exports = app;
"""

    def _gen_routes(self) -> str:
        lines = [
            "const express = require('express');",
            "const router = express.Router();",
            f"const controller = require('../controllers/{self.pkg}Controller');",
            "",
        ]
        for method in self.service.methods:
            verb = HTTP_TO_EXPRESS.get(method.http_method.upper(), "get")
            route_path = _express_path(method.path, method)
            # Normalize to ensure it starts with /
            if not route_path.startswith("/"):
                route_path = "/" + route_path
            camel = method.name[0].lower() + method.name[1:]
            if method.description:
                lines.append(f"// {method.description}")
            lines.append(f"router.{verb}('{route_path}', controller.{camel});")
            lines.append("")
        lines.append("module.exports = router;")
        return "\n".join(lines) + "\n"

    def _gen_controller(self) -> str:
        lines = []
        # Import models if any
        for model in self.service.models:
            lines.append(f"const {model.name} = require('../models/{model.name}');")
        if self.service.models:
            lines.append("")

        for method in self.service.methods:
            camel = method.name[0].lower() + method.name[1:]
            if method.description:
                lines.append(f"// {method.description}")
            lines.append(f"const {camel} = async (req, res) => {{")
            lines.append("  try {")

            # Extract parameters
            for p in method.parameters:
                if p.location.value == "path":
                    lines.append(f"    const {p.name} = req.params.{p.name};")
                elif p.location.value == "query":
                    lines.append(f"    const {p.name} = req.query.{p.name};")
                elif p.location.value == "body":
                    lines.append(f"    const {p.name} = req.body.{p.name};")
                elif p.location.value == "header":
                    lines.append(f"    const {p.name} = req.headers['{p.name.lower()}'];")

            # Build default response data
            rt = method.return_type
            if rt == "void":
                lines.append("    res.json({ success: true });")
            elif not self._is_primitive(rt):
                # Return a stub object for the model
                model_match = next((m for m in self.service.models if m.name == rt), None)
                if model_match:
                    fields_str = ", ".join(
                        f"{f.name}: {_js_default(f.type)}" for f in model_match.fields
                    )
                    lines.append(f"    const result = {{ {fields_str} }};")
                else:
                    lines.append(f"    const result = {{}};")
                lines.append("    res.json(result);")
            else:
                default_val = _js_default(rt)
                lines.append(f"    const result = {default_val};")
                lines.append("    res.json({ result });")

            lines.append("  } catch (err) {")
            lines.append("    next(err);")
            lines.append("  }")
            lines.append("};")
            lines.append("")

        # Export all
        exports = [method.name[0].lower() + method.name[1:] for method in self.service.methods]
        lines.append("module.exports = {")
        for exp in exports:
            lines.append(f"  {exp},")
        lines.append("};")
        return "\n".join(lines) + "\n"

    def _gen_model(self, model) -> str:
        lines = [f"class {model.name} {{"]
        if model.fields:
            constructor_params = ", ".join(
                f"{f.name} = {_js_default(f.type)}" for f in model.fields
            )
            lines.append(f"  constructor({constructor_params}) {{")
            for f in model.fields:
                lines.append(f"    this.{f.name} = {f.name};")
            lines.append("  }")
        else:
            lines.append("  constructor() {}")
        lines.append("")
        lines.append("  toJSON() {")
        lines.append("    return {")
        for f in model.fields:
            lines.append(f"      {f.name}: this.{f.name},")
        lines.append("    };")
        lines.append("  }")
        lines.append("}")
        lines.append("")
        lines.append(f"module.exports = {model.name};")
        return "\n".join(lines) + "\n"

    def _gen_readme(self) -> str:
        return f"""\
# {self.service.service_name} — Node.js Express REST API

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
# Development (with auto-reload)
npm run dev

# Production
npm start
```

The server starts on **http://localhost:3000**

## Endpoints

Base path: `/api/{self.pkg.replace('_', '-')}`

| Method | Path | Description |
|--------|------|-------------|
{"".join(f"| {m.http_method} | {m.path} | {m.description or m.name} |" + chr(10) for m in self.service.methods)}\

## Health Check

```
GET /health
```

## Models

{"".join(f"- `{model.name}`: " + ", ".join(f.name for f in model.fields) + chr(10) for model in self.service.models)}\
"""
