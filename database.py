import sqlite3

DB = "amazon.db"


def init_db():
    """Create products and reviews tables."""
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id          TEXT PRIMARY KEY,
                product_name        TEXT,
                category            TEXT,
                discounted_price    REAL,
                actual_price        REAL,
                discount_percentage REAL,
                rating              REAL,
                rating_count        INTEGER,
                about_product       TEXT,
                img_link            TEXT,
                product_link        TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                review_id       TEXT PRIMARY KEY,
                product_id      TEXT,
                user_id         TEXT,
                user_name       TEXT,
                review_title    TEXT,
                review_content  TEXT,
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        """)

        conn.commit()


def get_schema():
    """Return the full DB schema as a string."""
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
        rows = cursor.fetchall()
        return "\n\n".join(row[0] for row in rows if row[0])


def is_safe_query(query: str) -> bool:
    """Allow only SELECT statements."""
    blocked = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "REPLACE"]
    query_upper = query.upper().strip()
    if not query_upper.startswith("SELECT"):
        return False
    return not any(keyword in query_upper for keyword in blocked)


def execute_sql(query: str):
    """Run a SELECT query and return (columns, rows)."""
    if not is_safe_query(query):
        raise ValueError("Only SELECT queries are allowed.")
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        return columns, rows
