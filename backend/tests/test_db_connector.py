"""Unit tests for db_connector.py – tests connection dispatch and schema queries (mocked drivers)."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import patch, MagicMock, call


# ── get_connection dispatch ────────────────────────────────────────────────────

class TestGetConnectionDispatch:
    def test_mssql_calls_pyodbc(self):
        from db_connector import get_connection
        mock_conn = MagicMock()
        with patch("db_connector._connect_mssql", return_value=mock_conn) as mock_fn:
            result = get_connection('mssql', 'localhost', 1433, 'TestDB', 'sa', 'pass', 'sql')
        mock_fn.assert_called_once_with('localhost', 1433, 'TestDB', 'sa', 'pass', 'sql')
        assert result is mock_conn

    def test_mysql_dispatch(self):
        from db_connector import get_connection
        mock_conn = MagicMock()
        with patch("db_connector._connect_mysql", return_value=mock_conn) as mock_fn:
            result = get_connection('mysql', 'localhost', 3306, 'mydb', 'root', 'pass')
        mock_fn.assert_called_once_with('localhost', 3306, 'mydb', 'root', 'pass')
        assert result is mock_conn

    def test_postgresql_dispatch(self):
        from db_connector import get_connection
        mock_conn = MagicMock()
        with patch("db_connector._connect_postgresql", return_value=mock_conn) as mock_fn:
            result = get_connection('postgresql', 'localhost', 5432, 'pgdb', 'postgres', 'pass')
        mock_fn.assert_called_once_with('localhost', 5432, 'pgdb', 'postgres', 'pass')
        assert result is mock_conn

    def test_sqlite_dispatch(self):
        from db_connector import get_connection
        mock_conn = MagicMock()
        with patch("db_connector._connect_sqlite", return_value=mock_conn) as mock_fn:
            result = get_connection('sqlite', '', None, '/tmp/test.db', None, None)
        mock_fn.assert_called_once_with('/tmp/test.db')
        assert result is mock_conn

    def test_unsupported_db_type_raises(self):
        from db_connector import get_connection
        with pytest.raises(ValueError, match="不支援的資料庫類型"):
            get_connection('oracle', 'localhost', None, 'db', None, None)


# ── get_tables dispatch ────────────────────────────────────────────────────────

class TestGetTablesDispatch:
    def test_mssql_tables_format(self):
        from db_connector import get_tables
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            ("dbo", "Product", "dbo.Product"),
            ("sales", "Order", "sales.Order"),
        ]
        result = get_tables(mock_conn, 'mssql')
        assert len(result) == 2
        assert result[0] == {"schema": "dbo", "table_name": "Product", "full_name": "dbo.Product"}
        assert result[1] == {"schema": "sales", "table_name": "Order", "full_name": "sales.Order"}

    def test_mysql_tables_format(self):
        from db_connector import get_tables
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            ("myapp", "users", "users"),
            ("myapp", "orders", "orders"),
        ]
        result = get_tables(mock_conn, 'mysql')
        assert len(result) == 2
        assert result[0] == {"schema": "myapp", "table_name": "users", "full_name": "users"}
        # MySQL: full_name has no schema prefix
        assert '.' not in result[0]["full_name"]

    def test_postgresql_tables_format(self):
        from db_connector import get_tables
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            ("public", "users", "public.users"),
            ("app", "products", "app.products"),
        ]
        result = get_tables(mock_conn, 'postgresql')
        assert result[0] == {"schema": "public", "table_name": "users", "full_name": "public.users"}

    def test_sqlite_tables_format(self):
        from db_connector import get_tables
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            ("notes",),
            ("settings",),
        ]
        result = get_tables(mock_conn, 'sqlite')
        assert len(result) == 2
        assert result[0] == {"schema": "main", "table_name": "notes", "full_name": "notes"}
        assert result[1]["schema"] == "main"

    def test_unsupported_type_raises(self):
        from db_connector import get_tables
        with pytest.raises(ValueError):
            get_tables(MagicMock(), 'oracle')

    def test_default_db_type_is_mssql(self):
        from db_connector import get_tables
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [("dbo", "T", "dbo.T")]
        result = get_tables(mock_conn)  # no db_type → defaults to mssql
        assert result[0]["full_name"] == "dbo.T"


# ── get_columns dispatch ───────────────────────────────────────────────────────

class TestGetColumnsDispatch:
    def _make_mssql_cursor_rows(self):
        return [
            ("Id",    "int",      "NO",  None, 1),
            ("Name",  "nvarchar", "NO",  100,  0),
            ("Price", "decimal",  "YES", None, 0),
        ]

    def test_mssql_columns_parsed(self):
        from db_connector import get_columns
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = self._make_mssql_cursor_rows()

        result = get_columns(mock_conn, "dbo.Product", 'mssql')
        assert len(result) == 3
        assert result[0]["name"] == "Id"
        assert result[0]["service_type"] == "integer"
        assert result[0]["is_primary_key"] is True
        assert result[1]["is_primary_key"] is False
        assert result[2]["is_nullable"] is True

    def test_mssql_schema_defaults_to_dbo(self):
        from db_connector import get_columns
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        get_columns(mock_conn, "Product", 'mssql')  # no schema prefix
        # verify the SQL was called (cursor.execute was called)
        assert mock_cursor.execute.called

    def test_mysql_columns_parsed(self):
        from db_connector import get_columns
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            ("id",    "int",     "NO",  None, 1),
            ("email", "varchar", "YES", 255,  0),
        ]

        result = get_columns(mock_conn, "users", 'mysql')
        assert len(result) == 2
        assert result[0]["service_type"] == "integer"
        assert result[0]["is_primary_key"] is True
        assert result[1]["service_type"] == "string"
        assert result[1]["is_nullable"] is True

    def test_postgresql_columns_parsed(self):
        from db_connector import get_columns
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            ("id",    "integer", "NO",  None, True),
            ("title", "text",    "NO",  None, False),
            ("score", "numeric", "YES", None, False),
        ]

        result = get_columns(mock_conn, "public.articles", 'postgresql')
        assert result[0]["service_type"] == "integer"
        assert result[0]["is_primary_key"] is True
        assert result[1]["service_type"] == "string"
        assert result[2]["service_type"] == "float"
        assert result[2]["is_nullable"] is True

    def test_postgresql_schema_defaults_to_public(self):
        from db_connector import get_columns
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        get_columns(mock_conn, "articles", 'postgresql')  # no schema prefix
        assert mock_cursor.execute.called

    def test_sqlite_columns_parsed(self):
        from db_connector import get_columns
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        # PRAGMA table_info: cid, name, type, notnull, dflt_value, pk
        mock_cursor.fetchall.return_value = [
            (0, "id",    "INTEGER",    1, None, 1),
            (1, "name",  "TEXT",       1, None, 0),
            (2, "score", "REAL",       0, None, 0),
            (3, "notes", "VARCHAR(50)",0, None, 0),
        ]

        result = get_columns(mock_conn, "products", 'sqlite')
        assert len(result) == 4
        assert result[0]["service_type"] == "integer"
        assert result[0]["is_primary_key"] is True
        assert result[1]["service_type"] == "string"
        assert result[1]["is_nullable"] is False
        assert result[2]["service_type"] == "float"
        assert result[2]["is_nullable"] is True
        # VARCHAR(50) → stripped to 'varchar'
        assert result[3]["sql_type"] == "varchar"
        assert result[3]["service_type"] == "string"

    def test_sqlite_empty_type_defaults_to_text(self):
        from db_connector import get_columns
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            (0, "data", "", 0, None, 0),  # empty type
        ]
        result = get_columns(mock_conn, "raw_table", 'sqlite')
        assert result[0]["sql_type"] == "text"
        assert result[0]["service_type"] == "string"

    def test_unsupported_type_raises(self):
        from db_connector import get_columns
        with pytest.raises(ValueError):
            get_columns(MagicMock(), "table", 'oracle')

    def test_default_db_type_is_mssql(self):
        from db_connector import get_columns
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [("Id", "int", "NO", None, 1)]
        result = get_columns(mock_conn, "dbo.T")  # no db_type → defaults to mssql
        assert result[0]["service_type"] == "integer"


# ── _connect_mysql / _connect_postgresql / _connect_sqlite ──────────────────

class TestConnectMySQL:
    def test_uses_pymysql(self):
        mock_pymysql = MagicMock()
        mock_pymysql.connect.return_value = MagicMock()
        with patch.dict("sys.modules", {"pymysql": mock_pymysql}):
            from db_connector import _connect_mysql
            _connect_mysql("localhost", 3306, "mydb", "root", "pass")
        mock_pymysql.connect.assert_called_once()
        kwargs = mock_pymysql.connect.call_args.kwargs
        assert kwargs["host"] == "localhost"
        assert kwargs["port"] == 3306
        assert kwargs["database"] == "mydb"

    def test_default_port_3306(self):
        mock_pymysql = MagicMock()
        mock_pymysql.connect.return_value = MagicMock()
        with patch.dict("sys.modules", {"pymysql": mock_pymysql}):
            from db_connector import _connect_mysql
            _connect_mysql("localhost", None, "mydb", "root", "pass")
        kwargs = mock_pymysql.connect.call_args.kwargs
        assert kwargs["port"] == 3306

    def test_missing_pymysql_raises_importerror(self):
        with patch.dict("sys.modules", {"pymysql": None}):
            import importlib
            import db_connector
            importlib.reload(db_connector)
            with pytest.raises((ImportError, TypeError)):
                db_connector._connect_mysql("host", None, "db", "u", "p")


class TestConnectPostgreSQL:
    def test_uses_psycopg2(self):
        mock_psycopg2 = MagicMock()
        mock_psycopg2.connect.return_value = MagicMock()
        with patch.dict("sys.modules", {"psycopg2": mock_psycopg2}):
            from db_connector import _connect_postgresql
            _connect_postgresql("localhost", 5432, "pgdb", "postgres", "pass")
        mock_psycopg2.connect.assert_called_once()
        kwargs = mock_psycopg2.connect.call_args.kwargs
        assert kwargs["host"] == "localhost"
        assert kwargs["dbname"] == "pgdb"

    def test_default_port_5432(self):
        mock_psycopg2 = MagicMock()
        mock_psycopg2.connect.return_value = MagicMock()
        with patch.dict("sys.modules", {"psycopg2": mock_psycopg2}):
            from db_connector import _connect_postgresql
            _connect_postgresql("localhost", None, "pgdb", "postgres", "pass")
        kwargs = mock_psycopg2.connect.call_args.kwargs
        assert kwargs["port"] == 5432


class TestConnectSQLite:
    def test_uses_sqlite3(self):
        with patch("sqlite3.connect") as mock_connect:
            mock_connect.return_value = MagicMock()
            from db_connector import _connect_sqlite
            _connect_sqlite("/tmp/test.db")
        mock_connect.assert_called_once_with("/tmp/test.db")

    def test_in_memory_database(self):
        with patch("sqlite3.connect") as mock_connect:
            mock_connect.return_value = MagicMock()
            from db_connector import _connect_sqlite
            _connect_sqlite(":memory:")
        mock_connect.assert_called_once_with(":memory:")
