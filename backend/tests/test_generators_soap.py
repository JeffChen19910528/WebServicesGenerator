"""Tests for the 7 SOAP code generators."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest

from generators.soap.java_spring import JavaSpringWSGenerator
from generators.soap.java_cxf import JavaCXFGenerator
from generators.soap.python_spyne import PythonSpyneGenerator
from generators.soap.nodejs_soap import NodeJSSoapGenerator
from generators.soap.csharp_wcf import CSharpWCFGenerator
from generators.soap.php_soap import PHPSoapGenerator
from generators.soap.go_soap import GoSoapGenerator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _all_content(files: dict) -> str:
    """Return all file contents joined into one big string for searching."""
    return "\n".join(files.values())


def _has_file_ending(files: dict, suffix: str) -> bool:
    return any(k.endswith(suffix) for k in files)


def _has_file_containing(files: dict, substring: str) -> bool:
    return any(substring in k for k in files)


# ===========================================================================
# JavaSpringWSGenerator
# ===========================================================================


class TestJavaSpringWSGenerator:
    def test_imports_correctly(self):
        """Module imports without error."""
        from generators.soap import java_spring  # noqa: F401

    def test_generates_files(self, soap_service):
        gen = JavaSpringWSGenerator(soap_service)
        files = gen.generate()
        assert isinstance(files, dict)
        assert len(files) > 0

    def test_all_files_have_content(self, soap_service):
        files = JavaSpringWSGenerator(soap_service).generate()
        for path, content in files.items():
            assert content.strip(), f"File '{path}' is empty"

    def test_contains_method_names(self, soap_service):
        files = JavaSpringWSGenerator(soap_service).generate()
        content = _all_content(files)
        for method in soap_service.methods:
            assert method.name in content, (
                f"Method '{method.name}' not found in generated content"
            )

    def test_contains_model_names(self, soap_service):
        files = JavaSpringWSGenerator(soap_service).generate()
        content = _all_content(files)
        assert "Order" in content

    def test_works_with_minimal_service(self, minimal_service):
        gen = JavaSpringWSGenerator(minimal_service)
        files = gen.generate()
        assert isinstance(files, dict)
        assert len(files) > 0

    def test_has_pom_xml(self, soap_service):
        files = JavaSpringWSGenerator(soap_service).generate()
        assert "pom.xml" in files

    def test_has_xsd_file(self, soap_service):
        files = JavaSpringWSGenerator(soap_service).generate()
        assert _has_file_ending(files, ".xsd"), "No .xsd file generated"

    def test_pom_xml_is_valid_xml(self, soap_service):
        import xml.etree.ElementTree as ET

        files = JavaSpringWSGenerator(soap_service).generate()
        ET.fromstring(files["pom.xml"])  # raises if invalid

    def test_xsd_file_is_valid_xml(self, soap_service):
        import xml.etree.ElementTree as ET

        files = JavaSpringWSGenerator(soap_service).generate()
        xsd_file = next(k for k in files if k.endswith(".xsd"))
        ET.fromstring(files[xsd_file])

    def test_namespace_in_xsd(self, soap_service):
        files = JavaSpringWSGenerator(soap_service).generate()
        xsd_file = next(k for k in files if k.endswith(".xsd"))
        assert soap_service.namespace in files[xsd_file]

    def test_service_name_in_pom_xml(self, soap_service):
        files = JavaSpringWSGenerator(soap_service).generate()
        assert soap_service.service_name in files["pom.xml"]

    def test_endpoint_file_generated(self, soap_service):
        files = JavaSpringWSGenerator(soap_service).generate()
        assert _has_file_containing(files, "Endpoint.java")

    def test_minimal_service_has_pom_and_xsd(self, minimal_service):
        files = JavaSpringWSGenerator(minimal_service).generate()
        assert "pom.xml" in files
        assert _has_file_ending(files, ".xsd")


# ===========================================================================
# JavaCXFGenerator
# ===========================================================================


class TestJavaCXFGenerator:
    def test_imports_correctly(self):
        from generators.soap import java_cxf  # noqa: F401

    def test_generates_files(self, soap_service):
        files = JavaCXFGenerator(soap_service).generate()
        assert isinstance(files, dict)
        assert len(files) > 0

    def test_all_files_have_content(self, soap_service):
        files = JavaCXFGenerator(soap_service).generate()
        for path, content in files.items():
            assert content.strip(), f"File '{path}' is empty"

    def test_contains_method_names(self, soap_service):
        files = JavaCXFGenerator(soap_service).generate()
        content = _all_content(files)
        for method in soap_service.methods:
            assert method.name in content

    def test_contains_model_names(self, soap_service):
        files = JavaCXFGenerator(soap_service).generate()
        content = _all_content(files)
        assert "Order" in content

    def test_works_with_minimal_service(self, minimal_service):
        files = JavaCXFGenerator(minimal_service).generate()
        assert isinstance(files, dict)
        assert len(files) > 0

    def test_has_pom_xml(self, soap_service):
        files = JavaCXFGenerator(soap_service).generate()
        assert "pom.xml" in files

    def test_has_service_java_file(self, soap_service):
        files = JavaCXFGenerator(soap_service).generate()
        assert _has_file_containing(files, "Service.java"), (
            "No *Service.java file found"
        )

    def test_pom_xml_is_valid_xml(self, soap_service):
        import xml.etree.ElementTree as ET

        files = JavaCXFGenerator(soap_service).generate()
        ET.fromstring(files["pom.xml"])

    def test_service_interface_contains_webservice_annotation(self, soap_service):
        files = JavaCXFGenerator(soap_service).generate()
        content = _all_content(files)
        assert "@WebService" in content

    def test_namespace_referenced(self, soap_service):
        files = JavaCXFGenerator(soap_service).generate()
        content = _all_content(files)
        assert soap_service.namespace in content

    def test_model_class_generated(self, soap_service):
        files = JavaCXFGenerator(soap_service).generate()
        assert _has_file_containing(files, "Order.java")

    def test_minimal_service_has_pom_and_service_java(self, minimal_service):
        files = JavaCXFGenerator(minimal_service).generate()
        assert "pom.xml" in files
        assert _has_file_containing(files, "Service.java")


# ===========================================================================
# PythonSpyneGenerator
# ===========================================================================


class TestPythonSpyneGenerator:
    def test_imports_correctly(self):
        from generators.soap import python_spyne  # noqa: F401

    def test_generates_files(self, soap_service):
        files = PythonSpyneGenerator(soap_service).generate()
        assert isinstance(files, dict)
        assert len(files) > 0

    def test_all_files_have_content(self, soap_service):
        files = PythonSpyneGenerator(soap_service).generate()
        for path, content in files.items():
            assert content.strip(), f"File '{path}' is empty"

    def test_contains_method_names(self, soap_service):
        files = PythonSpyneGenerator(soap_service).generate()
        content = _all_content(files)
        for method in soap_service.methods:
            assert method.name in content

    def test_contains_model_names(self, soap_service):
        files = PythonSpyneGenerator(soap_service).generate()
        content = _all_content(files)
        assert "Order" in content

    def test_works_with_minimal_service(self, minimal_service):
        files = PythonSpyneGenerator(minimal_service).generate()
        assert isinstance(files, dict)
        assert len(files) > 0

    def test_has_requirements_txt(self, soap_service):
        files = PythonSpyneGenerator(soap_service).generate()
        assert "requirements.txt" in files

    def test_has_service_py(self, soap_service):
        files = PythonSpyneGenerator(soap_service).generate()
        assert "service.py" in files

    def test_requirements_contains_spyne(self, soap_service):
        files = PythonSpyneGenerator(soap_service).generate()
        assert "spyne" in files["requirements.txt"]

    def test_service_py_contains_servicebase(self, soap_service):
        files = PythonSpyneGenerator(soap_service).generate()
        assert "ServiceBase" in files["service.py"]

    def test_namespace_in_service_py(self, soap_service):
        files = PythonSpyneGenerator(soap_service).generate()
        assert soap_service.namespace in files["service.py"]

    def test_rpc_decorator_present(self, soap_service):
        files = PythonSpyneGenerator(soap_service).generate()
        assert "@rpc" in files["service.py"]

    def test_minimal_service_has_requirements_and_service(self, minimal_service):
        files = PythonSpyneGenerator(minimal_service).generate()
        assert "requirements.txt" in files
        assert "service.py" in files


# ===========================================================================
# NodeJSSoapGenerator
# ===========================================================================


class TestNodeJSSoapGenerator:
    def test_imports_correctly(self):
        from generators.soap import nodejs_soap  # noqa: F401

    def test_generates_files(self, soap_service):
        files = NodeJSSoapGenerator(soap_service).generate()
        assert isinstance(files, dict)
        assert len(files) > 0

    def test_all_files_have_content(self, soap_service):
        files = NodeJSSoapGenerator(soap_service).generate()
        for path, content in files.items():
            assert content.strip(), f"File '{path}' is empty"

    def test_contains_method_names(self, soap_service):
        files = NodeJSSoapGenerator(soap_service).generate()
        content = _all_content(files)
        for method in soap_service.methods:
            assert method.name in content

    def test_contains_model_names(self, soap_service):
        files = NodeJSSoapGenerator(soap_service).generate()
        content = _all_content(files)
        assert "Order" in content

    def test_works_with_minimal_service(self, minimal_service):
        files = NodeJSSoapGenerator(minimal_service).generate()
        assert isinstance(files, dict)
        assert len(files) > 0

    def test_has_package_json(self, soap_service):
        files = NodeJSSoapGenerator(soap_service).generate()
        assert "package.json" in files

    def test_has_wsdl_file(self, soap_service):
        files = NodeJSSoapGenerator(soap_service).generate()
        assert _has_file_ending(files, ".wsdl"), "No .wsdl file generated"

    def test_package_json_is_valid_json(self, soap_service):
        import json

        files = NodeJSSoapGenerator(soap_service).generate()
        data = json.loads(files["package.json"])
        assert "name" in data
        assert "dependencies" in data

    def test_wsdl_is_valid_xml(self, soap_service):
        import xml.etree.ElementTree as ET

        files = NodeJSSoapGenerator(soap_service).generate()
        wsdl_file = next(k for k in files if k.endswith(".wsdl"))
        ET.fromstring(files[wsdl_file])

    def test_namespace_in_wsdl(self, soap_service):
        files = NodeJSSoapGenerator(soap_service).generate()
        wsdl_file = next(k for k in files if k.endswith(".wsdl"))
        assert soap_service.namespace in files[wsdl_file]

    def test_soap_dependency_in_package_json(self, soap_service):
        import json

        files = NodeJSSoapGenerator(soap_service).generate()
        data = json.loads(files["package.json"])
        assert "soap" in data["dependencies"]

    def test_minimal_service_has_package_and_wsdl(self, minimal_service):
        files = NodeJSSoapGenerator(minimal_service).generate()
        assert "package.json" in files
        assert _has_file_ending(files, ".wsdl")


# ===========================================================================
# CSharpWCFGenerator
# ===========================================================================


class TestCSharpWCFGenerator:
    def test_imports_correctly(self):
        from generators.soap import csharp_wcf  # noqa: F401

    def test_generates_files(self, soap_service):
        files = CSharpWCFGenerator(soap_service).generate()
        assert isinstance(files, dict)
        assert len(files) > 0

    def test_all_files_have_content(self, soap_service):
        files = CSharpWCFGenerator(soap_service).generate()
        for path, content in files.items():
            assert content.strip(), f"File '{path}' is empty"

    def test_contains_method_names(self, soap_service):
        files = CSharpWCFGenerator(soap_service).generate()
        content = _all_content(files)
        for method in soap_service.methods:
            # CSharp capitalises method names
            assert method.name[0].upper() + method.name[1:] in content

    def test_contains_model_names(self, soap_service):
        files = CSharpWCFGenerator(soap_service).generate()
        content = _all_content(files)
        assert "Order" in content

    def test_works_with_minimal_service(self, minimal_service):
        files = CSharpWCFGenerator(minimal_service).generate()
        assert isinstance(files, dict)
        assert len(files) > 0

    def test_has_csproj_file(self, soap_service):
        files = CSharpWCFGenerator(soap_service).generate()
        assert _has_file_ending(files, ".csproj"), "No .csproj file generated"

    def test_csproj_references_corewcf(self, soap_service):
        files = CSharpWCFGenerator(soap_service).generate()
        csproj = next(v for k, v in files.items() if k.endswith(".csproj"))
        assert "CoreWCF" in csproj

    def test_service_contract_annotation(self, soap_service):
        files = CSharpWCFGenerator(soap_service).generate()
        content = _all_content(files)
        assert "ServiceContract" in content

    def test_operation_contract_annotation(self, soap_service):
        files = CSharpWCFGenerator(soap_service).generate()
        content = _all_content(files)
        assert "OperationContract" in content

    def test_namespace_in_interface(self, soap_service):
        files = CSharpWCFGenerator(soap_service).generate()
        content = _all_content(files)
        assert soap_service.namespace in content

    def test_model_cs_file_generated(self, soap_service):
        files = CSharpWCFGenerator(soap_service).generate()
        assert _has_file_containing(files, "Order.cs")

    def test_minimal_service_has_csproj(self, minimal_service):
        files = CSharpWCFGenerator(minimal_service).generate()
        assert _has_file_ending(files, ".csproj")


# ===========================================================================
# PHPSoapGenerator
# ===========================================================================


class TestPHPSoapGenerator:
    def test_imports_correctly(self):
        from generators.soap import php_soap  # noqa: F401

    def test_generates_files(self, soap_service):
        files = PHPSoapGenerator(soap_service).generate()
        assert isinstance(files, dict)
        assert len(files) > 0

    def test_all_files_have_content(self, soap_service):
        files = PHPSoapGenerator(soap_service).generate()
        for path, content in files.items():
            assert content.strip(), f"File '{path}' is empty"

    def test_contains_method_names(self, soap_service):
        files = PHPSoapGenerator(soap_service).generate()
        content = _all_content(files)
        for method in soap_service.methods:
            assert method.name in content

    def test_contains_model_names(self, soap_service):
        files = PHPSoapGenerator(soap_service).generate()
        content = _all_content(files)
        assert "Order" in content

    def test_works_with_minimal_service(self, minimal_service):
        files = PHPSoapGenerator(minimal_service).generate()
        assert isinstance(files, dict)
        assert len(files) > 0

    def test_has_server_php(self, soap_service):
        files = PHPSoapGenerator(soap_service).generate()
        assert "server.php" in files

    def test_has_wsdl_file(self, soap_service):
        files = PHPSoapGenerator(soap_service).generate()
        assert _has_file_ending(files, ".wsdl"), "No .wsdl file generated"

    def test_server_php_uses_soapserver(self, soap_service):
        files = PHPSoapGenerator(soap_service).generate()
        assert "SoapServer" in files["server.php"]

    def test_wsdl_is_valid_xml(self, soap_service):
        import xml.etree.ElementTree as ET

        files = PHPSoapGenerator(soap_service).generate()
        wsdl_file = next(k for k in files if k.endswith(".wsdl"))
        ET.fromstring(files[wsdl_file])

    def test_namespace_in_wsdl(self, soap_service):
        files = PHPSoapGenerator(soap_service).generate()
        wsdl_file = next(k for k in files if k.endswith(".wsdl"))
        assert soap_service.namespace in files[wsdl_file]

    def test_minimal_service_has_server_php_and_wsdl(self, minimal_service):
        files = PHPSoapGenerator(minimal_service).generate()
        assert "server.php" in files
        assert _has_file_ending(files, ".wsdl")


# ===========================================================================
# GoSoapGenerator
# ===========================================================================


class TestGoSoapGenerator:
    def test_imports_correctly(self):
        from generators.soap import go_soap  # noqa: F401

    def test_generates_files(self, soap_service):
        files = GoSoapGenerator(soap_service).generate()
        assert isinstance(files, dict)
        assert len(files) > 0

    def test_all_files_have_content(self, soap_service):
        files = GoSoapGenerator(soap_service).generate()
        for path, content in files.items():
            assert content.strip(), f"File '{path}' is empty"

    def test_contains_method_names(self, soap_service):
        files = GoSoapGenerator(soap_service).generate()
        content = _all_content(files)
        for method in soap_service.methods:
            # Go capitalises exported functions
            assert method.name[0].upper() + method.name[1:] in content

    def test_contains_model_names(self, soap_service):
        files = GoSoapGenerator(soap_service).generate()
        content = _all_content(files)
        assert "Order" in content

    def test_works_with_minimal_service(self, minimal_service):
        files = GoSoapGenerator(minimal_service).generate()
        assert isinstance(files, dict)
        assert len(files) > 0

    def test_has_go_mod(self, soap_service):
        files = GoSoapGenerator(soap_service).generate()
        assert "go.mod" in files

    def test_has_main_go(self, soap_service):
        files = GoSoapGenerator(soap_service).generate()
        assert "main.go" in files

    def test_go_mod_has_module_declaration(self, soap_service):
        files = GoSoapGenerator(soap_service).generate()
        assert "module" in files["go.mod"]
        assert "go 1." in files["go.mod"]

    def test_main_go_has_package_main(self, soap_service):
        files = GoSoapGenerator(soap_service).generate()
        assert "package main" in files["main.go"]

    def test_main_go_has_http_handler(self, soap_service):
        files = GoSoapGenerator(soap_service).generate()
        assert "http.HandleFunc" in files["main.go"]

    def test_wsdl_file_is_valid_xml(self, soap_service):
        import xml.etree.ElementTree as ET

        files = GoSoapGenerator(soap_service).generate()
        wsdl_file = next(k for k in files if k.endswith(".wsdl"))
        ET.fromstring(files[wsdl_file])

    def test_namespace_in_wsdl(self, soap_service):
        files = GoSoapGenerator(soap_service).generate()
        wsdl_file = next(k for k in files if k.endswith(".wsdl"))
        assert soap_service.namespace in files[wsdl_file]

    def test_minimal_service_has_go_mod_and_main(self, minimal_service):
        files = GoSoapGenerator(minimal_service).generate()
        assert "go.mod" in files
        assert "main.go" in files
