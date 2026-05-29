import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from models import ServiceDefinition
from generators.base import BaseGenerator
from typing import Dict


PHP_TYPE_MAP = {
    "string": "string",
    "int": "int",
    "float": "float",
    "boolean": "bool",
    "date": "string",
    "datetime": "string",
}

PHP_DEFAULT_MAP = {
    "string": "'default'",
    "int": "0",
    "float": "0.0",
    "boolean": "false",
    "date": "date('Y-m-d')",
    "datetime": "date('Y-m-d H:i:s')",
}

HTTP_TO_LARAVEL_ROUTE = {
    "GET": "get",
    "POST": "post",
    "PUT": "put",
    "DELETE": "delete",
    "PATCH": "patch",
}


def _php_type(t: str) -> str:
    return PHP_TYPE_MAP.get(t.lower(), t)


def _php_default(t: str) -> str:
    return PHP_DEFAULT_MAP.get(t.lower(), "null")


def _laravel_path(path: str, method) -> str:
    """Convert {param} notation for Laravel routes (already compatible)."""
    return path


class PHPLaravelGenerator(BaseGenerator):
    def __init__(self, service: ServiceDefinition):
        super().__init__(service)

    def generate(self) -> Dict[str, str]:
        files = {}
        files[f"app/Http/Controllers/Api/{self.class_name}Controller.php"] = self._gen_controller()
        for model in self.service.models:
            files[f"app/Models/{model.name}.php"] = self._gen_model(model)
        files["routes/api.php"] = self._gen_routes()
        files["composer.json"] = self._gen_composer()
        files["README.md"] = self._gen_readme()
        return files

    def _gen_controller(self) -> str:
        lines = [
            "<?php",
            "",
            "namespace App\\Http\\Controllers\\Api;",
            "",
            "use App\\Http\\Controllers\\Controller;",
            "use Illuminate\\Http\\Request;",
            "use Illuminate\\Http\\JsonResponse;",
        ]

        # Use model namespaces
        for model in self.service.models:
            lines.append(f"use App\\Models\\{model.name};")

        lines += [
            "",
            f"class {self.class_name}Controller extends Controller",
            "{",
        ]

        for method in self.service.methods:
            camel = method.name[0].lower() + method.name[1:]
            method_name = camel

            # Determine if we need Request and/or route params
            has_query_or_body = any(
                p.location.value in ("query", "body", "header") for p in method.parameters
            )
            path_params = [p for p in method.parameters if p.location.value == "path"]

            # Build parameter list for the PHP method
            php_params = []
            if has_query_or_body:
                php_params.append("Request $request")
            for p in path_params:
                php_type = _php_type(p.type)
                php_params.append(f"{php_type} ${p.name}")

            params_str = ", ".join(php_params)

            if method.description:
                lines.append(f"    /**")
                lines.append(f"     * {method.description}")
                lines.append(f"     */")

            lines.append(f"    public function {method_name}({params_str}): JsonResponse")
            lines.append("    {")

            # Extract query / body params
            for p in method.parameters:
                if p.location.value == "query":
                    php_t = _php_type(p.type)
                    lines.append(f"        ${p.name} = $request->query('{p.name}');")
                elif p.location.value == "body":
                    lines.append(f"        ${p.name} = $request->input('{p.name}');")
                elif p.location.value == "header":
                    lines.append(f"        ${p.name} = $request->header('{p.name}');")

            # Build response data
            rt = method.return_type
            if rt == "void":
                lines.append("        return response()->json(['success' => true]);")
            elif self._is_primitive(rt):
                default = _php_default(rt)
                lines.append(f"        $result = {default};")
                lines.append("        return response()->json(['result' => $result]);")
            else:
                model_match = next((m for m in self.service.models if m.name == rt), None)
                if model_match:
                    lines.append(f"        $result = [")
                    for f in model_match.fields:
                        lines.append(f"            '{f.name}' => {_php_default(f.type)},")
                    lines.append("        ];")
                    lines.append("        return response()->json($result);")
                else:
                    lines.append("        return response()->json([]);")

            lines.append("    }")
            lines.append("")

        lines.append("}")
        return "\n".join(lines) + "\n"

    def _gen_model(self, model) -> str:
        fillable = [f"'{f.name}'" for f in model.fields]
        fillable_str = ", ".join(fillable)

        # Casts array
        cast_lines = []
        for f in model.fields:
            t_lower = f.type.lower()
            if t_lower == "int":
                cast_lines.append(f"        '{f.name}' => 'integer',")
            elif t_lower == "float":
                cast_lines.append(f"        '{f.name}' => 'float',")
            elif t_lower == "boolean":
                cast_lines.append(f"        '{f.name}' => 'boolean',")
            elif t_lower == "date":
                cast_lines.append(f"        '{f.name}' => 'date',")
            elif t_lower == "datetime":
                cast_lines.append(f"        '{f.name}' => 'datetime',")

        lines = [
            "<?php",
            "",
            "namespace App\\Models;",
            "",
            "use Illuminate\\Database\\Eloquent\\Model;",
            "",
            f"class {model.name} extends Model",
            "{",
            "    /**",
            "     * The attributes that are mass assignable.",
            "     *",
            "     * @var array<string>",
            "     */",
            f"    protected $fillable = [{fillable_str}];",
        ]

        if cast_lines:
            lines += [
                "",
                "    /**",
                "     * The attributes that should be cast.",
                "     *",
                "     * @var array<string, string>",
                "     */",
                "    protected $casts = [",
            ]
            lines.extend(cast_lines)
            lines.append("    ];")

        lines.append("}")
        return "\n".join(lines) + "\n"

    def _gen_routes(self) -> str:
        lines = [
            "<?php",
            "",
            "use Illuminate\\Support\\Facades\\Route;",
            f"use App\\Http\\Controllers\\Api\\{self.class_name}Controller;",
            "",
            "/*",
            f"|--------------------------------------------------------------------------",
            f"| {self.service.service_name} API Routes",
            f"|--------------------------------------------------------------------------",
            "*/",
            "",
        ]

        prefix = self.pkg.replace("_", "-")
        lines.append(f"Route::prefix('{prefix}')->group(function () {{")

        for method in self.service.methods:
            verb = HTTP_TO_LARAVEL_ROUTE.get(method.http_method.upper(), "get")
            route_path = _laravel_path(method.path, method)
            if not route_path.startswith("/"):
                route_path = "/" + route_path

            camel = method.name[0].lower() + method.name[1:]
            route_name = f"{self.pkg}.{camel}"

            if method.description:
                lines.append(f"    // {method.description}")
            lines.append(
                f"    Route::{verb}('{route_path}', [{self.class_name}Controller::class, '{camel}'])"
                f"->name('{route_name}');"
            )
            lines.append("")

        lines.append("});")
        return "\n".join(lines) + "\n"

    def _gen_composer(self) -> str:
        return f"""\
{{
    "name": "{self.pkg.replace('_', '-')}/api",
    "description": "{self.service.description or self.service.service_name + ' Laravel REST API'}",
    "type": "project",
    "require": {{
        "php": "^8.2",
        "laravel/framework": "^10.0",
        "laravel/sanctum": "^3.3",
        "laravel/tinker": "^2.8"
    }},
    "require-dev": {{
        "fakerphp/faker": "^1.9.1",
        "laravel/pint": "^1.0",
        "phpunit/phpunit": "^10.1",
        "spatie/laravel-ignition": "^2.0"
    }},
    "autoload": {{
        "psr-4": {{
            "App\\\\": "app/",
            "Database\\\\Factories\\\\": "database/factories/",
            "Database\\\\Seeders\\\\": "database/seeders/"
        }}
    }},
    "autoload-dev": {{
        "psr-4": {{
            "Tests\\\\": "tests/"
        }}
    }},
    "scripts": {{
        "post-autoload-dump": [
            "Illuminate\\\\Foundation\\\\ComposerScripts::postAutoloadDump",
            "@php artisan package:discover --ansi"
        ],
        "post-update-cmd": [
            "@php artisan vendor:publish --tag=laravel-assets --ansi --force"
        ]
    }},
    "config": {{
        "optimize-autoloader": true,
        "preferred-install": "dist",
        "sort-packages": true,
        "allow-plugins": {{
            "pestphp/pest-plugin": true,
            "php-http/discovery": true
        }}
    }},
    "minimum-stability": "stable",
    "prefer-stable": true
}}
"""

    def _gen_readme(self) -> str:
        return f"""\
# {self.service.service_name} — Laravel REST API

{self.service.description or ''}

## Requirements

- PHP >= 8.2
- Composer
- Laravel >= 10.0

## Setup

```bash
# Install PHP dependencies
composer install

# Copy environment file
cp .env.example .env

# Generate application key
php artisan key:generate

# Run migrations (if applicable)
php artisan migrate
```

## Running

```bash
php artisan serve
```

The API starts on **http://localhost:8000**

## API Base URL

`http://localhost:8000/api/{self.pkg.replace('_', '-')}`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
{"".join(f"| {m.http_method} | /api/{self.pkg.replace('_', '-')}{m.path} | {m.description or m.name} |" + chr(10) for m in self.service.methods)}\

## Models

{"".join(f"- `{model.name}`: " + ", ".join(f.name for f in model.fields) + chr(10) for model in self.service.models)}\

## Testing with Artisan

```bash
php artisan route:list
```
"""
