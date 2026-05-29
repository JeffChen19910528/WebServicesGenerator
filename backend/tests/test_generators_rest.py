"""Tests for the 14 REST code generators."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
import pytest

from generators.rest.java_spring_boot import JavaSpringBootGenerator
from generators.rest.python_fastapi import PythonFastAPIGenerator
from generators.rest.python_flask import PythonFlaskGenerator
from generators.rest.python_django import PythonDjangoGenerator
from generators.rest.nodejs_express import NodeJSExpressGenerator
from generators.rest.nodejs_nestjs import NodeJSNestJSGenerator
from generators.rest.nodejs_fastify import NodeJSFastifyGenerator
from generators.rest.csharp_aspnet import CSharpAspNetGenerator
from generators.rest.php_laravel import PHPLaravelGenerator
from generators.rest.php_slim import PHPSlimGenerator
from generators.rest.go_gin import GoGinGenerator
from generators.rest.go_echo import GoEchoGenerator
from generators.rest.ruby_rails import RubyRailsGenerator
from generators.rest.ruby_sinatra import RubySinatraGenerator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _all_content(files: dict) -> str:
    return "\n".join(files.values())


def _has_file_ending(files: dict, suffix: str) -> bool:
    return any(k.endswith(suffix) for k in files)


def _has_file_containing(files: dict, substring: str) -> bool:
    return any(substring in k for k in files)


def _assert_no_empty_files(files: dict) -> None:
    for path, content in files.items():
        assert content.strip(), f"File '{path}' is empty"


def _assert_method_names_present(files: dict, service) -> None:
    content = _all_content(files)
    for method in service.methods:
        assert method.name in content or (
            method.name[0].upper() + method.name[1:]
        ) in content, f"Method '{method.name}' not in generated content"


def _assert_model_names_present(files: dict, service) -> None:
    content = _all_content(files)
    for model in service.models:
        assert model.name in content, (
            f"Model '{model.name}' not in generated content"
        )


# ===========================================================================
# JavaSpringBootGenerator
# ===========================================================================


class TestJavaSpringBootGenerator:
    def test_imports_correctly(self):
        from generators.rest import java_spring_boot  # noqa: F401

    def test_generates_files(self, rest_service):
        files = JavaSpringBootGenerator(rest_service).generate()
        assert isinstance(files, dict) and len(files) > 0

    def test_all_files_have_content(self, rest_service):
        _assert_no_empty_files(JavaSpringBootGenerator(rest_service).generate())

    def test_contains_method_names(self, rest_service):
        files = JavaSpringBootGenerator(rest_service).generate()
        _assert_method_names_present(files, rest_service)

    def test_contains_model_names(self, rest_service):
        files = JavaSpringBootGenerator(rest_service).generate()
        _assert_model_names_present(files, rest_service)

    def test_works_with_minimal_service(self, minimal_service):
        files = JavaSpringBootGenerator(minimal_service).generate()
        assert isinstance(files, dict) and len(files) > 0

    def test_has_pom_xml(self, rest_service):
        files = JavaSpringBootGenerator(rest_service).generate()
        assert "pom.xml" in files

    def test_has_controller_java(self, rest_service):
        files = JavaSpringBootGenerator(rest_service).generate()
        assert _has_file_containing(files, "Controller.java"), (
            "No *Controller.java file found"
        )

    def test_pom_xml_is_valid_xml(self, rest_service):
        import xml.etree.ElementTree as ET

        files = JavaSpringBootGenerator(rest_service).generate()
        ET.fromstring(files["pom.xml"])

    def test_rest_controller_annotation_present(self, rest_service):
        files = JavaSpringBootGenerator(rest_service).generate()
        content = _all_content(files)
        assert "@RestController" in content

    def test_request_mapping_annotation_present(self, rest_service):
        files = JavaSpringBootGenerator(rest_service).generate()
        content = _all_content(files)
        assert "@RequestMapping" in content

    def test_model_java_generated(self, rest_service):
        files = JavaSpringBootGenerator(rest_service).generate()
        assert _has_file_containing(files, "User.java")

    def test_spring_boot_dependency_in_pom(self, rest_service):
        files = JavaSpringBootGenerator(rest_service).generate()
        assert "spring-boot-starter-web" in files["pom.xml"]


# ===========================================================================
# PythonFastAPIGenerator
# ===========================================================================


class TestPythonFastAPIGenerator:
    def test_imports_correctly(self):
        from generators.rest import python_fastapi  # noqa: F401

    def test_generates_files(self, rest_service):
        files = PythonFastAPIGenerator(rest_service).generate()
        assert isinstance(files, dict) and len(files) > 0

    def test_all_files_have_content(self, rest_service):
        _assert_no_empty_files(PythonFastAPIGenerator(rest_service).generate())

    def test_contains_method_names(self, rest_service):
        files = PythonFastAPIGenerator(rest_service).generate()
        _assert_method_names_present(files, rest_service)

    def test_contains_model_names(self, rest_service):
        files = PythonFastAPIGenerator(rest_service).generate()
        _assert_model_names_present(files, rest_service)

    def test_works_with_minimal_service(self, minimal_service):
        files = PythonFastAPIGenerator(minimal_service).generate()
        assert isinstance(files, dict) and len(files) > 0

    def test_has_requirements_txt(self, rest_service):
        files = PythonFastAPIGenerator(rest_service).generate()
        assert "requirements.txt" in files

    def test_has_main_py(self, rest_service):
        files = PythonFastAPIGenerator(rest_service).generate()
        assert "main.py" in files

    def test_requirements_contains_fastapi(self, rest_service):
        files = PythonFastAPIGenerator(rest_service).generate()
        assert "fastapi" in files["requirements.txt"]

    def test_main_py_imports_fastapi(self, rest_service):
        files = PythonFastAPIGenerator(rest_service).generate()
        assert "FastAPI" in files["main.py"]

    def test_router_file_generated(self, rest_service):
        files = PythonFastAPIGenerator(rest_service).generate()
        assert _has_file_containing(files, "_router.py")

    def test_models_py_has_basemodel(self, rest_service):
        files = PythonFastAPIGenerator(rest_service).generate()
        assert "BaseModel" in files["models.py"]

    def test_http_methods_present_in_router(self, rest_service):
        files = PythonFastAPIGenerator(rest_service).generate()
        router_file = next(k for k in files if "_router.py" in k)
        content = files[router_file]
        assert "@router.get" in content or "@router.post" in content


# ===========================================================================
# PythonFlaskGenerator
# ===========================================================================


class TestPythonFlaskGenerator:
    def test_imports_correctly(self):
        from generators.rest import python_flask  # noqa: F401

    def test_generates_files(self, rest_service):
        files = PythonFlaskGenerator(rest_service).generate()
        assert isinstance(files, dict) and len(files) > 0

    def test_all_files_have_content(self, rest_service):
        _assert_no_empty_files(PythonFlaskGenerator(rest_service).generate())

    def test_contains_method_names(self, rest_service):
        files = PythonFlaskGenerator(rest_service).generate()
        _assert_method_names_present(files, rest_service)

    def test_contains_model_names(self, rest_service):
        files = PythonFlaskGenerator(rest_service).generate()
        _assert_model_names_present(files, rest_service)

    def test_works_with_minimal_service(self, minimal_service):
        files = PythonFlaskGenerator(minimal_service).generate()
        assert isinstance(files, dict) and len(files) > 0

    def test_has_requirements_txt(self, rest_service):
        files = PythonFlaskGenerator(rest_service).generate()
        assert "requirements.txt" in files

    def test_has_app_py(self, rest_service):
        files = PythonFlaskGenerator(rest_service).generate()
        assert "app.py" in files

    def test_requirements_contains_flask(self, rest_service):
        files = PythonFlaskGenerator(rest_service).generate()
        assert "flask" in files["requirements.txt"].lower()

    def test_app_py_imports_flask(self, rest_service):
        files = PythonFlaskGenerator(rest_service).generate()
        assert "Flask" in files["app.py"]

    def test_route_decorator_present(self, rest_service):
        files = PythonFlaskGenerator(rest_service).generate()
        content = _all_content(files)
        assert "@app.route" in content or "@blueprint" in content.lower() or "route" in content


# ===========================================================================
# PythonDjangoGenerator
# ===========================================================================


class TestPythonDjangoGenerator:
    def test_imports_correctly(self):
        from generators.rest import python_django  # noqa: F401

    def test_generates_files(self, rest_service):
        files = PythonDjangoGenerator(rest_service).generate()
        assert isinstance(files, dict) and len(files) > 0

    def test_all_files_have_content(self, rest_service):
        # Django generates __init__.py which may be empty; skip those
        files = PythonDjangoGenerator(rest_service).generate()
        for path, content in files.items():
            if path.endswith("__init__.py"):
                continue  # allowed to be empty
            assert content.strip(), f"File '{path}' is empty"

    def test_contains_method_names(self, rest_service):
        files = PythonDjangoGenerator(rest_service).generate()
        _assert_method_names_present(files, rest_service)

    def test_contains_model_names(self, rest_service):
        files = PythonDjangoGenerator(rest_service).generate()
        _assert_model_names_present(files, rest_service)

    def test_works_with_minimal_service(self, minimal_service):
        files = PythonDjangoGenerator(minimal_service).generate()
        assert isinstance(files, dict) and len(files) > 0

    def test_has_requirements_txt(self, rest_service):
        files = PythonDjangoGenerator(rest_service).generate()
        assert "requirements.txt" in files

    def test_has_manage_py(self, rest_service):
        files = PythonDjangoGenerator(rest_service).generate()
        assert "manage.py" in files

    def test_requirements_contains_django(self, rest_service):
        files = PythonDjangoGenerator(rest_service).generate()
        assert "django" in files["requirements.txt"].lower()

    def test_manage_py_has_django_import(self, rest_service):
        files = PythonDjangoGenerator(rest_service).generate()
        assert "django" in files["manage.py"].lower()

    def test_views_py_generated(self, rest_service):
        files = PythonDjangoGenerator(rest_service).generate()
        assert _has_file_containing(files, "views.py")


# ===========================================================================
# NodeJSExpressGenerator
# ===========================================================================


class TestNodeJSExpressGenerator:
    def test_imports_correctly(self):
        from generators.rest import nodejs_express  # noqa: F401

    def test_generates_files(self, rest_service):
        files = NodeJSExpressGenerator(rest_service).generate()
        assert isinstance(files, dict) and len(files) > 0

    def test_all_files_have_content(self, rest_service):
        _assert_no_empty_files(NodeJSExpressGenerator(rest_service).generate())

    def test_contains_method_names(self, rest_service):
        files = NodeJSExpressGenerator(rest_service).generate()
        _assert_method_names_present(files, rest_service)

    def test_contains_model_names(self, rest_service):
        files = NodeJSExpressGenerator(rest_service).generate()
        _assert_model_names_present(files, rest_service)

    def test_works_with_minimal_service(self, minimal_service):
        files = NodeJSExpressGenerator(minimal_service).generate()
        assert isinstance(files, dict) and len(files) > 0

    def test_has_package_json(self, rest_service):
        files = NodeJSExpressGenerator(rest_service).generate()
        assert "package.json" in files

    def test_has_routes_file(self, rest_service):
        files = NodeJSExpressGenerator(rest_service).generate()
        assert _has_file_containing(files, "Routes") or _has_file_containing(files, "routes"), (
            "No routes file found"
        )

    def test_package_json_is_valid_json(self, rest_service):
        files = NodeJSExpressGenerator(rest_service).generate()
        data = json.loads(files["package.json"])
        assert "dependencies" in data

    def test_express_in_package_json(self, rest_service):
        files = NodeJSExpressGenerator(rest_service).generate()
        data = json.loads(files["package.json"])
        assert "express" in data["dependencies"]

    def test_router_usage_in_routes(self, rest_service):
        files = NodeJSExpressGenerator(rest_service).generate()
        routes_file = next(k for k in files if "routes" in k.lower() or "Routes" in k)
        content = files[routes_file]
        assert "router" in content.lower() or "Router" in content


# ===========================================================================
# NodeJSNestJSGenerator
# ===========================================================================


class TestNodeJSNestJSGenerator:
    def test_imports_correctly(self):
        from generators.rest import nodejs_nestjs  # noqa: F401

    def test_generates_files(self, rest_service):
        files = NodeJSNestJSGenerator(rest_service).generate()
        assert isinstance(files, dict) and len(files) > 0

    def test_all_files_have_content(self, rest_service):
        _assert_no_empty_files(NodeJSNestJSGenerator(rest_service).generate())

    def test_contains_method_names(self, rest_service):
        files = NodeJSNestJSGenerator(rest_service).generate()
        _assert_method_names_present(files, rest_service)

    def test_contains_model_names(self, rest_service):
        files = NodeJSNestJSGenerator(rest_service).generate()
        _assert_model_names_present(files, rest_service)

    def test_works_with_minimal_service(self, minimal_service):
        files = NodeJSNestJSGenerator(minimal_service).generate()
        assert isinstance(files, dict) and len(files) > 0

    def test_has_package_json(self, rest_service):
        files = NodeJSNestJSGenerator(rest_service).generate()
        assert "package.json" in files

    def test_has_tsconfig_json(self, rest_service):
        files = NodeJSNestJSGenerator(rest_service).generate()
        assert "tsconfig.json" in files

    def test_package_json_is_valid_json(self, rest_service):
        files = NodeJSNestJSGenerator(rest_service).generate()
        data = json.loads(files["package.json"])
        assert "dependencies" in data

    def test_tsconfig_json_is_valid_json(self, rest_service):
        files = NodeJSNestJSGenerator(rest_service).generate()
        data = json.loads(files["tsconfig.json"])
        assert "compilerOptions" in data

    def test_nestjs_core_in_package_json(self, rest_service):
        files = NodeJSNestJSGenerator(rest_service).generate()
        data = json.loads(files["package.json"])
        assert "@nestjs/core" in data["dependencies"]

    def test_controller_decorator_present(self, rest_service):
        files = NodeJSNestJSGenerator(rest_service).generate()
        content = _all_content(files)
        assert "@Controller" in content


# ===========================================================================
# NodeJSFastifyGenerator
# ===========================================================================


class TestNodeJSFastifyGenerator:
    def test_imports_correctly(self):
        from generators.rest import nodejs_fastify  # noqa: F401

    def test_generates_files(self, rest_service):
        files = NodeJSFastifyGenerator(rest_service).generate()
        assert isinstance(files, dict) and len(files) > 0

    def test_all_files_have_content(self, rest_service):
        _assert_no_empty_files(NodeJSFastifyGenerator(rest_service).generate())

    def test_contains_method_names(self, rest_service):
        files = NodeJSFastifyGenerator(rest_service).generate()
        _assert_method_names_present(files, rest_service)

    def test_contains_model_names(self, rest_service):
        files = NodeJSFastifyGenerator(rest_service).generate()
        _assert_model_names_present(files, rest_service)

    def test_works_with_minimal_service(self, minimal_service):
        files = NodeJSFastifyGenerator(minimal_service).generate()
        assert isinstance(files, dict) and len(files) > 0

    def test_has_package_json(self, rest_service):
        files = NodeJSFastifyGenerator(rest_service).generate()
        assert "package.json" in files

    def test_has_app_js(self, rest_service):
        files = NodeJSFastifyGenerator(rest_service).generate()
        assert _has_file_containing(files, "app.js"), "No app.js found"

    def test_package_json_is_valid_json(self, rest_service):
        files = NodeJSFastifyGenerator(rest_service).generate()
        data = json.loads(files["package.json"])
        assert "dependencies" in data

    def test_fastify_in_package_json(self, rest_service):
        files = NodeJSFastifyGenerator(rest_service).generate()
        data = json.loads(files["package.json"])
        assert "fastify" in data["dependencies"]

    def test_fastify_imported_in_app_js(self, rest_service):
        files = NodeJSFastifyGenerator(rest_service).generate()
        app_js = next(v for k, v in files.items() if "app.js" in k)
        assert "fastify" in app_js.lower()


# ===========================================================================
# CSharpAspNetGenerator
# ===========================================================================


class TestCSharpAspNetGenerator:
    def test_imports_correctly(self):
        from generators.rest import csharp_aspnet  # noqa: F401

    def test_generates_files(self, rest_service):
        files = CSharpAspNetGenerator(rest_service).generate()
        assert isinstance(files, dict) and len(files) > 0

    def test_all_files_have_content(self, rest_service):
        _assert_no_empty_files(CSharpAspNetGenerator(rest_service).generate())

    def test_contains_method_names(self, rest_service):
        files = CSharpAspNetGenerator(rest_service).generate()
        content = _all_content(files)
        for method in rest_service.methods:
            cap = method.name[0].upper() + method.name[1:]
            assert cap in content or method.name in content

    def test_contains_model_names(self, rest_service):
        files = CSharpAspNetGenerator(rest_service).generate()
        _assert_model_names_present(files, rest_service)

    def test_works_with_minimal_service(self, minimal_service):
        files = CSharpAspNetGenerator(minimal_service).generate()
        assert isinstance(files, dict) and len(files) > 0

    def test_has_csproj_file(self, rest_service):
        files = CSharpAspNetGenerator(rest_service).generate()
        assert _has_file_ending(files, ".csproj"), "No .csproj file generated"

    def test_has_controller_cs(self, rest_service):
        files = CSharpAspNetGenerator(rest_service).generate()
        assert _has_file_containing(files, "Controller.cs"), (
            "No *Controller.cs file found"
        )

    def test_api_controller_attribute_present(self, rest_service):
        files = CSharpAspNetGenerator(rest_service).generate()
        content = _all_content(files)
        assert "[ApiController]" in content

    def test_model_cs_generated(self, rest_service):
        files = CSharpAspNetGenerator(rest_service).generate()
        assert _has_file_containing(files, "User.cs")

    def test_program_cs_or_startup_cs_present(self, rest_service):
        files = CSharpAspNetGenerator(rest_service).generate()
        assert "Program.cs" in files or _has_file_containing(files, "Startup.cs")


# ===========================================================================
# PHPLaravelGenerator
# ===========================================================================


class TestPHPLaravelGenerator:
    def test_imports_correctly(self):
        from generators.rest import php_laravel  # noqa: F401

    def test_generates_files(self, rest_service):
        files = PHPLaravelGenerator(rest_service).generate()
        assert isinstance(files, dict) and len(files) > 0

    def test_all_files_have_content(self, rest_service):
        _assert_no_empty_files(PHPLaravelGenerator(rest_service).generate())

    def test_contains_method_names(self, rest_service):
        files = PHPLaravelGenerator(rest_service).generate()
        _assert_method_names_present(files, rest_service)

    def test_contains_model_names(self, rest_service):
        files = PHPLaravelGenerator(rest_service).generate()
        _assert_model_names_present(files, rest_service)

    def test_works_with_minimal_service(self, minimal_service):
        files = PHPLaravelGenerator(minimal_service).generate()
        assert isinstance(files, dict) and len(files) > 0

    def test_has_composer_json(self, rest_service):
        files = PHPLaravelGenerator(rest_service).generate()
        assert "composer.json" in files

    def test_has_controller_php(self, rest_service):
        files = PHPLaravelGenerator(rest_service).generate()
        assert _has_file_containing(files, "Controller.php"), (
            "No *Controller.php file found"
        )

    def test_composer_json_is_valid_json(self, rest_service):
        files = PHPLaravelGenerator(rest_service).generate()
        data = json.loads(files["composer.json"])
        assert "require" in data or "name" in data

    def test_laravel_framework_in_composer(self, rest_service):
        files = PHPLaravelGenerator(rest_service).generate()
        composer_str = files["composer.json"]
        assert "laravel" in composer_str.lower()

    def test_controller_has_php_opening_tag(self, rest_service):
        files = PHPLaravelGenerator(rest_service).generate()
        controller_file = next(k for k in files if "Controller.php" in k)
        assert "<?php" in files[controller_file]


# ===========================================================================
# PHPSlimGenerator
# ===========================================================================


class TestPHPSlimGenerator:
    def test_imports_correctly(self):
        from generators.rest import php_slim  # noqa: F401

    def test_generates_files(self, rest_service):
        files = PHPSlimGenerator(rest_service).generate()
        assert isinstance(files, dict) and len(files) > 0

    def test_all_files_have_content(self, rest_service):
        _assert_no_empty_files(PHPSlimGenerator(rest_service).generate())

    def test_contains_method_names(self, rest_service):
        files = PHPSlimGenerator(rest_service).generate()
        _assert_method_names_present(files, rest_service)

    def test_contains_model_names(self, rest_service):
        files = PHPSlimGenerator(rest_service).generate()
        _assert_model_names_present(files, rest_service)

    def test_works_with_minimal_service(self, minimal_service):
        files = PHPSlimGenerator(minimal_service).generate()
        assert isinstance(files, dict) and len(files) > 0

    def test_has_composer_json(self, rest_service):
        files = PHPSlimGenerator(rest_service).generate()
        assert "composer.json" in files

    def test_has_index_php(self, rest_service):
        files = PHPSlimGenerator(rest_service).generate()
        assert _has_file_containing(files, "index.php"), "No index.php found"

    def test_composer_json_is_valid_json(self, rest_service):
        files = PHPSlimGenerator(rest_service).generate()
        data = json.loads(files["composer.json"])
        assert "require" in data or "name" in data

    def test_slim_in_composer(self, rest_service):
        files = PHPSlimGenerator(rest_service).generate()
        assert "slim" in files["composer.json"].lower()

    def test_index_php_has_opening_tag(self, rest_service):
        files = PHPSlimGenerator(rest_service).generate()
        index_file = next(k for k in files if "index.php" in k)
        assert "<?php" in files[index_file]


# ===========================================================================
# GoGinGenerator
# ===========================================================================


class TestGoGinGenerator:
    def test_imports_correctly(self):
        from generators.rest import go_gin  # noqa: F401

    def test_generates_files(self, rest_service):
        files = GoGinGenerator(rest_service).generate()
        assert isinstance(files, dict) and len(files) > 0

    def test_all_files_have_content(self, rest_service):
        _assert_no_empty_files(GoGinGenerator(rest_service).generate())

    def test_contains_method_names(self, rest_service):
        files = GoGinGenerator(rest_service).generate()
        content = _all_content(files)
        for method in rest_service.methods:
            cap = method.name[0].upper() + method.name[1:]
            assert cap in content or method.name in content

    def test_contains_model_names(self, rest_service):
        files = GoGinGenerator(rest_service).generate()
        _assert_model_names_present(files, rest_service)

    def test_works_with_minimal_service(self, minimal_service):
        files = GoGinGenerator(minimal_service).generate()
        assert isinstance(files, dict) and len(files) > 0

    def test_has_go_mod(self, rest_service):
        files = GoGinGenerator(rest_service).generate()
        assert "go.mod" in files

    def test_has_main_go(self, rest_service):
        files = GoGinGenerator(rest_service).generate()
        assert "main.go" in files

    def test_go_mod_module_declaration(self, rest_service):
        files = GoGinGenerator(rest_service).generate()
        assert "module" in files["go.mod"]

    def test_gin_import_in_main(self, rest_service):
        files = GoGinGenerator(rest_service).generate()
        content = _all_content(files)
        assert "gin" in content.lower()

    def test_package_main_present(self, rest_service):
        files = GoGinGenerator(rest_service).generate()
        assert "package main" in files["main.go"]


# ===========================================================================
# GoEchoGenerator
# ===========================================================================


class TestGoEchoGenerator:
    def test_imports_correctly(self):
        from generators.rest import go_echo  # noqa: F401

    def test_generates_files(self, rest_service):
        files = GoEchoGenerator(rest_service).generate()
        assert isinstance(files, dict) and len(files) > 0

    def test_all_files_have_content(self, rest_service):
        _assert_no_empty_files(GoEchoGenerator(rest_service).generate())

    def test_contains_method_names(self, rest_service):
        files = GoEchoGenerator(rest_service).generate()
        content = _all_content(files)
        for method in rest_service.methods:
            cap = method.name[0].upper() + method.name[1:]
            assert cap in content or method.name in content

    def test_contains_model_names(self, rest_service):
        files = GoEchoGenerator(rest_service).generate()
        _assert_model_names_present(files, rest_service)

    def test_works_with_minimal_service(self, minimal_service):
        files = GoEchoGenerator(minimal_service).generate()
        assert isinstance(files, dict) and len(files) > 0

    def test_has_go_mod(self, rest_service):
        files = GoEchoGenerator(rest_service).generate()
        assert "go.mod" in files

    def test_has_main_go(self, rest_service):
        files = GoEchoGenerator(rest_service).generate()
        assert "main.go" in files

    def test_go_mod_module_declaration(self, rest_service):
        files = GoEchoGenerator(rest_service).generate()
        assert "module" in files["go.mod"]

    def test_echo_import_in_main_or_handlers(self, rest_service):
        files = GoEchoGenerator(rest_service).generate()
        content = _all_content(files)
        assert "echo" in content.lower()

    def test_package_main_present(self, rest_service):
        files = GoEchoGenerator(rest_service).generate()
        assert "package main" in files["main.go"]


# ===========================================================================
# RubyRailsGenerator
# ===========================================================================


class TestRubyRailsGenerator:
    def test_imports_correctly(self):
        from generators.rest import ruby_rails  # noqa: F401

    def test_generates_files(self, rest_service):
        files = RubyRailsGenerator(rest_service).generate()
        assert isinstance(files, dict) and len(files) > 0

    def test_all_files_have_content(self, rest_service):
        _assert_no_empty_files(RubyRailsGenerator(rest_service).generate())

    def test_contains_method_names(self, rest_service):
        files = RubyRailsGenerator(rest_service).generate()
        _assert_method_names_present(files, rest_service)

    def test_contains_model_names(self, rest_service):
        files = RubyRailsGenerator(rest_service).generate()
        _assert_model_names_present(files, rest_service)

    def test_works_with_minimal_service(self, minimal_service):
        files = RubyRailsGenerator(minimal_service).generate()
        assert isinstance(files, dict) and len(files) > 0

    def test_has_gemfile(self, rest_service):
        files = RubyRailsGenerator(rest_service).generate()
        assert "Gemfile" in files

    def test_has_controller_rb(self, rest_service):
        files = RubyRailsGenerator(rest_service).generate()
        assert _has_file_containing(files, "_controller.rb"), (
            "No *_controller.rb file found"
        )

    def test_gemfile_references_rails(self, rest_service):
        files = RubyRailsGenerator(rest_service).generate()
        assert "rails" in files["Gemfile"].lower()

    def test_controller_inherits_application_controller(self, rest_service):
        files = RubyRailsGenerator(rest_service).generate()
        content = _all_content(files)
        assert "ApplicationController" in content or "ActionController" in content

    def test_routes_rb_generated(self, rest_service):
        files = RubyRailsGenerator(rest_service).generate()
        assert _has_file_containing(files, "routes.rb")


# ===========================================================================
# RubySinatraGenerator
# ===========================================================================


class TestRubySinatraGenerator:
    def test_imports_correctly(self):
        from generators.rest import ruby_sinatra  # noqa: F401

    def test_generates_files(self, rest_service):
        files = RubySinatraGenerator(rest_service).generate()
        assert isinstance(files, dict) and len(files) > 0

    def test_all_files_have_content(self, rest_service):
        _assert_no_empty_files(RubySinatraGenerator(rest_service).generate())

    def test_contains_method_names(self, rest_service):
        files = RubySinatraGenerator(rest_service).generate()
        _assert_method_names_present(files, rest_service)

    def test_contains_model_names(self, rest_service):
        files = RubySinatraGenerator(rest_service).generate()
        _assert_model_names_present(files, rest_service)

    def test_works_with_minimal_service(self, minimal_service):
        files = RubySinatraGenerator(minimal_service).generate()
        assert isinstance(files, dict) and len(files) > 0

    def test_has_gemfile(self, rest_service):
        files = RubySinatraGenerator(rest_service).generate()
        assert "Gemfile" in files

    def test_has_app_rb(self, rest_service):
        files = RubySinatraGenerator(rest_service).generate()
        assert "app.rb" in files

    def test_gemfile_references_sinatra(self, rest_service):
        files = RubySinatraGenerator(rest_service).generate()
        assert "sinatra" in files["Gemfile"].lower()

    def test_app_rb_requires_sinatra(self, rest_service):
        files = RubySinatraGenerator(rest_service).generate()
        assert "sinatra" in files["app.rb"].lower()

    def test_http_verb_methods_present_in_app_rb(self, rest_service):
        files = RubySinatraGenerator(rest_service).generate()
        content = files["app.rb"]
        # Sinatra uses get, post, put, delete blocks
        assert any(kw in content for kw in ("get '", "post '", "put '", "delete '", 'get "', 'post "', 'put "', 'delete "')), (
            "No HTTP verb route definitions found in app.rb"
        )
