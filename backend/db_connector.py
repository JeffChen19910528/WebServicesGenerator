from typing import List, Dict, Optional, Any


SQL_TYPE_MAP = {
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


def map_sql_type(sql_type: str) -> str:
    return SQL_TYPE_MAP.get(sql_type.lower(), 'string')


def get_connection(server: str, port: Optional[int], database: str,
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

    raise Exception(f"無法連線到資料庫: {last_error}")


def get_tables(conn) -> List[Dict[str, str]]:
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


def get_columns(conn, full_table_name: str) -> List[Dict[str, Any]]:
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
            "service_type": map_sql_type(row[1]),
            "is_nullable": row[2] == "YES",
            "max_length": row[3],
            "is_primary_key": bool(row[4]),
        }
        for row in cursor.fetchall()
    ]
