from typing import List, Dict, Optional, Any


SUPPORTED_DB_TYPES = ['mssql', 'mysql', 'postgresql', 'sqlite']

# ── Type maps ──────────────────────────────────────────────────────────────────

MSSQL_TYPE_MAP = {
    'int': 'integer', 'bigint': 'integer', 'smallint': 'integer', 'tinyint': 'integer',
    'float': 'float', 'real': 'float', 'decimal': 'float', 'numeric': 'float',
    'money': 'float', 'smallmoney': 'float',
    'varchar': 'string', 'nvarchar': 'string', 'char': 'string', 'nchar': 'string',
    'text': 'string', 'ntext': 'string', 'xml': 'string',
    'bit': 'boolean',
    'datetime': 'string', 'datetime2': 'string', 'date': 'string', 'time': 'string',
    'datetimeoffset': 'string', 'smalldatetime': 'string',
    'uniqueidentifier': 'string',
    'binary': 'string', 'varbinary': 'string', 'image': 'string',
}

MYSQL_TYPE_MAP = {
    'tinyint': 'integer', 'smallint': 'integer', 'mediumint': 'integer',
    'int': 'integer', 'integer': 'integer', 'bigint': 'integer',
    'float': 'float', 'double': 'float', 'decimal': 'float', 'numeric': 'float', 'real': 'float',
    'char': 'string', 'varchar': 'string', 'tinytext': 'string', 'text': 'string',
    'mediumtext': 'string', 'longtext': 'string', 'enum': 'string', 'set': 'string',
    'json': 'string',
    'bool': 'boolean', 'boolean': 'boolean',
    'date': 'string', 'datetime': 'string', 'timestamp': 'string', 'time': 'string', 'year': 'string',
    'binary': 'string', 'varbinary': 'string', 'tinyblob': 'string', 'blob': 'string',
    'mediumblob': 'string', 'longblob': 'string',
}

POSTGRESQL_TYPE_MAP = {
    'smallint': 'integer', 'integer': 'integer', 'bigint': 'integer',
    'int': 'integer', 'int2': 'integer', 'int4': 'integer', 'int8': 'integer',
    'serial': 'integer', 'bigserial': 'integer', 'smallserial': 'integer',
    'real': 'float', 'double precision': 'float', 'float4': 'float', 'float8': 'float',
    'numeric': 'float', 'decimal': 'float', 'money': 'float',
    'character varying': 'string', 'varchar': 'string', 'character': 'string',
    'char': 'string', 'text': 'string', 'name': 'string', 'uuid': 'string',
    'json': 'string', 'jsonb': 'string', 'xml': 'string',
    'boolean': 'boolean', 'bool': 'boolean',
    'date': 'string', 'timestamp': 'string', 'timestamp without time zone': 'string',
    'timestamp with time zone': 'string', 'timestamptz': 'string',
    'time': 'string', 'time without time zone': 'string', 'time with time zone': 'string',
    'interval': 'string', 'bytea': 'string',
}

SQLITE_TYPE_MAP = {
    'integer': 'integer', 'int': 'integer', 'tinyint': 'integer', 'smallint': 'integer',
    'mediumint': 'integer', 'bigint': 'integer', 'int2': 'integer', 'int8': 'integer',
    'real': 'float', 'double': 'float', 'double precision': 'float', 'float': 'float',
    'numeric': 'float', 'decimal': 'float',
    'character': 'string', 'varchar': 'string', 'varying character': 'string',
    'nchar': 'string', 'native character': 'string', 'nvarchar': 'string',
    'text': 'string', 'clob': 'string',
    'boolean': 'boolean', 'bool': 'boolean',
    'date': 'string', 'datetime': 'string',
    'blob': 'string',
}

TYPE_MAPS = {
    'mssql': MSSQL_TYPE_MAP,
    'mysql': MYSQL_TYPE_MAP,
    'postgresql': POSTGRESQL_TYPE_MAP,
    'sqlite': SQLITE_TYPE_MAP,
}


def map_sql_type(sql_type: str, db_type: str = 'mssql') -> str:
    type_map = TYPE_MAPS.get(db_type, MSSQL_TYPE_MAP)
    return type_map.get(sql_type.lower(), 'string')


# ── Connection factories ───────────────────────────────────────────────────────

def _connect_mssql(server: str, port: Optional[int], database: str,
                   username: Optional[str], password: Optional[str],
                   auth_type: str = "sql"):
    try:
        import pyodbc
    except ImportError:
        raise ImportError("pyodbc 未安裝，請執行：pip install pyodbc")

    drivers = [
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 17 for SQL Server",
        "ODBC Driver 13 for SQL Server",
        "SQL Server",
    ]
    server_str = f"{server},{port}" if port else server
    last_error = None

    for driver in drivers:
        try:
            if auth_type == "windows":
                conn_str = (
                    f"DRIVER={{{driver}}};SERVER={server_str};DATABASE={database};"
                    "Trusted_Connection=yes;TrustServerCertificate=yes;"
                )
            else:
                conn_str = (
                    f"DRIVER={{{driver}}};SERVER={server_str};DATABASE={database};"
                    f"UID={username};PWD={password};TrustServerCertificate=yes;"
                )
            return pyodbc.connect(conn_str, timeout=10)
        except pyodbc.Error as e:
            last_error = e
            continue

    raise Exception(f"無法連線到 MS SQL Server: {last_error}")


def _connect_mysql(server: str, port: Optional[int], database: str,
                   username: Optional[str], password: Optional[str]):
    try:
        import pymysql
    except ImportError:
        raise ImportError("pymysql 未安裝，請執行：pip install pymysql")

    return pymysql.connect(
        host=server,
        port=port or 3306,
        database=database,
        user=username or '',
        password=password or '',
        connect_timeout=10,
        charset='utf8mb4',
    )


def _connect_postgresql(server: str, port: Optional[int], database: str,
                        username: Optional[str], password: Optional[str]):
    try:
        import psycopg2
    except ImportError:
        raise ImportError("psycopg2 未安裝，請執行：pip install psycopg2-binary")

    return psycopg2.connect(
        host=server,
        port=port or 5432,
        dbname=database,
        user=username or '',
        password=password or '',
        connect_timeout=10,
    )


def _connect_sqlite(database: str):
    import sqlite3
    return sqlite3.connect(database)


def get_connection(db_type: str, server: str, port: Optional[int], database: str,
                   username: Optional[str], password: Optional[str],
                   auth_type: str = "sql"):
    if db_type == 'mssql':
        return _connect_mssql(server, port, database, username, password, auth_type)
    elif db_type == 'mysql':
        return _connect_mysql(server, port, database, username, password)
    elif db_type == 'postgresql':
        return _connect_postgresql(server, port, database, username, password)
    elif db_type == 'sqlite':
        return _connect_sqlite(database)
    else:
        raise ValueError(f"不支援的資料庫類型: {db_type}，支援類型: {', '.join(SUPPORTED_DB_TYPES)}")


# ── get_tables ─────────────────────────────────────────────────────────────────

def _get_tables_mssql(conn) -> List[Dict[str, str]]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TABLE_SCHEMA, TABLE_NAME,
               TABLE_SCHEMA + '.' + TABLE_NAME AS full_name
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """)
    return [
        {"schema": row[0], "table_name": row[1], "full_name": row[2]}
        for row in cursor.fetchall()
    ]


def _get_tables_mysql(conn) -> List[Dict[str, str]]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_NAME
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
    """)
    return [
        {"schema": row[0], "table_name": row[1], "full_name": row[2]}
        for row in cursor.fetchall()
    ]


def _get_tables_postgresql(conn) -> List[Dict[str, str]]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT schemaname, tablename,
               schemaname || '.' || tablename AS full_name
        FROM pg_tables
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY schemaname, tablename
    """)
    return [
        {"schema": row[0], "table_name": row[1], "full_name": row[2]}
        for row in cursor.fetchall()
    ]


def _get_tables_sqlite(conn) -> List[Dict[str, str]]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    return [
        {"schema": "main", "table_name": row[0], "full_name": row[0]}
        for row in cursor.fetchall()
    ]


def get_tables(conn, db_type: str = 'mssql') -> List[Dict[str, str]]:
    if db_type == 'mssql':
        return _get_tables_mssql(conn)
    elif db_type == 'mysql':
        return _get_tables_mysql(conn)
    elif db_type == 'postgresql':
        return _get_tables_postgresql(conn)
    elif db_type == 'sqlite':
        return _get_tables_sqlite(conn)
    else:
        raise ValueError(f"不支援的資料庫類型: {db_type}")


# ── get_columns ────────────────────────────────────────────────────────────────

def _get_columns_mssql(conn, full_table_name: str) -> List[Dict[str, Any]]:
    if '.' in full_table_name:
        schema, tbl = full_table_name.split('.', 1)
    else:
        schema, tbl = 'dbo', full_table_name

    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            c.COLUMN_NAME,
            c.DATA_TYPE,
            c.IS_NULLABLE,
            c.CHARACTER_MAXIMUM_LENGTH,
            CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 1 ELSE 0 END AS IS_PRIMARY_KEY
        FROM INFORMATION_SCHEMA.COLUMNS c
        LEFT JOIN (
            SELECT ku.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku
                ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
                AND tc.TABLE_SCHEMA = ku.TABLE_SCHEMA
                AND tc.TABLE_NAME = ku.TABLE_NAME
            WHERE tc.TABLE_SCHEMA = ? AND tc.TABLE_NAME = ?
              AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
        ) pk ON c.COLUMN_NAME = pk.COLUMN_NAME
        WHERE c.TABLE_SCHEMA = ? AND c.TABLE_NAME = ?
        ORDER BY c.ORDINAL_POSITION
    """, schema, tbl, schema, tbl)

    return [
        {
            "name": row[0],
            "sql_type": row[1],
            "service_type": map_sql_type(row[1], 'mssql'),
            "is_nullable": row[2] == "YES",
            "max_length": row[3],
            "is_primary_key": bool(row[4]),
        }
        for row in cursor.fetchall()
    ]


def _get_columns_mysql(conn, table_name: str) -> List[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            c.COLUMN_NAME,
            c.DATA_TYPE,
            c.IS_NULLABLE,
            c.CHARACTER_MAXIMUM_LENGTH,
            IF(c.COLUMN_KEY = 'PRI', 1, 0) AS IS_PRIMARY_KEY
        FROM information_schema.COLUMNS c
        WHERE c.TABLE_SCHEMA = DATABASE() AND c.TABLE_NAME = %s
        ORDER BY c.ORDINAL_POSITION
    """, (table_name,))

    return [
        {
            "name": row[0],
            "sql_type": row[1],
            "service_type": map_sql_type(row[1], 'mysql'),
            "is_nullable": row[2] == "YES",
            "max_length": row[3],
            "is_primary_key": bool(row[4]),
        }
        for row in cursor.fetchall()
    ]


def _get_columns_postgresql(conn, full_table_name: str) -> List[Dict[str, Any]]:
    if '.' in full_table_name:
        schema, tbl = full_table_name.split('.', 1)
    else:
        schema, tbl = 'public', full_table_name

    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            c.column_name,
            c.data_type,
            c.is_nullable,
            c.character_maximum_length,
            CASE WHEN kcu.column_name IS NOT NULL THEN true ELSE false END AS is_primary_key
        FROM information_schema.columns c
        LEFT JOIN (
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
                AND tc.table_name = kcu.table_name
            WHERE tc.table_schema = %s AND tc.table_name = %s
              AND tc.constraint_type = 'PRIMARY KEY'
        ) kcu ON c.column_name = kcu.column_name
        WHERE c.table_schema = %s AND c.table_name = %s
        ORDER BY c.ordinal_position
    """, (schema, tbl, schema, tbl))

    return [
        {
            "name": row[0],
            "sql_type": row[1],
            "service_type": map_sql_type(row[1], 'postgresql'),
            "is_nullable": row[2] == "YES",
            "max_length": row[3],
            "is_primary_key": bool(row[4]),
        }
        for row in cursor.fetchall()
    ]


def _get_columns_sqlite(conn, table_name: str) -> List[Dict[str, Any]]:
    # PRAGMA table_info: cid, name, type, notnull, dflt_value, pk
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info(\"{table_name}\")")
    return [
        {
            "name": row[1],
            "sql_type": (row[2].split('(')[0].strip().lower()) if row[2] else 'text',
            "service_type": map_sql_type(
                (row[2].split('(')[0].strip().lower()) if row[2] else 'text', 'sqlite'
            ),
            "is_nullable": not bool(row[3]),
            "max_length": None,
            "is_primary_key": bool(row[5]),
        }
        for row in cursor.fetchall()
    ]


def get_columns(conn, full_table_name: str, db_type: str = 'mssql') -> List[Dict[str, Any]]:
    if db_type == 'mssql':
        return _get_columns_mssql(conn, full_table_name)
    elif db_type == 'mysql':
        return _get_columns_mysql(conn, full_table_name)
    elif db_type == 'postgresql':
        return _get_columns_postgresql(conn, full_table_name)
    elif db_type == 'sqlite':
        return _get_columns_sqlite(conn, full_table_name)
    else:
        raise ValueError(f"不支援的資料庫類型: {db_type}")
