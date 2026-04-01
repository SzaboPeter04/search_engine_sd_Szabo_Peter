"""Simple configuration for the search engine.

Change these values if your database or preferences differ.
"""

# Database connection (Postgres). Keep as-is for the demo.
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "search_engine"
DB_USER = "postgres"
DB_PASSWORD = "12345"

# File types we support indexing (lowercase suffixes)
SUPPORTED_EXTENSIONS = {".txt", ".docx"}

# How many characters to keep in the preview
PREVIEW_MAX_CHARS = 500

# Max number of search results to return
SEARCH_LIMIT = 50