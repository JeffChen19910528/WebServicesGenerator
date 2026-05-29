import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from models import ServiceDefinition, ParameterLocation
from generators.base import BaseGenerator
from typing import Dict


class PythonFastAPIGenerator(BaseGenerator):
    """Generates a FastAPI REST project."""

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

    def _needs_date_import(self, types) -> bool:
        return any(t.lower() in self.DATE_TYPES for t in types)

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
        pkg = self.pkg

        files["requirements.txt"] = self._requirements()
        files["models.py"] = self._models_py()
        files[f"routers/{pkg}_router.py"] = self._router_py()
        files["main.py"] = self._main_py()
        files["README.md"] = self._readme()

        return files

    # ------------------------------------------------------------------ #
    #  requirements.txt
    # ------------------------------------------------------------------ #
    def _requirements(self) -> str:
        return """fastapi>=0.110.0
uvicorn[standard]>=0.29.0
pydantic>=2.0.0
"""

    # ------------------------------------------------------------------ #
    #  models.py
    # ------------------------------------------------------------------ #
    def _models_py(self) -> str:
        if not self.service.models:
            return "from pydantic import BaseModel\n"

        all_types = [f.type for m in self.service.models for f in m.fields]
        dt_import = self._collect_datetime_imports(all_types)

        lines = ["from pydantic import BaseModel"]
        if dt_import:
            lines.append(dt_import)
        lines.append("from typing import Optional")
        lines.append("")

        for model in self.service.models:
            lines.append(f"\nclass {model.name}(BaseModel):")
            if not model.fields:
                lines.append("    pass")
            else:
                for field in model.fields:
                    py_type = self._py_type(field.type)
                    if field.required:
                        lines.append(f"    {field.name}: {py_type}")
                    else:
                        lines.append(f"    {field.name}: Optional[{py_type}] = None")
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    #  router
    # ------------------------------------------------------------------ #
    def _router_py(self) -> str:
        pkg = self.pkg
        cls = self.class_name

        # Collect all types used in parameters and return types
        all_types = []
        for method in self.service.methods:
            all_types += [p.type for p in method.parameters]
            all_types.append(method.return_type)

        dt_import = self._collect_datetime_imports(all_types)

        # Determine which models are needed
        model_names = {m.name for m in self.service.models}
        used_models = set()
        for method in self.service.methods:
            for p in method.parameters:
                if not self._is_primitive(p.type) and p.type in model_names:
                    used_models.add(p.type)
            if not self._is_primitive(method.return_type) and method.return_type in model_names:
                used_models.add(method.return_type)

        needs_query = any(
            p.location == ParameterLocation.QUERY
            for method in self.service.methods
            for p in method.parameters
        )
        needs_header = any(
            p.location == ParameterLocation.HEADER
            for method in self.service.methods
            for p in method.parameters
        )

        lines = ["from fastapi import APIRouter"]
        if needs_query:
            lines[0] += ", Query"
        if needs_header:
            lines[0] += ", Header"
        if needs_query or needs_header:
            pass  # already added
        lines.append("from typing import Optional")
        if dt_import:
            lines.append(dt_import)
        if used_models:
            model_imports = ", ".join(sorted(used_models))
            lines.append(f"from models import {model_imports}")
        lines.append("")
        lines.append(f'router = APIRouter(prefix="/{pkg}", tags=["{cls}"])')
        lines.append("")

        for method in self.service.methods:
            http = method.http_method.lower()
            path = method.path if method.path else "/"
            ret_type = self._py_type(method.return_type)

            # Build function signature params
            sig_parts = []
            # Path params first
            for p in method.parameters:
                if p.location == ParameterLocation.PATH:
                    py_type = self._py_type(p.type)
                    sig_parts.append(f"{p.name}: {py_type}")

            # Query params
            for p in method.parameters:
                if p.location == ParameterLocation.QUERY:
                    py_type = self._py_type(p.type)
                    if p.required:
                        sig_parts.append(f"{p.name}: {py_type} = Query(...)")
                    else:
                        sig_parts.append(f"{p.name}: Optional[{py_type}] = Query(None)")

            # Body params
            for p in method.parameters:
                if p.location == ParameterLocation.BODY:
                    py_type = self._py_type(p.type)
                    sig_parts.append(f"{p.name}: {py_type}")

            # Header params
            for p in method.parameters:
                if p.location == ParameterLocation.HEADER:
                    py_type = self._py_type(p.type)
                    if p.required:
                        sig_parts.append(f"{p.name}: {py_type} = Header(...)")
                    else:
                        sig_parts.append(f"{p.name}: Optional[{py_type}] = Header(None)")

            sig = ", ".join(sig_parts)

            # Default return value
            if ret_type == "None":
                return_val = "return"
            elif ret_type == "str":
                return_val = 'return ""'
            elif ret_type == "int":
                return_val = "return 0"
            elif ret_type == "float":
                return_val = "return 0.0"
            elif ret_type == "bool":
                return_val = "return False"
            elif ret_type == "date":
                return_val = "from datetime import date; return date.today()"
            elif ret_type == "datetime":
                return_val = "from datetime import datetime; return datetime.now()"
            else:
                return_val = "return None"

            desc = method.description or f"{method.name} endpoint"
            lines.append(f'@router.{http}("{path}", summary="{desc}")')
            if ret_type == "None":
                lines.append(f"def {method.name}({sig}):")
            else:
                lines.append(f"def {method.name}({sig}) -> Optional[{ret_type}]:")
            lines.append(f"    {return_val}")
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    #  main.py
    # ------------------------------------------------------------------ #
    def _main_py(self) -> str:
        pkg = self.pkg
        cls = self.class_name
        return f"""from fastapi import FastAPI
from routers.{pkg}_router import router

app = FastAPI(
    title="{cls} API",
    description="{self.service.description or cls + ' REST API'}",
    version="{self.service.version}",
)

app.include_router(router)


@app.get("/health", tags=["Health"])
def health_check():
    return {{"status": "ok"}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
"""

    # ------------------------------------------------------------------ #
    #  README.md
    # ------------------------------------------------------------------ #
    def _readme(self) -> str:
        pkg = self.pkg
        cls = self.class_name
        return f"""# {cls} — FastAPI REST API

## Requirements

- Python 3.10+

## Installation

```bash
pip install -r requirements.txt
```

## Running the server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or simply:

```bash
python main.py
```

## Interactive docs

- Swagger UI: http://localhost:8000/docs
- ReDoc:       http://localhost:8000/redoc

## Project structure

```
.
├── main.py
├── models.py
├── requirements.txt
└── routers/
    └── {pkg}_router.py
```
"""
