"""Unit tests for db_to_service.py – no database connection required."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from db_to_service import to_pascal_case, to_camel_case, find_pk, build_service_from_schema
from models import ServiceType


# ── helpers ──────────────────────────────────────────────────────────────────

class TestToPascalCase:
    def test_simple(self):
        assert to_pascal_case("user") == "User"

    def test_underscore(self):
        assert to_pascal_case("order_item") == "OrderItem"

    def test_schema_prefix_stripped(self):
        assert to_pascal_case("dbo.Product") == "Product"

    def test_already_pascal(self):
        assert to_pascal_case("CustomerOrder") == "Customerorder"

    def test_multiple_underscores(self):
        assert to_pascal_case("some_long_table_name") == "SomeLongTableName"


class TestToCamelCase:
    def test_simple(self):
        assert to_camel_case("User") == "user"

    def test_underscore(self):
        assert to_camel_case("order_item") == "orderItem"

    def test_schema_prefix(self):
        assert to_camel_case("dbo.Product") == "product"


# ── find_pk ───────────────────────────────────────────────────────────────────

SAMPLE_COLS = [
    {"name": "Id", "sql_type": "int", "service_type": "integer",
     "is_nullable": False, "is_primary_key": True},
    {"name": "Name", "sql_type": "nvarchar", "service_type": "string",
     "is_nullable": False, "is_primary_key": False},
    {"name": "Price", "sql_type": "decimal", "service_type": "float",
     "is_nullable": True, "is_primary_key": False},
]

NO_PK_COLS = [
    {"name": "Code", "sql_type": "varchar", "service_type": "string",
     "is_nullable": False, "is_primary_key": False},
    {"name": "id", "sql_type": "int", "service_type": "integer",
     "is_nullable": False, "is_primary_key": False},
]


class TestFindPk:
    def test_finds_explicit_pk(self):
        pk = find_pk(SAMPLE_COLS)
        assert pk["name"] == "Id"
        assert pk["service_type"] == "integer"

    def test_falls_back_to_id_column(self):
        pk = find_pk(NO_PK_COLS)
        assert pk["name"] == "id"

    def test_falls_back_to_first_column(self):
        cols = [{"name": "Code", "sql_type": "varchar", "service_type": "string",
                 "is_nullable": False, "is_primary_key": False}]
        pk = find_pk(cols)
        assert pk["name"] == "Code"


# ── build_service_from_schema ─────────────────────────────────────────────────

SCHEMA = {
    "dbo.Product": SAMPLE_COLS,
}

ALL_OPS = ["getAll", "getById", "create", "update", "delete"]


class TestBuildServiceFromSchema:
    def test_returns_service_definition(self):
        svc = build_service_from_schema(
            schema=SCHEMA,
            operations={"dbo.Product": ALL_OPS},
            service_name="ProductService",
            service_type="REST",
        )
        assert svc.service_name == "ProductService"
        assert svc.service_type == ServiceType.REST

    def test_generates_models(self):
        svc = build_service_from_schema(
            schema=SCHEMA,
            operations={"dbo.Product": ALL_OPS},
            service_name="S",
            service_type="REST",
        )
        assert len(svc.models) == 1
        assert svc.models[0].name == "Product"
        field_names = [f.name for f in svc.models[0].fields]
        assert "Id" in field_names
        assert "Name" in field_names
        assert "Price" in field_names

    def test_generates_all_five_methods(self):
        svc = build_service_from_schema(
            schema=SCHEMA,
            operations={"dbo.Product": ALL_OPS},
            service_name="S",
            service_type="REST",
        )
        method_names = [m.name for m in svc.methods]
        assert "getAllProduct" in method_names
        assert "getProductById" in method_names
        assert "createProduct" in method_names
        assert "updateProduct" in method_names
        assert "deleteProduct" in method_names

    def test_selective_ops(self):
        svc = build_service_from_schema(
            schema=SCHEMA,
            operations={"dbo.Product": ["getAll", "create"]},
            service_name="S",
            service_type="REST",
        )
        method_names = [m.name for m in svc.methods]
        assert "getAllProduct" in method_names
        assert "createProduct" in method_names
        assert "deleteProduct" not in method_names
        assert "getProductById" not in method_names

    def test_http_methods_correct(self):
        svc = build_service_from_schema(
            schema=SCHEMA,
            operations={"dbo.Product": ALL_OPS},
            service_name="S",
            service_type="REST",
        )
        by_name = {m.name: m for m in svc.methods}
        assert by_name["getAllProduct"].http_method == "GET"
        assert by_name["getProductById"].http_method == "GET"
        assert by_name["createProduct"].http_method == "POST"
        assert by_name["updateProduct"].http_method == "PUT"
        assert by_name["deleteProduct"].http_method == "DELETE"

    def test_paths_correct(self):
        svc = build_service_from_schema(
            schema=SCHEMA,
            operations={"dbo.Product": ALL_OPS},
            service_name="S",
            service_type="REST",
        )
        by_name = {m.name: m for m in svc.methods}
        assert by_name["getAllProduct"].path == "/product"
        assert by_name["getProductById"].path == "/product/{Id}"
        assert by_name["createProduct"].path == "/product"
        assert by_name["updateProduct"].path == "/product/{Id}"
        assert by_name["deleteProduct"].path == "/product/{Id}"

    def test_getById_has_path_param(self):
        svc = build_service_from_schema(
            schema=SCHEMA,
            operations={"dbo.Product": ["getById"]},
            service_name="S",
            service_type="REST",
        )
        m = svc.methods[0]
        assert len(m.parameters) == 1
        assert m.parameters[0].name == "Id"
        assert m.parameters[0].location.value == "path"

    def test_create_has_body_param(self):
        svc = build_service_from_schema(
            schema=SCHEMA,
            operations={"dbo.Product": ["create"]},
            service_name="S",
            service_type="REST",
        )
        m = svc.methods[0]
        assert len(m.parameters) == 1
        assert m.parameters[0].location.value == "body"
        assert m.parameters[0].type == "Product"

    def test_update_has_two_params(self):
        svc = build_service_from_schema(
            schema=SCHEMA,
            operations={"dbo.Product": ["update"]},
            service_name="S",
            service_type="REST",
        )
        m = svc.methods[0]
        assert len(m.parameters) == 2
        locations = {p.location.value for p in m.parameters}
        assert "path" in locations
        assert "body" in locations

    def test_soap_service_type(self):
        svc = build_service_from_schema(
            schema=SCHEMA,
            operations={"dbo.Product": ["getAll"]},
            service_name="S",
            service_type="SOAP",
        )
        assert svc.service_type == ServiceType.SOAP

    def test_multiple_tables(self):
        schema = {
            "dbo.Product": SAMPLE_COLS,
            "dbo.Order": [
                {"name": "OrderId", "sql_type": "int", "service_type": "integer",
                 "is_nullable": False, "is_primary_key": True},
                {"name": "Total", "sql_type": "decimal", "service_type": "float",
                 "is_nullable": False, "is_primary_key": False},
            ],
        }
        svc = build_service_from_schema(
            schema=schema,
            operations={
                "dbo.Product": ["getAll"],
                "dbo.Order": ["getAll", "getById"],
            },
            service_name="S",
            service_type="REST",
        )
        assert len(svc.models) == 2
        model_names = {m.name for m in svc.models}
        assert "Product" in model_names
        assert "Order" in model_names
        assert len(svc.methods) == 3  # 1 + 2

    def test_empty_ops(self):
        svc = build_service_from_schema(
            schema=SCHEMA,
            operations={"dbo.Product": []},
            service_name="S",
            service_type="REST",
        )
        assert len(svc.methods) == 0
        assert len(svc.models) == 1

    def test_nullable_fields_not_required(self):
        svc = build_service_from_schema(
            schema=SCHEMA,
            operations={"dbo.Product": []},
            service_name="S",
            service_type="REST",
        )
        field_map = {f.name: f for f in svc.models[0].fields}
        assert field_map["Price"].required is False
        assert field_map["Name"].required is True
