"""Tests for the three test-artifact generators (soap_xml, soapui, postman)."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
import xml.etree.ElementTree as ET

import pytest

from test_generators.soap_xml import generate_soap_xml
from test_generators.soapui_project import generate_soapui_project
from test_generators.postman_collection import generate_postman_collection


# ===========================================================================
# generate_soap_xml
# ===========================================================================


class TestGenerateSoapXml:
    def test_generates_files(self, soap_service):
        files = generate_soap_xml(soap_service)
        assert isinstance(files, dict)
        assert len(files) > 0

    def test_has_files_per_method_soap11_and_soap12(self, soap_service):
        """Each method produces 2 files: SOAP 1.1 and SOAP 1.2."""
        files = generate_soap_xml(soap_service)
        expected = len(soap_service.methods) * 2
        assert len(files) == expected, (
            f"Expected {expected} files for {len(soap_service.methods)} methods, got {len(files)}"
        )

    def test_files_are_valid_xml(self, soap_service):
        files = generate_soap_xml(soap_service)
        for path, content in files.items():
            try:
                ET.fromstring(content)
            except ET.ParseError as exc:
                pytest.fail(f"File '{path}' is not valid XML: {exc}")

    def test_namespace_appears_in_xml(self, soap_service):
        files = generate_soap_xml(soap_service)
        for path, content in files.items():
            assert soap_service.namespace in content, (
                f"Namespace not found in '{path}'"
            )

    def test_method_names_appear_in_xml(self, soap_service):
        files = generate_soap_xml(soap_service)
        for method in soap_service.methods:
            method_found = any(method.name in content for content in files.values())
            assert method_found, f"Method name '{method.name}' not found in any soap_xml file"

    def test_param_names_appear_in_xml(self, soap_service):
        files = generate_soap_xml(soap_service)
        all_content = "\n".join(files.values())
        for method in soap_service.methods:
            for param in method.parameters:
                assert param.name in all_content, (
                    f"Parameter '{param.name}' not found in soap_xml output"
                )

    def test_soap11_envelope_namespace(self, soap_service):
        files = generate_soap_xml(soap_service)
        soap11_files = {k: v for k, v in files.items() if not k.endswith("_SOAP12.xml")}
        for path, content in soap11_files.items():
            assert "http://schemas.xmlsoap.org/soap/envelope/" in content, (
                f"SOAP 1.1 namespace not found in '{path}'"
            )

    def test_soap12_envelope_namespace(self, soap_service):
        files = generate_soap_xml(soap_service)
        soap12_files = {k: v for k, v in files.items() if k.endswith("_SOAP12.xml")}
        assert len(soap12_files) > 0, "No SOAP 1.2 files generated"
        for path, content in soap12_files.items():
            assert "http://www.w3.org/2003/05/soap-envelope" in content, (
                f"SOAP 1.2 namespace not found in '{path}'"
            )

    def test_soap12_files_have_action_element(self, soap_service):
        files = generate_soap_xml(soap_service)
        soap12_files = {k: v for k, v in files.items() if k.endswith("_SOAP12.xml")}
        for path, content in soap12_files.items():
            assert "Action" in content or "action" in content, (
                f"No Action element in SOAP 1.2 file '{path}'"
            )

    def test_file_paths_under_soap_xml_dir(self, soap_service):
        files = generate_soap_xml(soap_service)
        for path in files:
            assert path.startswith("soap_xml/"), (
                f"File path '{path}' does not start with 'soap_xml/'"
            )

    def test_minimal_service_returns_empty_or_valid(self, minimal_service):
        """No methods means no files — should not raise."""
        files = generate_soap_xml(minimal_service)
        assert isinstance(files, dict)
        # For each file that IS produced, it must be valid XML
        for path, content in files.items():
            ET.fromstring(content)

    def test_rest_service_generates_soap_xml(self, rest_service):
        """soap_xml generator works with any service type."""
        files = generate_soap_xml(rest_service)
        assert len(files) == len(rest_service.methods) * 2

    def test_files_have_content(self, soap_service):
        files = generate_soap_xml(soap_service)
        for path, content in files.items():
            assert content.strip(), f"File '{path}' is empty"


# ===========================================================================
# generate_soapui_project
# ===========================================================================


class TestGenerateSoapuiProject:
    def test_generates_one_file(self, soap_service):
        files = generate_soapui_project(soap_service)
        assert len(files) == 1

    def test_file_path_under_soapui_dir(self, soap_service):
        files = generate_soapui_project(soap_service)
        path = list(files.keys())[0]
        assert path.startswith("soapui/"), f"File '{path}' not under soapui/"

    def test_file_is_valid_xml(self, soap_service):
        files = generate_soapui_project(soap_service)
        content = list(files.values())[0]
        ET.fromstring(content)

    def test_file_content_not_empty(self, soap_service):
        files = generate_soapui_project(soap_service)
        content = list(files.values())[0]
        assert content.strip()

    def test_contains_method_operations(self, soap_service):
        files = generate_soapui_project(soap_service)
        content = list(files.values())[0]
        for method in soap_service.methods:
            assert method.name in content, (
                f"Method '{method.name}' not in soapui project"
            )

    def test_has_test_suite_element(self, soap_service):
        files = generate_soapui_project(soap_service)
        content = list(files.values())[0]
        assert "testSuite" in content or "TestSuite" in content, (
            "No testSuite element found in SoapUI project"
        )

    def test_soap_service_produces_soap_project(self, soap_service):
        files = generate_soapui_project(soap_service)
        content = list(files.values())[0]
        assert "wsdl" in content.lower() or "soap" in content.lower()

    def test_rest_service_produces_rest_project(self, rest_service):
        files = generate_soapui_project(rest_service)
        content = list(files.values())[0]
        assert 'type="rest"' in content

    def test_both_service_produces_soap_project(self, both_service):
        files = generate_soapui_project(both_service)
        content = list(files.values())[0]
        # BOTH should use the SOAP project path
        assert "wsdl" in content.lower() or 'type="wsdl"' in content

    def test_service_name_in_project(self, soap_service):
        files = generate_soapui_project(soap_service)
        content = list(files.values())[0]
        assert soap_service.service_name in content

    def test_project_has_soapui_version(self, soap_service):
        files = generate_soapui_project(soap_service)
        content = list(files.values())[0]
        assert "soapui-version" in content

    def test_test_cases_for_each_method(self, soap_service):
        files = generate_soapui_project(soap_service)
        content = list(files.values())[0]
        for method in soap_service.methods:
            assert method.name in content

    def test_minimal_service_ok(self, minimal_service):
        """Empty methods service should produce a valid XML file without crashing."""
        files = generate_soapui_project(minimal_service)
        assert len(files) == 1
        content = list(files.values())[0]
        ET.fromstring(content)

    def test_filename_contains_service_name(self, soap_service):
        files = generate_soapui_project(soap_service)
        path = list(files.keys())[0]
        assert soap_service.service_name in path


# ===========================================================================
# generate_postman_collection
# ===========================================================================


class TestGeneratePostmanCollection:
    def test_generates_two_files(self, rest_service):
        """Should produce collection file + environment file."""
        files = generate_postman_collection(rest_service)
        assert len(files) == 2

    def test_file_paths_under_postman_dir(self, rest_service):
        files = generate_postman_collection(rest_service)
        for path in files:
            assert path.startswith("postman/"), f"File '{path}' not under postman/"

    def test_collection_is_valid_json(self, rest_service):
        files = generate_postman_collection(rest_service)
        collection_path = next(k for k in files if "collection" in k)
        json.loads(files[collection_path])  # raises if invalid

    def test_environment_is_valid_json(self, rest_service):
        files = generate_postman_collection(rest_service)
        env_path = next(k for k in files if "environment" in k)
        json.loads(files[env_path])

    def test_collection_schema_version(self, rest_service):
        files = generate_postman_collection(rest_service)
        collection_path = next(k for k in files if "collection" in k)
        data = json.loads(files[collection_path])
        schema = data["info"]["schema"]
        assert "v2.1.0" in schema, f"Expected v2.1.0 schema, got '{schema}'"

    def test_collection_has_items(self, rest_service):
        files = generate_postman_collection(rest_service)
        collection_path = next(k for k in files if "collection" in k)
        data = json.loads(files[collection_path])
        assert "item" in data
        assert len(data["item"]) > 0

    def test_item_count_at_least_method_count(self, rest_service):
        files = generate_postman_collection(rest_service)
        collection_path = next(k for k in files if "collection" in k)
        data = json.loads(files[collection_path])
        assert len(data["item"]) >= len(rest_service.methods)

    def test_environment_has_base_url(self, rest_service):
        files = generate_postman_collection(rest_service)
        env_path = next(k for k in files if "environment" in k)
        data = json.loads(files[env_path])
        values = data.get("values", [])
        keys = [v["key"] for v in values]
        assert "base_url" in keys, "base_url variable not found in environment"

    def test_method_names_in_item_names(self, rest_service):
        files = generate_postman_collection(rest_service)
        collection_path = next(k for k in files if "collection" in k)
        data = json.loads(files[collection_path])
        item_names = [item["name"] for item in data["item"]]
        for method in rest_service.methods:
            assert any(method.name in name for name in item_names), (
                f"Method '{method.name}' not found in any item name"
            )

    def test_collection_info_has_name(self, rest_service):
        files = generate_postman_collection(rest_service)
        collection_path = next(k for k in files if "collection" in k)
        data = json.loads(files[collection_path])
        assert "name" in data["info"]
        assert data["info"]["name"] == rest_service.service_name

    def test_each_rest_item_has_request(self, rest_service):
        files = generate_postman_collection(rest_service)
        collection_path = next(k for k in files if "collection" in k)
        data = json.loads(files[collection_path])
        for item in data["item"]:
            assert "request" in item, f"Item '{item.get('name')}' has no request"

    def test_each_rest_item_has_correct_http_method(self, rest_service):
        files = generate_postman_collection(rest_service)
        collection_path = next(k for k in files if "collection" in k)
        data = json.loads(files[collection_path])
        # Build a map: item name -> http method in collection
        item_map = {item["name"]: item["request"]["method"] for item in data["item"]}
        for method in rest_service.methods:
            assert method.name in item_map
            assert item_map[method.name] == method.http_method.upper()

    def test_soap_service_items_use_post(self, soap_service):
        """SOAP Postman items are always POST."""
        files = generate_postman_collection(soap_service)
        collection_path = next(k for k in files if "collection" in k)
        data = json.loads(files[collection_path])
        for item in data["item"]:
            assert item["request"]["method"] == "POST"

    def test_soap_service_items_have_xml_content_type(self, soap_service):
        files = generate_postman_collection(soap_service)
        collection_path = next(k for k in files if "collection" in k)
        data = json.loads(files[collection_path])
        for item in data["item"]:
            headers = {h["key"]: h["value"] for h in item["request"]["header"]}
            assert "Content-Type" in headers
            assert "xml" in headers["Content-Type"].lower()

    def test_both_service_has_soap_and_rest_folders(self, both_service):
        files = generate_postman_collection(both_service)
        collection_path = next(k for k in files if "collection" in k)
        data = json.loads(files[collection_path])
        folder_names = [item["name"] for item in data["item"]]
        assert "SOAP Requests" in folder_names
        assert "REST Requests" in folder_names

    def test_collection_has_base_url_variable(self, rest_service):
        files = generate_postman_collection(rest_service)
        collection_path = next(k for k in files if "collection" in k)
        data = json.loads(files[collection_path])
        variables = data.get("variable", [])
        var_keys = [v["key"] for v in variables]
        assert "base_url" in var_keys

    def test_minimal_service_ok(self, minimal_service):
        """No methods should produce a valid collection with empty items."""
        files = generate_postman_collection(minimal_service)
        assert len(files) == 2
        collection_path = next(k for k in files if "collection" in k)
        data = json.loads(files[collection_path])
        assert "item" in data
        # Empty service means zero items (or a folder with zero items)
        assert isinstance(data["item"], list)

    def test_environment_has_localhost_base_url(self, rest_service):
        files = generate_postman_collection(rest_service)
        env_path = next(k for k in files if "environment" in k)
        data = json.loads(files[env_path])
        values = {v["key"]: v["value"] for v in data.get("values", [])}
        assert "localhost" in values.get("base_url", "")

    def test_postman_collection_files_have_correct_extensions(self, rest_service):
        files = generate_postman_collection(rest_service)
        for path in files:
            assert path.endswith(".json"), f"Expected .json extension, got: '{path}'"
