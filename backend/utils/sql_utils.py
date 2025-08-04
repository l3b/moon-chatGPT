import os
import pyodbc

def query_azure_sql(query, params=None):
    """
    Execute a SQL query against Azure SQL Database and return results as a list of dicts.
    """
    conn_str = os.environ["AZURE_SQL_SERVER_CONNECTION_STRING"]
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params or [])
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return results
