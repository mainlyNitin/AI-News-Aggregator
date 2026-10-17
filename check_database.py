import sqlite3
from database import DB_PATH

conn = sqlite3.connect(DB_PATH)

# Check tables
tables = conn.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
""").fetchall()

print("Database:", DB_PATH)
print("Tables:", tables)

# Count saved articles
count = conn.execute(
    "SELECT COUNT(*) FROM articles"
).fetchone()[0]

print("Saved articles:", count)

# Count saved AI summaries
summaries = conn.execute("""
    SELECT COUNT(*)
    FROM articles
    WHERE summary IS NOT NULL AND summary != ''
""").fetchone()[0]

print("Saved AI summaries:", summaries)

conn.close()