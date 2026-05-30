"""Integration tests for the /api/database/* endpoints (mocked pyodbc)."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def _make_mock_conn(tables=None, columns=None):
    """Build a mock pyodbc connection that returns test data."""
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor

    if tables is not None:
        cursor.fetchall.return_value = tables

    if columns is not None:
        cursor.fetchall.side_effect = [columns]

    return conn


SAMPLE_TABLES = [
    ("dbo", "Product", "dbo.Product"),
    ("dbo", "Order",   "dbo.Order"),
]

SAMPLE_COLUMNS = [
    ("Id",    "int",      "NO",  None, 1),
    ("Name",  "nvarchar", "NO",  100,  0),
    ("Price", "decimal",  "YES", None, 0),
]

CONNECT_PAYLOAD = {
    "server": "localhost",
    "database": "TestDB",
    "username": "sa",
    "password": "pass",
    "auth_type": "sql",
}


# ── /api/database/connect ─────────────────────────────────────────────────────

class TestDatabaseConnect:
    def test_returns_table_list(self):
        with patch("db_connector.get_connection") as mock_get_conn, \
             patch("db_connector.get_tables") as mock_get_tables:
            mock_get_conn.return_value = MagicMock()
            mock_get_tables.return_value = [
                {"schema": "dbo", "table_name": "Product", "full_name": "dbo.Product"},
                {"schema": "dbo", "table_name": "Order",   "full_name": "dbo.Order"},
            ]
            res = client.post("/api/database/connect", json=CONNECT_PAYLOAD)

        assert res.status_code == 200
        data = res.json()
        assert "tables" in data
        assert len(data["tables"]) == 2
        assert data["tables"][0]["full_name"] == "dbo.Product"

    def test_connection_failure_returns_400(self):
        with patch("db_connector.get_connection") as mock_get_conn:
            mock_get_conn.side_effect = Exception("Login failed")
            res = client.post("/api/database/connect", json=CONNECT_PAYLOAD)

        assert res.status_code == 400
        assert "Login failed" in res.json()["detail"]

    def test_windows_auth_payload(self):
        payload = {**CONNECT_PAYLOAD, "auth_type": "windows", "username": None, "password": None}
        with patch("db_connector.get_connection") as mock_get_conn, \
             patch("db_connector.get_tables") as mock_get_tables:
            mock_get_conn.return_value = MagicMock()
            mock_get_tables.return_value = []
            res = client.post("/api/database/connect", json=payload)

        assert res.status_code == 200
        # Verify windows auth_type was forwarded
        call_args = mock_get_conn.call_args
        assert call_args.args[5] == "windows"


# ── /api/database/schema ──────────────────────────────────────────────────────

class TestDatabaseSchema:
    def test_returns_schema_for_selected_tables(self):
        cols = [
            {"name": "Id",    "sql_type": "int",      "service_type": "integer",
             "is_nullable": False, "max_length": None, "is_primary_key": True},
            {"name": "Name",  "sql_type": "nvarchar",  "service_type": "string",
             "is_nullable": False, "max_length": 100,  "is_primary_key": False},
        ]
        payload = {**CONNECT_PAYLOAD, "tables": ["dbo.Product"]}

        with patch("db_connector.get_connection") as mock_get_conn, \
             patch("db_connector.get_columns") as mock_get_cols:
            mock_get_conn.return_value = MagicMock()
            mock_get_cols.return_value = cols
            res = client.post("/api/database/schema", json=payload)

        assert res.status_code == 200
        data = res.json()
        assert "schema" in data
        assert "dbo.Product" in data["schema"]
        assert len(data["schema"]["dbo.Product"]) == 2

    def test_multiple_tables(self):
        payload = {**CONNECT_PAYLOAD, "tables": ["dbo.Product", "dbo.Order"]}
        with patch("db_connector.get_connection") as mock_get_conn, \
             patch("db_connector.get_columns") as mock_get_cols:
            mock_get_conn.return_value = MagicMock()
            mock_get_cols.return_value = []
            res = client.post("/api/database/schema", json=payload)

        assert res.status_code == 200
        assert mock_get_cols.call_count == 2


# ── /api/database/generate-service ───────────────────────────────────────────

class TestDatabaseGenerateService:
    COLS = [
        {"name": "Id",    "sql_type": "int",     "service_type": "integer",
         "is_nullable": False, "max_length": None, "is_primary_key": True},
        {"name": "Title", "sql_type": "nvarchar", "service_type": "string",
         "is_nullable": False, "max_length": 200,  "is_primary_key": False},
    ]

    PAYLOAD = {
        **CONNECT_PAYLOAD,
        "tables": ["dbo.Book"],
        "operations": {"dbo.Book": ["getAll", "getById", "create", "update", "delete"]},
        "service_name": "BookService",
        "service_type": "REST",
    }

    def test_returns_service_definition(self):
        with patch("db_connector.get_connection") as mock_get_conn, \
             patch("db_connector.get_columns") as mock_get_cols:
            mock_get_conn.return_value = MagicMock()
            mock_get_cols.return_value = self.COLS
            res = client.post("/api/database/generate-service", json=self.PAYLOAD)

        assert res.status_code == 200
        data = res.json()
        assert data["service_name"] == "BookService"
        assert data["service_type"] == "REST"

    def test_has_correct_methods(self):
        with patch("db_connector.get_connection") as mock_get_conn, \
             patch("db_connector.get_columns") as mock_get_cols:
            mock_get_conn.return_value = MagicMock()
            mock_get_cols.return_value = self.COLS
            res = client.post("/api/database/generate-service", json=self.PAYLOAD)

        data = res.json()
        method_names = [m["name"] for m in data["methods"]]
        assert "getAllBook" in method_names
        assert "getBookById" in method_names
        assert "createBook" in method_names
        assert "updateBook" in method_names
        assert "deleteBook" in method_names

    def test_has_model(self):
        with patch("db_connector.get_connection") as mock_get_conn, \
             patch("db_connector.get_columns") as mock_get_cols:
            mock_get_conn.return_value = MagicMock()
            mock_get_cols.return_value = self.COLS
            res = client.post("/api/database/generate-service", json=self.PAYLOAD)

        data = res.json()
        assert any(m["name"] == "Book" for m in data["models"])

    def test_selective_operations(self):
        payload = {**self.PAYLOAD, "operations": {"dbo.Book": ["getAll"]}}
        with patch("db_connector.get_connection") as mock_get_conn, \
             patch("db_connector.get_columns") as mock_get_cols:
            mock_get_conn.return_value = MagicMock()
            mock_get_cols.return_value = self.COLS
            res = client.post("/api/database/generate-service", json=payload)

        data = res.json()
        assert len(data["methods"]) == 1
        assert data["methods"][0]["name"] == "getAllBook"

    def test_soap_service_type(self):
        payload = {**self.PAYLOAD, "service_type": "SOAP"}
        with patch("db_connector.get_connection") as mock_get_conn, \
             patch("db_connector.get_columns") as mock_get_cols:
            mock_get_conn.return_value = MagicMock()
            mock_get_cols.return_value = self.COLS
            res = client.post("/api/database/generate-service", json=payload)

        data = res.json()
        assert data["service_type"] == "SOAP"

    def test_connection_error_returns_400(self):
        with patch("db_connector.get_connection") as mock_get_conn:
            mock_get_conn.side_effect = Exception("Connection refused")
            res = client.post("/api/database/generate-service", json=self.PAYLOAD)

        assert res.status_code == 400


# ── db_connector.map_sql_type ─────────────────────────────────────────────────

class TestMapSqlType:
    def test_integer_types(self):
        from db_connector import map_sql_type
        for t in ("int", "bigint", "smallint", "tinyint"):
            assert map_sql_type(t) == "integer", f"Failed for {t}"

    def test_float_types(self):
        from db_connector import map_sql_type
        for t in ("float", "decimal", "numeric", "money"):
            assert map_sql_type(t) == "float", f"Failed for {t}"

    def test_string_types(self):
        from db_connector import map_sql_type
        for t in ("varchar", "nvarchar", "char", "nchar", "text", "xml"):
            assert map_sql_type(t) == "string", f"Failed for {t}"

    def test_boolean(self):
        from db_connector import map_sql_type
        assert map_sql_type("bit") == "boolean"

    def test_datetime_as_string(self):
        from db_connector import map_sql_type
        for t in ("datetime", "datetime2", "date", "time"):
            assert map_sql_type(t) == "string", f"Failed for {t}"

    def test_unknown_defaults_to_string(self):
        from db_connector import map_sql_type
        assert map_sql_type("geometry") == "string"

    def test_case_insensitive(self):
        from db_connector import map_sql_type
        assert map_sql_type("INT") == "integer"
        assert map_sql_type("NVarChar") == "string"
