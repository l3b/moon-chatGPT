from langchain_community.utilities import SQLDatabase
import os

# Create a LangChain SQLDatabase object for Azure SQL

def get_langchain_sql_db():
    conn_str = os.environ["AZURE_SQL_SERVER_CONNECTION_STRING"]
    # LangChain expects a SQLAlchemy URL, so we convert the ODBC string
    # Example: mssql+pyodbc://username:password@server:1433/dbname?driver=ODBC+Driver+18+for+SQL+Server
    import urllib
    from sqlalchemy.engine import URL

    # Parse connection string
    # You may want to parse from env or build dynamically
    driver = 'ODBC Driver 18 for SQL Server'
    server = os.environ.get('AZURE_SQL_SERVER_SERVER') or '<your-server>.database.windows.net'
    database = os.environ.get('AZURE_SQL_SERVER_DATABASE') or '<your-db>'
    username = os.environ.get('AZURE_SQL_SERVER_USERNAME') or '<your-username>'
    password = os.environ.get('AZURE_SQL_SERVER_PASSWORD') or '<your-password>'

    connection_url = URL.create(
        "mssql+pyodbc",
        username=username,
        password=password,
        host=server,
        port=1433,
        database=database,
        query={"driver": driver}
    )
    return SQLDatabase.from_uri(str(connection_url))
