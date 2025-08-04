import os
import pyodbc
import pandas as pd
from typing import List, Dict, Any
from azure.identity import DefaultAzureCredential
import logging

logger = logging.getLogger(__name__)

class SQLConnector:
    def __init__(self):
        # Use connection string or managed identity
        if os.getenv("SQL_CONNECTION_STRING"):
            self.conn_string = os.getenv("SQL_CONNECTION_STRING")
        else:
            # --- REQUIRED ENVIRONMENT VARIABLES FOR TESTING ---
            # SQL_SERVER=<your-server>.database.windows.net
            # SQL_DATABASE=<your-db>
            # SQL_USERNAME=<your-username>
            # SQL_PASSWORD=<your-password>
            # Example connection string generated:
            # mssql+pyodbc://<your-username>:<your-password>@<your-server>.database.windows.net:1433/<your-db>?driver=ODBC+Driver+18+for+SQL+Server
            driver = 'ODBC Driver 18 for SQL Server'
            server = os.getenv('SQL_SERVER') or '<your-server>.database.windows.net'
            database = os.getenv('SQL_DATABASE') or '<your-db>'
            username = os.getenv('SQL_USERNAME') or '<your-username>'
            password = os.getenv('SQL_PASSWORD') or '<your-password>'
            self.connection_url = f"mssql+pyodbc://{username}:{password}@{server}:1433/{database}?driver={driver.replace(' ', '+')}"
            self.db = SQLDatabase.from_uri(self.connection_url)

import os
from typing import List, Dict, Any
from langchain_community.utilities import SQLDatabase
from sqlalchemy.exc import SQLAlchemyError

class SQLConnector:
    def __init__(self):
        # Build SQLAlchemy connection URL for LangChain
        driver = 'ODBC Driver 18 for SQL Server'
        server = os.getenv('SQL_SERVER') or '<your-server>.database.windows.net'
        database = os.getenv('SQL_DATABASE') or '<your-db>'
        username = os.getenv('SQL_USERNAME') or '<your-username>'
        password = os.getenv('SQL_PASSWORD') or '<your-password>'
        self.connection_url = f"mssql+pyodbc://{username}:{password}@{server}:1433/{database}?driver={driver.replace(' ', '+')}"
        self.db = SQLDatabase.from_uri(self.connection_url)

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute SQL query and return results as list of dicts using LangChain."""
        try:
            if not self._is_safe_query(query):
                raise ValueError("Unsafe query detected")
            result = self.db.run(query)
            # LangChain returns a string, try to parse as list of dicts if possible
            import json
            try:
                return json.loads(result)
            except Exception:
                return [{"result": result}]
        except SQLAlchemyError as e:
            raise RuntimeError(f"SQLAlchemy error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"SQL execution error: {str(e)}")

    def _is_safe_query(self, query: str) -> bool:
        forbidden = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'EXEC']
        query_upper = query.upper()
        return not any(word in query_upper for word in forbidden)

    def get_table_schema(self, table_name: str) -> str:
        """Get table schema for context using LangChain."""
        try:
            inspector = self.db._engine.inspect(self.db._engine)
            columns = inspector.get_columns(table_name)
            schema_lines = [f"{col['name']} ({col['type']}) nullable={col['nullable']}" for col in columns]
            return "\n".join(schema_lines)
        except Exception as e:
            return f"Could not retrieve schema: {str(e)}"