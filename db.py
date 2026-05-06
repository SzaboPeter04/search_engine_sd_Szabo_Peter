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
    ensure_col_sql = "ALTER TABLE documents ADD COLUMN IF NOT EXISTS path_score double precision DEFAULT 0;"

    insert_sql = """
    INSERT INTO documents (
        path, filename, extension, size_bytes, modified_at, content, preview, path_score
    ) VALUES (
        %(path)s, %(filename)s, %(extension)s, %(size_bytes)s,
        %(modified_at)s, %(content)s, %(preview)s, %(path_score)s
    )
    """

    update_sql = """
    UPDATE documents SET
        filename = %(filename)s,
        extension = %(extension)s,
        size_bytes = %(size_bytes)s,
        modified_at = %(modified_at)s,
        content = %(content)s,
        preview = %(preview)s,
        path_score = %(path_score)s
    WHERE path = %(path)s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM documents WHERE path = %s", (doc["path"],))
            exists = cur.fetchone() is not None

            
            try:
                cur.execute(ensure_col_sql)
            except Exception:
                
                pass

            if exists:
                cur.execute(update_sql, doc)
                conn.commit()
                return False
            else:
                cur.execute(insert_sql, doc)
                conn.commit()
                return True

def _parse_query(query_text: str):
    import re

    qualifiers = {}

    
    for m in re.finditer(r"(\w+):\s*\"([^\"]+)\"|(\w+):\s*(\S+)", query_text):
        if m.group(1):
            key = m.group(1).lower()
            val = m.group(2)
        else:
            key = m.group(3).lower()
            val = m.group(4)
        qualifiers.setdefault(key, []).append(val)

    
    free = re.sub(r"(\w+):\s*\"([^\"]+)\"|(\w+):\s*(\S+)", "", query_text)
    
    free = re.sub(r"\b\w+:(?=\s|$)", "", free).strip()
    return qualifiers, free


def search_documents(query, ranking="alphabetical"):
    with get_connection() as conn:
        with conn.cursor() as cur:
            
            try:
                cur.execute(
                    "SELECT 1 FROM information_schema.columns WHERE table_name = %s AND column_name = %s",
                    ("documents", "path_score"),
                )
                col_exists = cur.fetchone() is not None
            except Exception:
                col_exists = False
            if not query or not str(query).strip():
                order_clause = "modified_at DESC" if ranking == "date" else "filename ASC"
                if ranking == "score":
                    order_clause = "path_score DESC"

                if col_exists:
                    cur.execute(
                        f"""
                        SELECT path, filename, extension, preview, modified_at, path_score
                        FROM documents
                        ORDER BY {order_clause}
                        LIMIT %s
                        """,
                        (SEARCH_LIMIT,)
                    )
                else:
                    
                    cur.execute(
                        f"""
                        SELECT path, filename, extension, preview, modified_at
                        FROM documents
                        ORDER BY {order_clause}
                        LIMIT %s
                        """,
                        (SEARCH_LIMIT,)
                    )
                return cur.fetchall()

            qualifiers, free_text = _parse_query(str(query))

            where_clauses = []
            params = []

            
            for key, vals in qualifiers.items():
                sub_clauses = []
                for v in vals:
                    if key == "path":
                        
                        sub_clauses.append("REPLACE(path, CHR(92), '/') ILIKE %s")
                        nv = v.rstrip("/\\")
                        if nv == "":
                            nv = v
                        v_fwd = nv.replace('\\', '/')
                        params.append(f"%{v_fwd}%")
                    elif key == "content":
                        sub_clauses.append("content ILIKE %s")
                        params.append(f"%{v}%")
                    elif key == "filename":
                        sub_clauses.append("filename ILIKE %s")
                        params.append(f"%{v}%")
                    elif key == "extension":
                        sub_clauses.append("extension ILIKE %s")
                        params.append(f"%{v}%")
                    else:
                        sub_clauses.append("(filename ILIKE %s OR content ILIKE %s OR path ILIKE %s)")
                        params.extend([f"%{v}%"] * 3)

                if sub_clauses:
                    where_clauses.append("(" + " OR ".join(sub_clauses) + ")")

            
            if free_text:
                like = f"%{free_text}%"
                where_clauses.append("(filename ILIKE %s OR content ILIKE %s OR path ILIKE %s)")
                params.extend([like, like, like])

            where_sql = " AND ".join(where_clauses) if where_clauses else "TRUE"

            order_clause = "filename ASC"
            if ranking == "date":
                order_clause = "modified_at DESC"
            elif ranking == "score":
                order_clause = "path_score DESC"

            if col_exists:
                sql = f"""
                SELECT path, filename, extension, preview, modified_at, path_score
                FROM documents
                WHERE {where_sql}
                ORDER BY {order_clause}
                LIMIT %s
                """
            else:
                sql = f"""
                SELECT path, filename, extension, preview, modified_at
                FROM documents
                WHERE {where_sql}
                ORDER BY {order_clause}
                LIMIT %s
                """

            params.append(SEARCH_LIMIT)
            cur.execute(sql, tuple(params))
            return cur.fetchall()


def get_document_content(path):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT content FROM documents WHERE path = %s", (path,))
            row = cur.fetchone()
            if not row:
                return ""
            return row.get("content", "")


def increment_path_score(path, amount=1):
    ensure_col_sql = "ALTER TABLE documents ADD COLUMN IF NOT EXISTS path_score double precision DEFAULT 0;"
    with get_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(ensure_col_sql)
            except Exception:
                
                pass

            cur.execute(
                """
                UPDATE documents
                SET path_score = COALESCE(path_score, 0) + %s
                WHERE path = %s
                RETURNING path_score
                """,
                (amount, path),
            )
            row = cur.fetchone()
            if not row:
                return None
            
            new_score = row.get("path_score") if isinstance(row, dict) else row[0]
            conn.commit()
            return new_score
