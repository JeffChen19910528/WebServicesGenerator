"""Tests for Pydantic models in models.py."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from pydantic import ValidationError

from models import (
    ServiceDefinition,
    ServiceType,
    Method,
    Parameter,
    ModelDef,
    Field,
    ParameterLocation,
    GenerateRequest,
    GenerateTestsRequest,
)


# ---------------------------------------------------------------------------
# ServiceType enum
# ---------------------------------------------------------------------------


class TestServiceTypeEnum:
    def test_soap_value(self):
        assert ServiceType.SOAP == "SOAP"

    def test_rest_value(self):
        assert ServiceType.REST == "REST"

    def test_both_value(self):
        assert ServiceType.BOTH == "BOTH"

    def test_enum_members_count(self):
        assert len(ServiceType) == 3

    def test_invalid_service_type_raises(self):
        with pytest.raises(ValidationError):
            ServiceDefinition(
                service_name="BadService",
                service_type="INVALID",
                namespace="http://example.com",
            )


# ---------------------------------------------------------------------------
# ParameterLocation enum
# ---------------------------------------------------------------------------


class TestParameterLocationEnum:
    def test_query_value(self):
        assert ParameterLocation.QUERY == "query"

    def test_path_value(self):
        assert ParameterLocation.PATH == "path"

    def test_body_value(self):
        assert ParameterLocation.BODY == "body"

    def test_header_value(self):
        assert ParameterLocation.HEADER == "header"


# ---------------------------------------------------------------------------
# Parameter model
# ---------------------------------------------------------------------------


class TestParameterModel:
    def test_required_defaults_to_true(self):
        p = Parameter(name="id", type="int")
        assert p.required is True

    def test_location_defaults_to_query(self):
        p = Parameter(name="q", type="string")
        assert p.location == ParameterLocation.QUERY

    def test_explicit_location(self):
        p = Parameter(name="body_param", type="string", location=ParameterLocation.BODY)
        assert p.location == ParameterLocation.BODY

    def test_optional_required(self):
        p = Parameter(name="opt", type="boolean", required=False)
        assert p.required is False

    def test_name_and_type_stored(self):
        p = Parameter(name="userId", type="int")
        assert p.name == "userId"
        assert p.type == "int"

    def test_description_optional(self):
        p = Parameter(name="x", type="string")
        assert p.description is None

    def test_description_set(self):
        p = Parameter(name="x", type="string", description="A description")
        assert p.description == "A description"

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            Parameter(type="int")

    def test_missing_type_raises(self):
        with pytest.raises(ValidationError):
            Parameter(name="x")


# ---------------------------------------------------------------------------
# Method model
# ---------------------------------------------------------------------------


class TestMethodModel:
    def test_default_http_method(self):
        m = Method(name="doSomething")
        assert m.http_method == "GET"

    def test_default_path(self):
        m = Method(name="doSomething")
        assert m.path == "/"

    def test_default_return_type(self):
        m = Method(name="doSomething")
        assert m.return_type == "void"

    def test_default_parameters_empty_list(self):
        m = Method(name="doSomething")
        assert m.parameters == []

    def test_custom_http_method(self):
        m = Method(name="create", http_method="POST")
        assert m.http_method == "POST"

    def test_custom_path(self):
        m = Method(name="getById", path="/items/{id}")
        assert m.path == "/items/{id}"

    def test_custom_return_type(self):
        m = Method(name="getUser", return_type="User")
        assert m.return_type == "User"

    def test_parameters_stored(self):
        p = Parameter(name="id", type="int")
        m = Method(name="get", parameters=[p])
        assert len(m.parameters) == 1
        assert m.parameters[0].name == "id"

    def test_description_optional(self):
        m = Method(name="x")
        assert m.description is None

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            Method(http_method="GET")


# ---------------------------------------------------------------------------
# Field model
# ---------------------------------------------------------------------------


class TestFieldModel:
    def test_required_defaults_to_true(self):
        f = Field(name="id", type="int")
        assert f.required is True

    def test_name_and_type_stored(self):
        f = Field(name="email", type="string")
        assert f.name == "email"
        assert f.type == "string"

    def test_optional_field(self):
        f = Field(name="nickname", type="string", required=False)
        assert f.required is False

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            Field(type="string")

    def test_missing_type_raises(self):
        with pytest.raises(ValidationError):
            Field(name="x")


# ---------------------------------------------------------------------------
# ModelDef model
# ---------------------------------------------------------------------------


class TestModelDefModel:
    def test_fields_default_empty(self):
        m = ModelDef(name="EmptyModel")
        assert m.fields == []

    def test_name_stored(self):
        m = ModelDef(name="User")
        assert m.name == "User"

    def test_fields_stored(self):
        f = Field(name="id", type="int")
        m = ModelDef(name="Thing", fields=[f])
        assert len(m.fields) == 1
        assert m.fields[0].name == "id"

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            ModelDef()


# ---------------------------------------------------------------------------
# ServiceDefinition model
# ---------------------------------------------------------------------------


class TestServiceDefinitionModel:
    def test_requires_service_name(self):
        with pytest.raises(ValidationError):
            ServiceDefinition(service_type=ServiceType.REST)

    def test_requires_service_type(self):
        with pytest.raises(ValidationError):
            ServiceDefinition(service_name="Svc")

    def test_namespace_default(self):
        svc = ServiceDefinition(service_name="Svc", service_type=ServiceType.REST)
        assert svc.namespace == "http://example.com/service"

    def test_version_default(self):
        svc = ServiceDefinition(service_name="Svc", service_type=ServiceType.REST)
        assert svc.version == "1.0"

    def test_methods_default_empty(self):
        svc = ServiceDefinition(service_name="Svc", service_type=ServiceType.REST)
        assert svc.methods == []

    def test_models_default_empty(self):
        svc = ServiceDefinition(service_name="Svc", service_type=ServiceType.REST)
        assert svc.models == []

    def test_description_optional(self):
        svc = ServiceDefinition(service_name="Svc", service_type=ServiceType.REST)
        assert svc.description is None

    def test_service_name_with_spaces(self):
        svc = ServiceDefinition(
            service_name="My Service Name",
            service_type=ServiceType.REST,
        )
        assert svc.service_name == "My Service Name"

    def test_service_name_with_hyphens(self):
        svc = ServiceDefinition(
            service_name="my-service-api",
            service_type=ServiceType.SOAP,
        )
        assert svc.service_name == "my-service-api"

    def test_full_construction(self):
        svc = ServiceDefinition(
            service_name="FullService",
            service_type=ServiceType.BOTH,
            namespace="http://example.com/full",
            description="Full service description",
            version="2.5",
            methods=[Method(name="ping")],
            models=[ModelDef(name="PingResult")],
        )
        assert svc.service_name == "FullService"
        assert svc.service_type == ServiceType.BOTH
        assert svc.namespace == "http://example.com/full"
        assert svc.description == "Full service description"
        assert svc.version == "2.5"
        assert len(svc.methods) == 1
        assert len(svc.models) == 1

    def test_soap_service_type(self):
        svc = ServiceDefinition(
            service_name="Svc", service_type=ServiceType.SOAP
        )
        assert svc.service_type == ServiceType.SOAP

    def test_rest_service_type(self):
        svc = ServiceDefinition(
            service_name="Svc", service_type=ServiceType.REST
        )
        assert svc.service_type == ServiceType.REST

    def test_both_service_type(self):
        svc = ServiceDefinition(
            service_name="Svc", service_type=ServiceType.BOTH
        )
        assert svc.service_type == ServiceType.BOTH


# ---------------------------------------------------------------------------
# GenerateRequest model
# ---------------------------------------------------------------------------


class TestGenerateRequestModel:
    def test_requires_service_and_framework(self):
        with pytest.raises(ValidationError):
            GenerateRequest(framework="rest-python-fastapi")

    def test_valid_construction(self):
        svc = ServiceDefinition(service_name="Svc", service_type=ServiceType.REST)
        req = GenerateRequest(service=svc, framework="rest-python-fastapi")
        assert req.framework == "rest-python-fastapi"
        assert req.service.service_name == "Svc"


# ---------------------------------------------------------------------------
# GenerateTestsRequest model
# ---------------------------------------------------------------------------


class TestGenerateTestsRequestModel:
    def test_requires_service_and_test_types(self):
        with pytest.raises(ValidationError):
            GenerateTestsRequest(test_types=["postman"])

    def test_valid_construction(self):
        svc = ServiceDefinition(service_name="Svc", service_type=ServiceType.REST)
        req = GenerateTestsRequest(service=svc, test_types=["postman", "soapui"])
        assert "postman" in req.test_types
        assert "soapui" in req.test_types

    def test_empty_test_types_allowed_by_model(self):
        """The model itself allows empty list; enforcement is done in the API layer."""
        svc = ServiceDefinition(service_name="Svc", service_type=ServiceType.REST)
        req = GenerateTestsRequest(service=svc, test_types=[])
        assert req.test_types == []
