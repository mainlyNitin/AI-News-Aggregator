
import os
import sqlite3
import pandas as pd

DB_PATH = os.getenv(
    "DATABASE_PATH",
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "news.db"
    )
)



def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                link TEXT PRIMARY KEY,
                title TEXT,
                category TEXT,
                source TEXT,
                published TEXT,
                description TEXT,
                summary TEXT DEFAULT '',
                saved_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        columns = [
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(articles)"
            ).fetchall()
        ]

        if "sentiment" not in columns:
            conn.execute("""
                ALTER TABLE articles
                ADD COLUMN sentiment TEXT DEFAULT 'Neutral'
            """)

        if "sentiment_score" not in columns:
            conn.execute("""
                ALTER TABLE articles
                ADD COLUMN sentiment_score REAL DEFAULT 0
            """)


def save_articles(df):
    if df is None or df.empty:
        return

    with get_connection() as conn:
        for _, row in df.iterrows():
            link = str(row.get("Link", "") or "").strip()

            if not link:
                continue

            conn.execute("""
                INSERT INTO articles (
                    link, title, category, source,
                    published, description
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(link) DO UPDATE SET
                    title = excluded.title,
                    category = excluded.category,
                    source = excluded.source,
                    published = excluded.published,
                    description = excluded.description
            """, (
                link,
                str(row.get("Title", "") or ""),
                str(row.get("Category", "") or ""),
                str(row.get("Source", "") or ""),
                str(row.get("Published", "") or ""),
                str(row.get("Description", "") or "")
            ))


def get_all_articles():
    with get_connection() as conn:
        return pd.read_sql_query("""
            SELECT
                title AS Title,
                category AS Category,
                source AS Source,
                published AS Published,
                link AS Link,
                description AS Description,
                summary AS Summary,
                sentiment AS Sentiment,
                sentiment_score AS SentimentScore
            FROM articles
            ORDER BY rowid DESC
        """, conn)


def get_summary(link):
    with get_connection() as conn:
        result = conn.execute(
            "SELECT summary FROM articles WHERE link = ?",
            (link,)
        ).fetchone()

    return result[0] if result and result[0] else ""


def save_summary(link, summary):
    with get_connection() as conn:
        conn.execute("""
            UPDATE articles
            SET summary = ?
            WHERE link = ?
        """, (summary, link))


def save_sentiment(link, sentiment, score):
    with get_connection() as conn:
        conn.execute("""
            UPDATE articles
            SET sentiment = ?, sentiment_score = ?
            WHERE link = ?
        """, (sentiment, score, link))


# Create or update the database schema
init_db()
