import psycopg
from psycopg.rows import dict_row
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, SEARCH_LIMIT


def get_connection():
    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        row_factory=dict_row,
    )

def up_insert_document(doc):
    insert_sql = """
    INSERT INTO documents (
        path, filename, extension, size_bytes, modified_at, content, preview
    ) VALUES (
        %(path)s, %(filename)s, %(extension)s, %(size_bytes)s,
        %(modified_at)s, %(content)s, %(preview)s
    )
    """

    update_sql = """
    UPDATE documents SET
        filename = %(filename)s,
        extension = %(extension)s,
        size_bytes = %(size_bytes)s,
        modified_at = %(modified_at)s,
        content = %(content)s,
        preview = %(preview)s
    WHERE path = %(path)s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM documents WHERE path = %s", (doc["path"],))
            exists = cur.fetchone() is not None

            if exists:
                cur.execute(update_sql, doc)
                conn.commit()
                return False
            else:
                cur.execute(insert_sql, doc)
                conn.commit()
                return True

def search_documents(query):
    with get_connection() as conn:
        with conn.cursor() as cur:
            if not query or not query.strip():
                cur.execute(
                    """
                    SELECT path, filename, extension, preview, modified_at
                    FROM documents
                    ORDER BY modified_at DESC
                    LIMIT %s
                    """,
                    (SEARCH_LIMIT,)
                )
                return cur.fetchall()

            like_query = f"%{query}%"

            cur.execute(
                """
                SELECT path, filename, extension, preview, modified_at
                FROM documents
                WHERE filename ILIKE %s OR content ILIKE %s OR extension ILIKE %s OR path ILIKE %s
                ORDER BY filename ASC
                LIMIT %s
                """,
                (like_query, like_query, like_query, like_query, SEARCH_LIMIT),
            )
            return cur.fetchall()


def get_document_content(path):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT content FROM documents WHERE path = %s", (path,))
            row = cur.fetchone()
            if not row:
                return ""
            return row.get("content", "")