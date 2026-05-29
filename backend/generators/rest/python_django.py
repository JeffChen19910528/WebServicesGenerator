import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from models import ServiceDefinition, ParameterLocation
from generators.base import BaseGenerator
from typing import Dict


class PythonDjangoGenerator(BaseGenerator):
    """Generates a Django REST Framework project."""

    # ------------------------------------------------------------------ #
    #  Python / Django type mapping
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

    DJANGO_FIELD_TYPES: Dict[str, str] = {
        "string":   "models.CharField(max_length=255, blank=True, null=True)",
        "int":      "models.IntegerField(null=True, blank=True)",
        "float":    "models.FloatField(null=True, blank=True)",
        "boolean":  "models.BooleanField(default=False)",
        "date":     "models.DateField(null=True, blank=True)",
        "datetime": "models.DateTimeField(null=True, blank=True)",
    }

    DATE_TYPES = {"date", "datetime"}

    def _py_type(self, t: str) -> str:
        return self.PY_TYPES.get(t.lower(), t)

    def _django_field(self, t: str) -> str:
        return self.DJANGO_FIELD_TYPES.get(t.lower(), f"models.TextField(null=True, blank=True)")

    # ------------------------------------------------------------------ #
    #  generate()
    # ------------------------------------------------------------------ #
    def generate(self) -> Dict[str, str]:
        files: Dict[str, str] = {}
        pkg = self.pkg
        proj = f"{pkg}_project"
        app = f"{pkg}_app"

        files["requirements.txt"] = self._requirements()
        files["manage.py"] = self._manage_py(proj)
        files[f"{proj}/settings.py"] = self._settings_py(pkg, proj, app)
        files[f"{proj}/urls.py"] = self._project_urls_py(pkg, app)
        files[f"{proj}/wsgi.py"] = self._wsgi_py(proj)
        files[f"{proj}/__init__.py"] = ""
        files[f"{app}/__init__.py"] = ""
        files[f"{app}/models.py"] = self._app_models_py()
        files[f"{app}/serializers.py"] = self._serializers_py(pkg, app)
        files[f"{app}/views.py"] = self._views_py(pkg, app)
        files[f"{app}/urls.py"] = self._app_urls_py()
        files["README.md"] = self._readme(pkg, proj, app)

        return files

    # ------------------------------------------------------------------ #
    #  requirements.txt
    # ------------------------------------------------------------------ #
    def _requirements(self) -> str:
        return """django>=4.2.0
djangorestframework>=3.15.0
"""

    # ------------------------------------------------------------------ #
    #  manage.py
    # ------------------------------------------------------------------ #
    def _manage_py(self, proj: str) -> str:
        return f"""#!/usr/bin/env python
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{proj}.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Make sure it is installed and available on your "
            "PYTHONPATH environment variable. Did you forget to activate a virtual "
            "environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
"""

    # ------------------------------------------------------------------ #
    #  settings.py
    # ------------------------------------------------------------------ #
    def _settings_py(self, pkg: str, proj: str, app: str) -> str:
        return f"""from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-change-me-in-production-{pkg}-secret-key"

DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "rest_framework",
    "{app}",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "{proj}.urls"

TEMPLATES = [
    {{
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {{
            "context_processors": [
                "django.template.context_processors.request",
            ],
        }},
    }},
]

WSGI_APPLICATION = "{proj}.wsgi.application"

DATABASES = {{
    "default": {{
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }}
}}

REST_FRAMEWORK = {{
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
}}

STATIC_URL = "/static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
"""

    # ------------------------------------------------------------------ #
    #  project/urls.py
    # ------------------------------------------------------------------ #
    def _project_urls_py(self, pkg: str, app: str) -> str:
        return f"""from django.urls import path, include

urlpatterns = [
    path("api/v{self.service.version}/", include("{app}.urls")),
]
"""

    # ------------------------------------------------------------------ #
    #  wsgi.py
    # ------------------------------------------------------------------ #
    def _wsgi_py(self, proj: str) -> str:
        return f"""import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{proj}.settings")

application = get_wsgi_application()
"""

    # ------------------------------------------------------------------ #
    #  app/models.py
    # ------------------------------------------------------------------ #
    def _app_models_py(self) -> str:
        if not self.service.models:
            return "from django.db import models\n\n# No models defined\n"

        lines = ["from django.db import models", ""]

        for model in self.service.models:
            lines.append(f"\nclass {model.name}(models.Model):")
            if not model.fields:
                lines.append("    pass")
            else:
                for f in model.fields:
                    dj_field = self._django_field(f.type)
                    lines.append(f"    {f.name} = {dj_field}")
            lines.append("")
            lines.append(f"    class Meta:")
            lines.append(f"        db_table = \"{model.name.lower()}\"")
            lines.append("")
            lines.append(f"    def __str__(self):")
            first_field = model.fields[0].name if model.fields else "id"
            lines.append(f"        return str(self.{first_field})")
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    #  app/serializers.py
    # ------------------------------------------------------------------ #
    def _serializers_py(self, pkg: str, app: str) -> str:
        if not self.service.models:
            return "from rest_framework import serializers\n\n# No serializers defined\n"

        model_names = [m.name for m in self.service.models]
        model_import = ", ".join(model_names)

        lines = [
            "from rest_framework import serializers",
            f"from .models import {model_import}",
            "",
        ]

        for model in self.service.models:
            fields_list = ", ".join(
                f'"{f.name}"' for f in model.fields
            )
            if not fields_list:
                fields_list = '"__all__"'
                fields_value = '"__all__"'
            else:
                fields_value = f"[{fields_list}]"

            lines.append(f"\nclass {model.name}Serializer(serializers.ModelSerializer):")
            lines.append(f"    class Meta:")
            lines.append(f"        model = {model.name}")
            lines.append(f"        fields = {fields_value}")
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    #  app/views.py
    # ------------------------------------------------------------------ #
    def _views_py(self, pkg: str, app: str) -> str:
        model_names = {m.name for m in self.service.models}

        # Determine which models are referenced
        used_models = set()
        for method in self.service.methods:
            for p in method.parameters:
                if not self._is_primitive(p.type) and p.type in model_names:
                    used_models.add(p.type)
            if not self._is_primitive(method.return_type) and method.return_type in model_names:
                used_models.add(method.return_type)

        lines = [
            "from rest_framework.views import APIView",
            "from rest_framework.response import Response",
            "from rest_framework import status",
        ]

        if used_models:
            models_str = ", ".join(sorted(used_models))
            serializers_str = ", ".join(f"{m}Serializer" for m in sorted(used_models))
            lines.append(f"from .models import {models_str}")
            lines.append(f"from .serializers import {serializers_str}")

        lines.append("")

        for method in self.service.methods:
            class_name = "".join(w.capitalize() for w in method.name.split("_")) + "View"
            http = method.http_method.upper()
            ret_type = self._py_type(method.return_type)

            # Build the handler method body
            body_lines = []

            # Extract query/header params
            for p in method.parameters:
                if p.location == ParameterLocation.QUERY:
                    body_lines.append(f'        {p.name} = request.query_params.get("{p.name}")')
                elif p.location == ParameterLocation.HEADER:
                    body_lines.append(f'        {p.name} = request.META.get("HTTP_{p.name.upper()}")')
                elif p.location == ParameterLocation.BODY:
                    body_lines.append(f'        {p.name} = request.data')

            # Default response
            if ret_type == "None":
                body_lines.append(
                    "        return Response(status=status.HTTP_204_NO_CONTENT)"
                )
            elif ret_type == "str":
                body_lines.append(
                    '        return Response({"result": ""}, status=status.HTTP_200_OK)'
                )
            elif ret_type == "int":
                body_lines.append(
                    '        return Response({"result": 0}, status=status.HTTP_200_OK)'
                )
            elif ret_type == "float":
                body_lines.append(
                    '        return Response({"result": 0.0}, status=status.HTTP_200_OK)'
                )
            elif ret_type == "bool":
                body_lines.append(
                    '        return Response({"result": False}, status=status.HTTP_200_OK)'
                )
            else:
                body_lines.append(
                    '        return Response({"result": None}, status=status.HTTP_200_OK)'
                )

            body = "\n".join(body_lines) if body_lines else "        pass"

            # Path params — include in method signature
            path_params = [
                p.name
                for p in method.parameters
                if p.location == ParameterLocation.PATH
            ]
            extra_args = (", " + ", ".join(path_params)) if path_params else ""

            http_method_lower = http.lower()
            # map PATCH → patch, etc.
            desc = method.description or f"{method.name} view"

            lines.append(f"\nclass {class_name}(APIView):")
            lines.append(f'    """{desc}"""')
            lines.append("")
            lines.append(f"    def {http_method_lower}(self, request{extra_args}, *args, **kwargs):")
            lines.append(body)
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    #  app/urls.py
    # ------------------------------------------------------------------ #
    def _app_urls_py(self) -> str:
        cls = self.class_name
        lines = [
            "from django.urls import path",
            "from . import views",
            "",
            "urlpatterns = [",
        ]

        for method in self.service.methods:
            view_class = "".join(w.capitalize() for w in method.name.split("_")) + "View"
            # Convert FastAPI-style {param} to Django <param>
            django_path = method.path.lstrip("/")
            # Replace {param} with <param>
            import re
            django_path = re.sub(r"\{(\w+)\}", r"<\1>", django_path)
            if not django_path:
                django_path = ""
            name = method.name.replace("_", "-")
            lines.append(f'    path("{django_path}", views.{view_class}.as_view(), name="{name}"),')

        lines.append("]")
        lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    #  README.md
    # ------------------------------------------------------------------ #
    def _readme(self, pkg: str, proj: str, app: str) -> str:
        cls = self.class_name
        return f"""# {cls} — Django REST Framework API

## Requirements

- Python 3.10+

## Installation

```bash
pip install -r requirements.txt
```

## Setup & Run

```bash
# Apply migrations
python manage.py migrate

# Start the development server
python manage.py runserver 0.0.0.0:8000
```

The API will be available at `http://localhost:8000/api/v{self.service.version}/`.

## Project structure

```
.
├── manage.py
├── requirements.txt
├── {proj}/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── {app}/
    ├── __init__.py
    ├── models.py
    ├── serializers.py
    ├── views.py
    └── urls.py
```

## Endpoints

| Method | Path | View |
|--------|------|------|
{''.join(f"| {m.http_method.upper()} | /api/v{self.service.version}{m.path} | {''.join(w.capitalize() for w in m.name.split('_'))}View |" + chr(10) for m in self.service.methods)}
"""
