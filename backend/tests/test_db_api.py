"""Integration tests for the /api/database/* endpoints (mocked drivers)."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

SAMPLE_TABLES_MSSQL = [
    ("dbo", "Product", "dbo.Product"),
    ("dbo", "Order",   "dbo.Order"),
]

SAMPLE_COLS = [
    {"name": "Id",    "sql_type": "int",      "service_type": "integer",
     "is_nullable": False, "max_length": None, "is_primary_key": True},
    {"name": "Name",  "sql_type": "nvarchar",  "service_type": "string",
     "is_nullable": False, "max_length": 100,  "is_primary_key": False},
    {"name": "Price", "sql_type": "decimal",   "service_type": "float",
     "is_nullable": True,  "max_length": None, "is_primary_key": False},
]

MSSQL_PAYLOAD = {
    "db_type": "mssql",
    "server": "localhost",
    "database": "TestDB",
    "username": "sa",
    "password": "pass",
    "auth_type": "sql",
}

MYSQL_PAYLOAD = {
    "db_type": "mysql",
    "server": "localhost",
    "port": 3306,
    "database": "testdb",
    "username": "root",
    "password": "pass",
}

POSTGRESQL_PAYLOAD = {
    "db_type": "postgresql",
    "server": "localhost",
    "port": 5432,
    "database": "testdb",
    "username": "postgres",
    "password": "pass",
}

SQLITE_PAYLOAD = {
    "db_type": "sqlite",
    "server": "",
    "database": "/tmp/test.db",
}


# ── /api/database/connect  MS SQL ─────────────────────────────────────────────

class TestDatabaseConnect:
    def test_returns_table_list(self):
        with patch("db_connector.get_connection") as mock_get_conn, \
             patch("db_connector.get_tables") as mock_get_tables:
            mock_get_conn.return_value = MagicMock()
            mock_get_tables.return_value = [
                {"schema": "dbo", "table_name": "Product", "full_name": "dbo.Product"},
                {"schema": "dbo", "table_name": "Order",   "full_name": "dbo.Order"},
            ]
            res = client.post("/api/database/connect", json=MSSQL_PAYLOAD)

        assert res.status_code == 200
        data = res.json()
        assert "tables" in data
        assert len(data["tables"]) == 2
        assert data["tables"][0]["full_name"] == "dbo.Product"

    def test_connection_failure_returns_400(self):
        with patch("db_connector.get_connection") as mock_get_conn:
            mock_get_conn.side_effect = Exception("Login failed")
            res = client.post("/api/database/connect", json=MSSQL_PAYLOAD)

        assert res.status_code == 400
        assert "Login failed" in res.json()["detail"]

    def test_windows_auth_payload(self):
        payload = {**MSSQL_PAYLOAD, "auth_type": "windows", "username": None, "password": None}
        with patch("db_connector.get_connection") as mock_get_conn, \
             patch("db_connector.get_tables") as mock_get_tables:
            mock_get_conn.return_value = MagicMock()
            mock_get_tables.return_value = []
            res = client.post("/api/database/connect", json=payload)

        assert res.status_code == 200
        call_args = mock_get_conn.call_args
        # Signature: get_connection(db_type, server, port, database, username, password, auth_type)
        assert call_args.args[6] == "windows"


# ── /api/database/connect  MySQL ──────────────────────────────────────────────

class TestDatabaseConnectMySQL:
    def test_returns_table_list(self):
        with patch("db_connector.get_connection") as mock_get_conn, \
             patch("db_connector.get_tables") as mock_get_tables:
            mock_get_conn.return_value = MagicMock()
            mock_get_tables.return_value = [
                {"schema": "testdb", "table_name": "users", "full_name": "users"},
                {"schema": "testdb", "table_name": "orders", "full_name": "orders"},
            ]
            res = client.post("/api/database/connect", json=MYSQL_PAYLOAD)

        assert res.status_code == 200
        data = res.json()
        assert len(data["tables"]) == 2
        assert data["tables"][0]["full_name"] == "users"

    def test_db_type_forwarded(self):
        with patch("db_connector.get_connection") as mock_get_conn, \
             patch("db_connector.get_tables") as mock_get_tables:
            mock_get_conn.return_value = MagicMock()
            mock_get_tables.return_value = []
            client.post("/api/database/connect", json=MYSQL_PAYLOAD)

        assert mock_get_conn.call_args.args[0] == "mysql"

    def test_connection_failure_returns_400(self):
        with patch("db_connector.get_connection") as mock_get_conn:
            mock_get_conn.side_effect = Exception("Access denied for user")
            res = client.post("/api/database/connect", json=MYSQL_PAYLOAD)

        assert res.status_code == 400


# ── /api/database/connect  PostgreSQL ────────────────────────────────────────

class TestDatabaseConnectPostgreSQL:
    def test_returns_table_list(self):
        with patch("db_connector.get_connection") as mock_get_conn, \
             patch("db_connector.get_tables") as mock_get_tables:
            mock_get_conn.return_value = MagicMock()
            mock_get_tables.return_value = [
                {"schema": "public", "table_name": "users", "full_name": "public.users"},
            ]
            res = client.post("/api/database/connect", json=POSTGRESQL_PAYLOAD)

        assert res.status_code == 200
        assert res.json()["tables"][0]["full_name"] == "public.users"

    def test_db_type_forwarded(self):
        with patch("db_connector.get_connection") as mock_get_conn, \
             patch("db_connector.get_tables") as mock_get_tables:
            mock_get_conn.return_value = MagicMock()
            mock_get_tables.return_value = []
            client.post("/api/database/connect", json=POSTGRESQL_PAYLOAD)

        assert mock_get_conn.call_args.args[0] == "postgresql"


# ── /api/database/connect  SQLite ─────────────────────────────────────────────

class TestDatabaseConnectSQLite:
    def test_returns_table_list(self):
        with patch("db_connector.get_connection") as mock_get_conn, \
             patch("db_connector.get_tables") as mock_get_tables:
            mock_get_conn.return_value = MagicMock()
            mock_get_tables.return_value = [
                {"schema": "main", "table_name": "products", "full_name": "products"},
            ]
            res = client.post("/api/database/connect", json=SQLITE_PAYLOAD)

        assert res.status_code == 200
        assert res.json()["tables"][0]["full_name"] == "products"

    def test_db_type_forwarded(self):
        with patch("db_connector.get_connection") as mock_get_conn, \
             patch("db_connector.get_tables") as mock_get_tables:
            mock_get_conn.return_value = MagicMock()
            mock_get_tables.return_value = []
            client.post("/api/database/connect", json=SQLITE_PAYLOAD)

        assert mock_get_conn.call_args.args[0] == "sqlite"


# ── /api/database/schema ──────────────────────────────────────────────────────

class TestDatabaseSchema:
    def test_returns_schema_for_selected_tables(self):
        payload = {**MSSQL_PAYLOAD, "tables": ["dbo.Product"]}
        with patch("db_connector.get_connection") as mock_get_conn, \
             patch("db_connector.get_columns") as mock_get_cols:
            mock_get_conn.return_value = MagicMock()
            mock_get_cols.return_value = SAMPLE_COLS[:2]
            res = client.post("/api/database/schema", json=payload)

        assert res.status_code == 200
        data = res.json()
        assert "schema" in data
        assert "dbo.Product" in data["schema"]
        assert len(data["schema"]["dbo.Product"]) == 2

    def test_multiple_tables(self):
        payload = {**MSSQL_PAYLOAD, "tables": ["dbo.Product", "dbo.Order"]}
        with patch("db_connector.get_connection") as mock_get_conn, \
             patch("db_connector.get_columns") as mock_get_cols:
            mock_get_conn.return_value = MagicMock()
            mock_get_cols.return_value = []
            res = client.post("/api/database/schema", json=payload)

        assert res.status_code == 200
        assert mock_get_cols.call_count == 2

    def test_mysql_schema(self):
        payload = {**MYSQL_PAYLOAD, "tables": ["users"]}
        with patch("db_connector.get_connection") as mock_get_conn, \
             patch("db_connector.get_columns") as mock_get_cols:
            mock_get_conn.return_value = MagicMock()
            mock_get_cols.return_value = SAMPLE_COLS[:2]
            res = client.post("/api/database/schema", json=payload)

        assert res.status_code == 200
        assert "users" in res.json()["schema"]

    def test_sqlite_schema(self):
        payload = {**SQLITE_PAYLOAD, "tables": ["products"]}
        with patch("db_connector.get_connection") as mock_get_conn, \
             patch("db_connector.get_columns") as mock_get_cols:
            mock_get_conn.return_value = MagicMock()
            mock_get_cols.return_value = SAMPLE_COLS[:2]
            res = client.post("/api/database/schema", json=payload)

        assert res.status_code == 200
        assert "products" in res.json()["schema"]


# ── /api/database/generate-service ───────────────────────────────────────────

class TestDatabaseGenerateService:
    COLS = [
        {"name": "Id",    "sql_type": "int",     "service_type": "integer",
         "is_nullable": False, "max_length": None, "is_primary_key": True},
        {"name": "Title", "sql_type": "nvarchar", "service_type": "string",
         "is_nullable": False, "max_length": 200,  "is_primary_key": False},
    ]

    PAYLOAD = {
        **MSSQL_PAYLOAD,
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

        assert res.json()["service_type"] == "SOAP"

    def test_connection_error_returns_400(self):
        with patch("db_connector.get_connection") as mock_get_conn:
            mock_get_conn.side_effect = Exception("Connection refused")
            res = client.post("/api/database/generate-service", json=self.PAYLOAD)

        assert res.status_code == 400

    def test_mysql_generate_service(self):
        mysql_cols = [
            {"name": "id",    "sql_type": "int",     "service_type": "integer",
             "is_nullable": False, "max_length": None, "is_primary_key": True},
            {"name": "name",  "sql_type": "varchar",  "service_type": "string",
             "is_nullable": False, "max_length": 100,  "is_primary_key": False},
        ]
        payload = {
            **MYSQL_PAYLOAD,
            "tables": ["users"],
            "operations": {"users": ["getAll", "getById", "create"]},
            "service_name": "UserService",
            "service_type": "REST",
        }
        with patch("db_connector.get_connection") as mock_get_conn, \
             patch("db_connector.get_columns") as mock_get_cols:
            mock_get_conn.return_value = MagicMock()
            mock_get_cols.return_value = mysql_cols
            res = client.post("/api/database/generate-service", json=payload)

        assert res.status_code == 200
        data = res.json()
        assert data["service_name"] == "UserService"
        method_names = [m["name"] for m in data["methods"]]
        # "users" → PascalCase "Users"
        assert "getAllUsers" in method_names
        assert "getUsersById" in method_names
        assert "createUsers" in method_names

    def test_postgresql_generate_service(self):
        pg_cols = [
            {"name": "id",    "sql_type": "integer", "service_type": "integer",
             "is_nullable": False, "max_length": None, "is_primary_key": True},
            {"name": "title", "sql_type": "text",    "service_type": "string",
             "is_nullable": False, "max_length": None, "is_primary_key": False},
        ]
        payload = {
            **POSTGRESQL_PAYLOAD,
            "tables": ["public.articles"],
            "operations": {"public.articles": ["getAll", "getById"]},
            "service_name": "ArticleService",
            "service_type": "REST",
        }
        with patch("db_connector.get_connection") as mock_get_conn, \
             patch("db_connector.get_columns") as mock_get_cols:
            mock_get_conn.return_value = MagicMock()
            mock_get_cols.return_value = pg_cols
            res = client.post("/api/database/generate-service", json=payload)

        assert res.status_code == 200
        data = res.json()
        assert data["service_name"] == "ArticleService"
        # "articles" → PascalCase "Articles"
        assert any(m["name"] == "Articles" for m in data["models"])

    def test_sqlite_generate_service(self):
        sqlite_cols = [
            {"name": "id",   "sql_type": "integer", "service_type": "integer",
             "is_nullable": False, "max_length": None, "is_primary_key": True},
            {"name": "body", "sql_type": "text",    "service_type": "string",
             "is_nullable": True,  "max_length": None, "is_primary_key": False},
        ]
        payload = {
            **SQLITE_PAYLOAD,
            "tables": ["notes"],
            "operations": {"notes": ["getAll", "create", "delete"]},
            "service_name": "NoteService",
            "service_type": "REST",
        }
        with patch("db_connector.get_connection") as mock_get_conn, \
             patch("db_connector.get_columns") as mock_get_cols:
            mock_get_conn.return_value = MagicMock()
            mock_get_cols.return_value = sqlite_cols
            res = client.post("/api/database/generate-service", json=payload)

        assert res.status_code == 200
        data = res.json()
        assert data["service_name"] == "NoteService"
        method_names = [m["name"] for m in data["methods"]]
        # "notes" → PascalCase "Notes"
        assert "getAllNotes" in method_names
        assert "createNotes" in method_names
        assert "deleteNotes" in method_names


# ── db_connector.map_sql_type ─────────────────────────────────────────────────

class TestMapSqlTypeMSSQL:
    def test_integer_types(self):
        from db_connector import map_sql_type
        for t in ("int", "bigint", "smallint", "tinyint"):
            assert map_sql_type(t, 'mssql') == "integer", f"Failed for {t}"

    def test_float_types(self):
        from db_connector import map_sql_type
        for t in ("float", "decimal", "numeric", "money"):
            assert map_sql_type(t, 'mssql') == "float", f"Failed for {t}"

    def test_string_types(self):
        from db_connector import map_sql_type
        for t in ("varchar", "nvarchar", "char", "nchar", "text", "xml"):
            assert map_sql_type(t, 'mssql') == "string", f"Failed for {t}"

    def test_boolean(self):
        from db_connector import map_sql_type
        assert map_sql_type("bit", 'mssql') == "boolean"

    def test_datetime_as_string(self):
        from db_connector import map_sql_type
        for t in ("datetime", "datetime2", "date", "time"):
            assert map_sql_type(t, 'mssql') == "string", f"Failed for {t}"

    def test_unknown_defaults_to_string(self):
        from db_connector import map_sql_type
        assert map_sql_type("geometry", 'mssql') == "string"

    def test_case_insensitive(self):
        from db_connector import map_sql_type
        assert map_sql_type("INT", 'mssql') == "integer"
        assert map_sql_type("NVarChar", 'mssql') == "string"

    def test_default_db_type_is_mssql(self):
        from db_connector import map_sql_type
        assert map_sql_type("int") == "integer"
        assert map_sql_type("bit") == "boolean"


class TestMapSqlTypeMySQL:
    def test_integer_types(self):
        from db_connector import map_sql_type
        for t in ("int", "integer", "bigint", "smallint", "tinyint", "mediumint"):
            assert map_sql_type(t, 'mysql') == "integer", f"Failed for {t}"

    def test_float_types(self):
        from db_connector import map_sql_type
        for t in ("float", "double", "decimal", "numeric"):
            assert map_sql_type(t, 'mysql') == "float", f"Failed for {t}"

    def test_string_types(self):
        from db_connector import map_sql_type
        for t in ("char", "varchar", "text", "tinytext", "mediumtext", "longtext"):
            assert map_sql_type(t, 'mysql') == "string", f"Failed for {t}"

    def test_boolean(self):
        from db_connector import map_sql_type
        assert map_sql_type("bool", 'mysql') == "boolean"
        assert map_sql_type("boolean", 'mysql') == "boolean"

    def test_datetime_as_string(self):
        from db_connector import map_sql_type
        for t in ("date", "datetime", "timestamp", "time"):
            assert map_sql_type(t, 'mysql') == "string", f"Failed for {t}"

    def test_json_as_string(self):
        from db_connector import map_sql_type
        assert map_sql_type("json", 'mysql') == "string"

    def test_unknown_defaults_to_string(self):
        from db_connector import map_sql_type
        assert map_sql_type("geometry", 'mysql') == "string"


class TestMapSqlTypePostgreSQL:
    def test_integer_types(self):
        from db_connector import map_sql_type
        for t in ("integer", "bigint", "smallint", "serial", "bigserial"):
            assert map_sql_type(t, 'postgresql') == "integer", f"Failed for {t}"

    def test_float_types(self):
        from db_connector import map_sql_type
        for t in ("real", "double precision", "numeric", "decimal", "money"):
            assert map_sql_type(t, 'postgresql') == "float", f"Failed for {t}"

    def test_string_types(self):
        from db_connector import map_sql_type
        for t in ("varchar", "character varying", "text", "uuid", "json", "jsonb"):
            assert map_sql_type(t, 'postgresql') == "string", f"Failed for {t}"

    def test_boolean(self):
        from db_connector import map_sql_type
        assert map_sql_type("boolean", 'postgresql') == "boolean"
        assert map_sql_type("bool", 'postgresql') == "boolean"

    def test_datetime_as_string(self):
        from db_connector import map_sql_type
        for t in ("date", "timestamp", "timestamp without time zone", "timestamptz"):
            assert map_sql_type(t, 'postgresql') == "string", f"Failed for {t}"

    def test_unknown_defaults_to_string(self):
        from db_connector import map_sql_type
        assert map_sql_type("geometry", 'postgresql') == "string"


class TestMapSqlTypeSQLite:
    def test_integer_types(self):
        from db_connector import map_sql_type
        for t in ("integer", "int", "tinyint", "smallint", "bigint"):
            assert map_sql_type(t, 'sqlite') == "integer", f"Failed for {t}"

    def test_float_types(self):
        from db_connector import map_sql_type
        for t in ("real", "float", "double", "numeric", "decimal"):
            assert map_sql_type(t, 'sqlite') == "float", f"Failed for {t}"

    def test_string_types(self):
        from db_connector import map_sql_type
        for t in ("text", "varchar", "nvarchar", "character", "clob"):
            assert map_sql_type(t, 'sqlite') == "string", f"Failed for {t}"

    def test_boolean(self):
        from db_connector import map_sql_type
        assert map_sql_type("boolean", 'sqlite') == "boolean"
        assert map_sql_type("bool", 'sqlite') == "boolean"

    def test_unknown_defaults_to_string(self):
        from db_connector import map_sql_type
        assert map_sql_type("custom_type", 'sqlite') == "string"
