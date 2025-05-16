import psycopg2
from utils import get_db_connection, release_connection, init_connection

class PostgresOperator:
    """
    """
    def __init__(self, db_pool):
        self.db_pool = db_pool

    def execute_select(self, query_path, params=None):
        """Execute a SELECT query from a .sql file and return results as a list of dicts."""
        with open(query_path, 'r') as f:
            query = f.read().strip()
            if not query:
                raise ValueError(f"Query '{query_path}' not found.")

        # Get connection from pool
        conn = get_db_connection(self.db_pool)
        if not conn:
            raise ConnectionError("Failed to get database connection.")
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    columns = [desc[0] for desc in cursor.description]
                    result = [dict(zip(columns, row)) for row in cursor.fetchall()]
                    return result, None
        except Exception as e:
            return None, str(e)
        finally:
            release_connection(self.db_pool, conn)

    def execute_insert(self, query_path, params=None):
        """Execute an INSERT query from .sql file and return the number of affected rows."""
        with open(query_path, "r") as f:
            query = f.read().strip()
            if not query:
                raise ValueError(f"Query '{query_path}' not found.")
            
        conn = get_db_connection(self.db_pool)
        if not conn:
            raise ConnectionError("Failed to get database connection.")
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor.rowcount, None
        except Exception as e:
            return 0, str(e)
        finally:
            release_connection(self.db_pool, conn)

    def execute_query(self, query, params=None, fetch=False):
        """Execute a SQL query. If fetch is True, return results as list of dicts."""
        conn = get_db_connection(self.db_pool)
        if not conn:
            raise ConnectionError("Failed to get database connection.")
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    if fetch:
                        columns = [desc[0] for desc in cursor.description]
                        result = [dict(zip(columns, row)) for row in cursor.fetchall()]
                        return result, None
                    else:
                        conn.commit()
                        return cursor.rowcount, None
        except Exception as e:
            return None if fetch else 0, str(e)
        finally:
            release_connection(self.db_pool, conn)

if __name__ == "__main__":
    db_pool = init_connection()
    operator = PostgresOperator(db_pool=db_pool)
    result = operator.execute_select(r'queries/select_locations.sql', (1,))
    print(f"Execute SELECT: {result}")
