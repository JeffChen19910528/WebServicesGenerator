"""Tests for FastAPI endpoints in main.py."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import io
import json
import zipfile

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

# ---------------------------------------------------------------------------
# Shared request payloads
# ---------------------------------------------------------------------------

SOAP_SERVICE_PAYLOAD = {
    "service": {
        "service_name": "OrderService",
        "service_type": "SOAP",
        "namespace": "http://example.com/orders",
        "version": "1.0",
        "methods": [
            {
                "name": "getOrder",
                "http_method": "GET",
                "path": "/orders/{orderId}",
                "return_type": "Order",
                "parameters": [
                    {"name": "orderId", "type": "int", "required": True, "location": "path"}
                ],
            }
        ],
        "models": [
            {
                "name": "Order",
                "fields": [
                    {"name": "id", "type": "int"},
                    {"name": "product", "type": "string"},
                ],
            }
        ],
    },
    "framework": "soap-java-spring-ws",
}

REST_SERVICE_PAYLOAD = {
    "service": {
        "service_name": "UserService",
        "service_type": "REST",
        "namespace": "http://example.com/users",
        "version": "1.0",
        "methods": [
            {
                "name": "getUser",
                "http_method": "GET",
                "path": "/users/{userId}",
                "return_type": "User",
                "parameters": [
                    {"name": "userId", "type": "int", "required": True, "location": "path"}
                ],
            },
            {
                "name": "createUser",
                "http_method": "POST",
                "path": "/users",
                "return_type": "User",
                "parameters": [
                    {"name": "user", "type": "User", "required": True, "location": "body"}
                ],
            },
        ],
        "models": [
            {
                "name": "User",
                "fields": [
                    {"name": "id", "type": "int"},
                    {"name": "name", "type": "string"},
                ],
            }
        ],
    },
    "framework": "rest-python-fastapi",
}

# All 21 framework IDs
ALL_FRAMEWORKS = [
    "soap-java-spring-ws",
    "soap-java-cxf",
    "soap-python-spyne",
    "soap-nodejs-soap",
    "soap-csharp-wcf",
    "soap-php",
    "soap-go",
    "rest-java-spring-boot",
    "rest-python-fastapi",
    "rest-python-flask",
    "rest-python-django",
    "rest-nodejs-express",
    "rest-nodejs-nestjs",
    "rest-nodejs-fastify",
    "rest-csharp-aspnet",
    "rest-php-laravel",
    "rest-php-slim",
    "rest-go-gin",
    "rest-go-echo",
    "rest-ruby-rails",
    "rest-ruby-sinatra",
]


def _make_zip(response) -> zipfile.ZipFile:
    """Helper: parse response content as an in-memory ZipFile."""
    buf = io.BytesIO(response.content)
    return zipfile.ZipFile(buf, "r")


def _service_payload_for(framework: str) -> dict:
    """Return an appropriate generate payload for the given framework."""
    if framework.startswith("soap-"):
        payload = dict(SOAP_SERVICE_PAYLOAD)
        payload["framework"] = framework
    else:
        payload = dict(REST_SERVICE_PAYLOAD)
        payload["framework"] = framework
    return payload


# ---------------------------------------------------------------------------
# GET /api/frameworks
# ---------------------------------------------------------------------------


class TestGetFrameworks:
    def test_get_frameworks_returns_200(self):
        response = client.get("/api/frameworks")
        assert response.status_code == 200

    def test_get_frameworks_has_soap_and_rest_keys(self):
        response = client.get("/api/frameworks")
        data = response.json()
        assert "soap" in data
        assert "rest" in data

    def test_get_frameworks_soap_count(self):
        response = client.get("/api/frameworks")
        data = response.json()
        assert len(data["soap"]) == 7

    def test_get_frameworks_rest_count(self):
        response = client.get("/api/frameworks")
        data = response.json()
        assert len(data["rest"]) == 14

    def test_get_frameworks_soap_items_have_id_and_label(self):
        response = client.get("/api/frameworks")
        data = response.json()
        for item in data["soap"]:
            assert "id" in item
            assert "label" in item

    def test_get_frameworks_rest_items_have_id_and_label(self):
        response = client.get("/api/frameworks")
        data = response.json()
        for item in data["rest"]:
            assert "id" in item
            assert "label" in item

    def test_get_frameworks_soap_ids_start_with_soap_prefix(self):
        response = client.get("/api/frameworks")
        data = response.json()
        for item in data["soap"]:
            assert item["id"].startswith("soap-"), (
                f"SOAP framework ID '{item['id']}' does not start with 'soap-'"
            )

    def test_get_frameworks_rest_ids_start_with_rest_prefix(self):
        response = client.get("/api/frameworks")
        data = response.json()
        for item in data["rest"]:
            assert item["id"].startswith("rest-"), (
                f"REST framework ID '{item['id']}' does not start with 'rest-'"
            )


# ---------------------------------------------------------------------------
# POST /api/generate
# ---------------------------------------------------------------------------


class TestGenerateEndpoint:
    def test_generate_invalid_framework_returns_400(self):
        payload = dict(SOAP_SERVICE_PAYLOAD)
        payload["framework"] = "invalid-framework-xyz"
        response = client.post("/api/generate", json=payload)
        assert response.status_code == 400

    def test_generate_invalid_framework_error_message(self):
        payload = dict(SOAP_SERVICE_PAYLOAD)
        payload["framework"] = "not-a-real-framework"
        response = client.post("/api/generate", json=payload)
        assert response.status_code == 400
        detail = response.json().get("detail", "")
        assert "not-a-real-framework" in detail or "Unknown" in detail

    def test_generate_soap_java_spring_returns_200(self):
        response = client.post("/api/generate", json=SOAP_SERVICE_PAYLOAD)
        assert response.status_code == 200

    def test_generate_soap_java_spring_returns_zip_content_type(self):
        response = client.post("/api/generate", json=SOAP_SERVICE_PAYLOAD)
        assert response.status_code == 200
        assert "application/zip" in response.headers.get("content-type", "")

    def test_generate_rest_python_fastapi_returns_200(self):
        response = client.post("/api/generate", json=REST_SERVICE_PAYLOAD)
        assert response.status_code == 200

    def test_generate_rest_python_fastapi_returns_zip_content_type(self):
        response = client.post("/api/generate", json=REST_SERVICE_PAYLOAD)
        assert response.status_code == 200
        assert "application/zip" in response.headers.get("content-type", "")

    def test_generate_zip_is_valid(self):
        response = client.post("/api/generate", json=REST_SERVICE_PAYLOAD)
        assert response.status_code == 200
        zf = _make_zip(response)
        assert zf is not None

    def test_generate_zip_is_nonempty(self):
        response = client.post("/api/generate", json=REST_SERVICE_PAYLOAD)
        zf = _make_zip(response)
        assert len(zf.namelist()) > 0

    def test_generate_zip_contains_expected_main_py(self):
        """rest-python-fastapi must produce a main.py in the ZIP."""
        response = client.post("/api/generate", json=REST_SERVICE_PAYLOAD)
        zf = _make_zip(response)
        assert "main.py" in zf.namelist()

    def test_generate_zip_files_have_nonempty_content(self):
        response = client.post("/api/generate", json=REST_SERVICE_PAYLOAD)
        zf = _make_zip(response)
        for name in zf.namelist():
            content = zf.read(name)
            assert len(content) > 0, f"File '{name}' in ZIP is empty"

    def test_generate_content_disposition_header_present(self):
        response = client.post("/api/generate", json=SOAP_SERVICE_PAYLOAD)
        assert response.status_code == 200
        cd = response.headers.get("content-disposition", "")
        assert "attachment" in cd
        assert ".zip" in cd

    def test_generate_missing_service_returns_422(self):
        response = client.post("/api/generate", json={"framework": "rest-python-fastapi"})
        assert response.status_code == 422

    def test_generate_missing_framework_returns_422(self):
        response = client.post(
            "/api/generate",
            json={
                "service": {
                    "service_name": "X",
                    "service_type": "REST",
                }
            },
        )
        assert response.status_code == 422

    @pytest.mark.parametrize("framework", ALL_FRAMEWORKS)
    def test_generate_all_frameworks_succeed(self, framework):
        """Every one of the 21 framework IDs must return 200 and a valid ZIP."""
        payload = _service_payload_for(framework)
        response = client.post("/api/generate", json=payload)
        assert response.status_code == 200, (
            f"Framework '{framework}' returned {response.status_code}: {response.text[:300]}"
        )
        zf = _make_zip(response)
        assert len(zf.namelist()) > 0, (
            f"Framework '{framework}' produced an empty ZIP"
        )


# ---------------------------------------------------------------------------
# POST /api/generate-tests
# ---------------------------------------------------------------------------

TESTS_SERVICE = {
    "service_name": "OrderService",
    "service_type": "SOAP",
    "namespace": "http://example.com/orders",
    "version": "1.0",
    "methods": [
        {
            "name": "getOrder",
            "http_method": "GET",
            "path": "/orders/{orderId}",
            "return_type": "Order",
            "parameters": [
                {"name": "orderId", "type": "int", "required": True, "location": "path"}
            ],
        },
        {
            "name": "createOrder",
            "http_method": "POST",
            "path": "/orders",
            "return_type": "Order",
            "parameters": [
                {"name": "order", "type": "Order", "required": True, "location": "body"}
            ],
        },
    ],
    "models": [],
}


class TestGenerateTestsEndpoint:
    def test_generate_tests_soap_xml_returns_200(self):
        payload = {"service": TESTS_SERVICE, "test_types": ["soap-xml"]}
        response = client.post("/api/generate-tests", json=payload)
        assert response.status_code == 200

    def test_generate_tests_soap_xml_returns_zip(self):
        payload = {"service": TESTS_SERVICE, "test_types": ["soap-xml"]}
        response = client.post("/api/generate-tests", json=payload)
        zf = _make_zip(response)
        assert len(zf.namelist()) > 0

    def test_generate_tests_postman_returns_200(self):
        payload = {"service": TESTS_SERVICE, "test_types": ["postman"]}
        response = client.post("/api/generate-tests", json=payload)
        assert response.status_code == 200

    def test_generate_tests_postman_returns_zip(self):
        payload = {"service": TESTS_SERVICE, "test_types": ["postman"]}
        response = client.post("/api/generate-tests", json=payload)
        zf = _make_zip(response)
        assert len(zf.namelist()) > 0

    def test_generate_tests_soapui_returns_200(self):
        payload = {"service": TESTS_SERVICE, "test_types": ["soapui"]}
        response = client.post("/api/generate-tests", json=payload)
        assert response.status_code == 200

    def test_generate_tests_soapui_returns_zip(self):
        payload = {"service": TESTS_SERVICE, "test_types": ["soapui"]}
        response = client.post("/api/generate-tests", json=payload)
        zf = _make_zip(response)
        assert len(zf.namelist()) > 0

    def test_generate_tests_all_types_returns_200(self):
        payload = {"service": TESTS_SERVICE, "test_types": ["soap-xml", "soapui", "postman"]}
        response = client.post("/api/generate-tests", json=payload)
        assert response.status_code == 200

    def test_generate_tests_all_types_zip_has_files_from_all_generators(self):
        payload = {"service": TESTS_SERVICE, "test_types": ["soap-xml", "soapui", "postman"]}
        response = client.post("/api/generate-tests", json=payload)
        zf = _make_zip(response)
        names = zf.namelist()
        # soap-xml produces files under soap_xml/
        assert any("soap_xml" in n for n in names), "No soap_xml files in combined ZIP"
        # soapui produces files under soapui/
        assert any("soapui" in n for n in names), "No soapui files in combined ZIP"
        # postman produces files under postman/
        assert any("postman" in n for n in names), "No postman files in combined ZIP"

    def test_generate_tests_empty_types_returns_400(self):
        payload = {"service": TESTS_SERVICE, "test_types": []}
        response = client.post("/api/generate-tests", json=payload)
        assert response.status_code == 400

    def test_generate_tests_empty_types_error_detail(self):
        payload = {"service": TESTS_SERVICE, "test_types": []}
        response = client.post("/api/generate-tests", json=payload)
        assert response.status_code == 400
        detail = response.json().get("detail", "")
        assert detail  # some error message is present

    def test_generate_tests_unknown_type_treated_as_empty(self):
        """Unknown test type keys produce no files, so should return 400."""
        payload = {"service": TESTS_SERVICE, "test_types": ["not-a-type"]}
        response = client.post("/api/generate-tests", json=payload)
        assert response.status_code == 400

    def test_generate_tests_soap_xml_filenames_contain_method_names(self):
        payload = {"service": TESTS_SERVICE, "test_types": ["soap-xml"]}
        response = client.post("/api/generate-tests", json=payload)
        zf = _make_zip(response)
        names_str = " ".join(zf.namelist())
        assert "getOrder" in names_str
        assert "createOrder" in names_str

    def test_generate_tests_content_disposition_present(self):
        payload = {"service": TESTS_SERVICE, "test_types": ["postman"]}
        response = client.post("/api/generate-tests", json=payload)
        assert response.status_code == 200
        cd = response.headers.get("content-disposition", "")
        assert "attachment" in cd
