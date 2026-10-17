
import feedparser
import pandas as pd

RSS_FEEDS = {
    "India": "https://indianexpress.com/section/india/feed/",
    "Technology": "https://indianexpress.com/section/technology/feed/",
    "Business": "https://indianexpress.com/section/business/feed/",
    "Sports": "https://indianexpress.com/section/sports/feed/",
    "India - BBC": "https://feeds.bbci.co.uk/news/world/asia/india/rss.xml",
}

def fetch_news():
    articles = []

    for category, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)

            if feed.bozo and not feed.entries:
                print(f"Could not read {category} feed.")
                continue

            for entry in feed.entries[:10]:
                articles.append({
                    "Title": entry.get("title", "No title"),
                    "Category": category,
                    "Source": feed.feed.get("title", category),
                    "Link": entry.get("link", ""),
                    "Published": entry.get("published", "Unknown"),
                })

        except Exception as error:
            print(f"Error fetching {category}: {error}")

    df = pd.DataFrame(
        articles,
        columns=[
            "Title", "Category", "Source",
            "Link", "Published"
        ]
    )

    if not df.empty:
        df = df.drop_duplicates(subset=["Link"])
        df = df[df["Link"].astype(bool)]

    return df


if __name__ == "__main__":
    news = fetch_news()

    if news.empty:
        print("No news received. Check your internet or RSS feeds.")
    else:
        print(news[["Title", "Category", "Source"]].to_string(index=False))
        news.to_csv("news.csv", index=False)
        print(f"\nTotal unique articles: {len(news)}")
        print("Saved to news.csv")
