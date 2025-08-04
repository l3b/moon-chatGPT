
import os
from typing import List, Dict, Any
from langchain_community.utilities import SQLDatabase
from sqlalchemy.exc import SQLAlchemyError

class SQLConnector:
    def __init__(self):
        # Build SQLAlchemy connection URL for LangChain (Azure-ready)
        driver = 'ODBC Driver 18 for SQL Server'
        server = os.getenv('SQL_SERVER')
        database = os.getenv('SQL_DATABASE')
        username = os.getenv('SQL_USERNAME')
        password = os.getenv('SQL_PASSWORD')
        if not all([server, database, username, password]):
            raise ValueError("SQL_SERVER, SQL_DATABASE, SQL_USERNAME, and SQL_PASSWORD must be set in environment variables.")
        self.connection_url = f"mssql+pyodbc://{username}:{password}@{server}:1433/{database}?driver={driver.replace(' ', '+')}"
        self.db = SQLDatabase.from_uri(self.connection_url)

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute SQL query and return results as list of dicts using LangChain."""
        try:
            if not self._is_safe_query(query):
                raise ValueError("Unsafe query detected")
            result = self.db.run(query)
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