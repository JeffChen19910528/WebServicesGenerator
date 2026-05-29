import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from models import ServiceDefinition, ParameterLocation
from generators.base import BaseGenerator
from typing import Dict


class PythonFlaskGenerator(BaseGenerator):
    """Generates a Flask REST project."""

    # ------------------------------------------------------------------ #
    #  Python type mapping
    # ------------------------------------------------------------------ #
    PY_TYPES: Dict[str, str] = {
        "string":   "str",
        "int":      "int",
        "float":    "float",
        "boolean":  "bool",
        "date":     "date",
        "datetime": "datetime",
        "void":     "None",
    }

    DATE_TYPES = {"date", "datetime"}

    def _py_type(self, t: str) -> str:
        return self.PY_TYPES.get(t.lower(), t)

    def _collect_datetime_imports(self, types) -> str:
        needed = {t.lower() for t in types if t.lower() in self.DATE_TYPES}
        if not needed:
            return ""
        return "from datetime import " + ", ".join(sorted(needed))

    # ------------------------------------------------------------------ #
    #  generate()
    # ------------------------------------------------------------------ #
    def generate(self) -> Dict[str, str]:
        files: Dict[str, str] = {}

        files["requirements.txt"] = self._requirements()
        files["models.py"] = self._models_py()
        files["app.py"] = self._app_py()
        files["README.md"] = self._readme()

        return files

    # ------------------------------------------------------------------ #
    #  requirements.txt
    # ------------------------------------------------------------------ #
    def _requirements(self) -> str:
        return """flask>=3.0.0
flask-restful>=0.3.10
"""

    # ------------------------------------------------------------------ #
    #  models.py — dataclasses
    # ------------------------------------------------------------------ #
    def _models_py(self) -> str:
        if not self.service.models:
            return "# No models defined\n"

        all_types = [f.type for m in self.service.models for f in m.fields]
        dt_import = self._collect_datetime_imports(all_types)

        lines = ["from dataclasses import dataclass, field", "from typing import Optional"]
        if dt_import:
            lines.append(dt_import)
        lines.append("")

        for model in self.service.models:
            lines.append(f"\n@dataclass")
            lines.append(f"class {model.name}:")
            if not model.fields:
                lines.append("    pass")
            else:
                for f in model.fields:
                    py_type = self._py_type(f.type)
                    if f.required:
                        lines.append(f"    {f.name}: {py_type} = field(default=None)")
                    else:
                        lines.append(f"    {f.name}: Optional[{py_type}] = field(default=None)")
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    #  app.py
    # ------------------------------------------------------------------ #
    def _app_py(self) -> str:
        pkg = self.pkg
        cls = self.class_name

        # Determine model imports
        model_names = {m.name for m in self.service.models}
        used_models = set()
        for method in self.service.methods:
            for p in method.parameters:
                if not self._is_primitive(p.type) and p.type in model_names:
                    used_models.add(p.type)
            if not self._is_primitive(method.return_type) and method.return_type in model_names:
                used_models.add(method.return_type)

        model_import_line = ""
        if used_models:
            model_import_line = f"from models import {', '.join(sorted(used_models))}\n"

        # Build routes
        route_lines = []
        for method in self.service.methods:
            http = method.http_method.upper()
            path = method.path if method.path else "/"
            func_name = method.name
            ret_type = self._py_type(method.return_type)

            # Build param extraction comment and default response
            if ret_type == "None":
                default_data = "{}"
                status = 204
            elif ret_type == "str":
                default_data = '{"result": ""}'
                status = 200
            elif ret_type == "int":
                default_data = '{"result": 0}'
                status = 200
            elif ret_type == "float":
                default_data = '{"result": 0.0}'
                status = 200
            elif ret_type == "bool":
                default_data = '{"result": False}'
                status = 200
            else:
                default_data = '{"result": None}'
                status = 200

            # Collect parameter extraction lines
            param_lines = []
            for p in method.parameters:
                if p.location == ParameterLocation.QUERY:
                    param_lines.append(
                        f'    {p.name} = request.args.get("{p.name}")'
                    )
                elif p.location == ParameterLocation.BODY:
                    param_lines.append(
                        f'    {p.name} = request.get_json()'
                    )
                elif p.location == ParameterLocation.HEADER:
                    param_lines.append(
                        f'    {p.name} = request.headers.get("{p.name}")'
                    )
                # PATH params come from the route URL binding automatically

            desc = method.description or f"{method.name} endpoint"

            route_lines.append(f'@bp.route("{path}", methods=["{http}"])')
            route_lines.append(f"def {func_name}(**kwargs):")
            route_lines.append(f'    """{desc}"""')
            if param_lines:
                route_lines.extend(param_lines)
            if ret_type == "None":
                route_lines.append(f"    return jsonify({{}}), {status}")
            else:
                route_lines.append(f"    return jsonify({default_data}), {status}")
            route_lines.append("")

        routes_block = "\n".join(route_lines)

        return f"""from flask import Flask, Blueprint, jsonify, request
{model_import_line}
bp = Blueprint("{pkg}", __name__, url_prefix="/api/v{self.service.version}")

{routes_block}

def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(bp)

    @app.route("/health")
    def health():
        return jsonify({{"status": "ok"}})

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
"""

    # ------------------------------------------------------------------ #
    #  README.md
    # ------------------------------------------------------------------ #
    def _readme(self) -> str:
        cls = self.class_name
        pkg = self.pkg
        return f"""# {cls} — Flask REST API

## Requirements

- Python 3.10+

## Installation

```bash
pip install -r requirements.txt
```

## Running the server

```bash
python app.py
```

The API will be available at `http://localhost:5000`.

## Endpoints

All routes are prefixed with `/api/v{self.service.version}/{pkg}`.

| Method | Path | Description |
|--------|------|-------------|
{''.join(f"| {m.http_method.upper()} | {m.path} | {m.description or m.name} |" + chr(10) for m in self.service.methods)}
## Project structure

```
.
├── app.py
├── models.py
└── requirements.txt
```
"""
