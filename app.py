
import streamlit as st
import pandas as pd
import plotly.express as px

from news_fetcher import fetch_news
from ai_summarizer import summarize_news
from sentiment_analyzer import analyze_sentiment

from database import (
    save_articles,
    get_all_articles,
    get_summary,
    save_summary,
    save_sentiment
)


# --------------------------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="AI News Aggregator",
    page_icon="📰",
    layout="wide"
)

st.title("📰 AI News Aggregator")
st.write(
    "Live news, SQLite storage, Gemini AI summaries, "
    "sentiment analysis, and interactive visualizations."
)


# --------------------------------------------------
# 2. REFRESH NEWS
# --------------------------------------------------

if st.button("🔄 Refresh News"):
    st.cache_data.clear()
    st.rerun()


# --------------------------------------------------
# 3. FETCH AND STORE NEWS
# --------------------------------------------------

@st.cache_data(ttl=300)
def load_news():
    fresh_news = fetch_news()

    if fresh_news is not None and not fresh_news.empty:
        save_articles(fresh_news)

    return get_all_articles()


df = load_news()

if df is None or df.empty:
    st.warning(
        "No saved news is available. Check your internet "
        "connection and click Refresh News."
    )
    st.stop()


# --------------------------------------------------
# 4. ENSURE REQUIRED COLUMNS EXIST
# --------------------------------------------------

required_columns = [
    "Title",
    "Category",
    "Source",
    "Published",
    "Link",
    "Description",
    "Sentiment",
    "SentimentScore"
]

for column in required_columns:
    if column not in df.columns:
        df[column] = ""


# --------------------------------------------------
# 5. CALCULATE AND SAVE SENTIMENT FOR ALL ARTICLES
# --------------------------------------------------

progress = st.progress(0, text="Analyzing saved news...")

total_articles = len(df)

for position, (index, article) in enumerate(
    df.iterrows(), start=1
):
    title = str(article["Title"] or "")
    description = str(article["Description"] or "")
    link = str(article["Link"] or "").strip()

    sentiment_text = f"{title}. {description}"
    sentiment, score = analyze_sentiment(sentiment_text)

    # Save sentiment to SQLite
    if link:
        save_sentiment(link, sentiment, score)

    # Update the DataFrame immediately
    df.at[index, "Sentiment"] = sentiment
    df.at[index, "SentimentScore"] = score

    progress.progress(
        position / total_articles,
        text=f"Analyzing article {position} of {total_articles}..."
    )

progress.empty()


# --------------------------------------------------
# 6. PREPARE PUBLICATION DATES
# --------------------------------------------------

df["PublishedDate"] = pd.to_datetime(
    df["Published"],
    errors="coerce",
    utc=True
).dt.date


# --------------------------------------------------
# 7. SIDEBAR FILTERS
# --------------------------------------------------

st.sidebar.header("📰 News Filters")

categories = ["All"] + sorted(
    df["Category"].dropna().astype(str).unique().tolist()
)

selected_category = st.sidebar.selectbox(
    "Select category",
    categories
)

search = st.sidebar.text_input("Search headlines")

st.sidebar.subheader("📅 Date Filter")

valid_dates = df["PublishedDate"].dropna()

# Start with all articles
filtered = df.copy()

# Category filter
if selected_category != "All":
    filtered = filtered[
        filtered["Category"] == selected_category
    ]

# Headline search
if search:
    filtered = filtered[
        filtered["Title"].astype(str).str.contains(
            search,
            case=False,
            na=False
        )
    ]

# Publication date filter
if not valid_dates.empty:

    min_date = min(valid_dates)
    max_date = max(valid_dates)

    date_range = st.sidebar.date_input(
        "Select publication date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        start_date, end_date = date_range

        filtered = filtered[
            filtered["PublishedDate"].notna()
            & (filtered["PublishedDate"] >= start_date)
            & (filtered["PublishedDate"] <= end_date)
        ]

else:
    st.sidebar.info("No valid publication dates available.")


# --------------------------------------------------
# 8. DASHBOARD METRICS
# --------------------------------------------------

col1, col2, col3 = st.columns(3)

col1.metric("Total Saved Articles", len(df))
col2.metric("Matching Articles", len(filtered))
col3.metric("News Categories", df["Category"].nunique())


# --------------------------------------------------
# 9. SENTIMENT METRICS
# --------------------------------------------------

st.subheader("📈 Sentiment Overview")

sentiment_labels = (
    filtered["Sentiment"]
    .fillna("Neutral")
    .replace("", "Neutral")
)

positive_count = int((sentiment_labels == "Positive").sum())
neutral_count = int((sentiment_labels == "Neutral").sum())
negative_count = int((sentiment_labels == "Negative").sum())

col4, col5, col6 = st.columns(3)

col4.metric("😊 Positive News", positive_count)
col5.metric("😐 Neutral News", neutral_count)
col6.metric("😟 Negative News", negative_count)


# --------------------------------------------------
# 10. NEWS CARDS AND GEMINI SUMMARIES
# --------------------------------------------------

st.subheader("📰 Latest News")

if filtered.empty:
    st.info("No articles match your selected filters.")

else:
    for i, (_, article) in enumerate(filtered.iterrows()):

        with st.container(border=True):

            title = str(article["Title"] or "Untitled")
            link = str(article["Link"] or "").strip()
            description = str(article["Description"] or "")

            st.markdown(f"### {title}")
            st.write(f"**Category:** {article['Category']}")
            st.write(f"**Source:** {article['Source']}")
            st.write(f"**Published:** {article['Published']}")

            # Sentiment label
            sentiment = article["Sentiment"]
            score = article["SentimentScore"]

            if sentiment == "Positive":
                st.success(
                    f"😊 Sentiment: {sentiment} | Score: {score}"
                )
            elif sentiment == "Negative":
                st.error(
                    f"😟 Sentiment: {sentiment} | Score: {score}"
                )
            else:
                st.info(
                    f"😐 Sentiment: {sentiment} | Score: {score}"
                )

            # Original article link
            if link.startswith(("https://", "http://")):
                st.link_button("🔗 Read Full Article", link)

            # Load saved AI summary
            saved_summary = get_summary(link) if link else ""

            if saved_summary:
                st.markdown("#### 🤖 Saved AI Summary")
                st.markdown(saved_summary)

            button_label = (
                "🔄 Regenerate AI Summary"
                if saved_summary
                else "✨ Summarize News"
            )

            if st.button(
                button_label,
                key=f"summary_{i}"
            ):

                if not link:
                    st.error(
                        "This article has no link, "
                        "so its summary cannot be saved."
                    )

                else:
                    with st.spinner("Generating AI summary..."):
                        result = summarize_news(
                            title,
                            description
                        )

                    if result.startswith(
                        (
                            "AI summary failed:",
                            "Error:",
                            "Summary failed."
                        )
                    ):
                        st.error(result)

                    else:
                        save_summary(link, result)

                        st.success(
                            "AI summary generated and saved in SQLite!"
                        )

                        st.markdown("#### 🤖 AI Summary")
                        st.markdown(result)


# --------------------------------------------------
# 11. NEWS BY CATEGORY CHART
# --------------------------------------------------

st.subheader("📊 News by Category")

chart_data = (
    filtered["Category"]
    .value_counts()
    .rename_axis("Category")
    .reset_index(name="Articles")
)

if not chart_data.empty:

    fig_category = px.bar(
        chart_data,
        x="Category",
        y="Articles",
        color="Category",
        text="Articles",
        title="Articles in Each Category"
    )

    st.plotly_chart(
        fig_category,
        use_container_width=True
    )

else:
    st.info("No category data available.")


# --------------------------------------------------
# 12. SENTIMENT DISTRIBUTION CHART
# --------------------------------------------------

st.subheader("📊 News Sentiment Distribution")

sentiment_chart_data = (
    sentiment_labels
    .value_counts()
    .reindex(
        ["Positive", "Neutral", "Negative"],
        fill_value=0
    )
    .rename_axis("Sentiment")
    .reset_index(name="Articles")
)

fig_sentiment = px.pie(
    sentiment_chart_data,
    names="Sentiment",
    values="Articles",
    title="Positive vs Neutral vs Negative News",
    hole=0.45
)

fig_sentiment.update_traces(
    textposition="inside",
    textinfo="percent+label"
)

st.plotly_chart(
    fig_sentiment,
    use_container_width=True
)


# --------------------------------------------------
# 13. NEWS PUBLICATION TREND
# --------------------------------------------------

st.subheader("📅 News Publication Trend")

trend_data = filtered.dropna(
    subset=["PublishedDate"]
).copy()

if not trend_data.empty:

    daily_counts = (
        trend_data.groupby("PublishedDate")
        .size()
        .reset_index(name="Articles")
        .sort_values("PublishedDate")
    )

    fig_trend = px.line(
        daily_counts,
        x="PublishedDate",
        y="Articles",
        markers=True,
        title="Number of News Articles Published Each Day"
    )

    fig_trend.update_layout(
        xaxis_title="Publication Date",
        yaxis_title="Number of Articles"
    )

    st.plotly_chart(
        fig_trend,
        use_container_width=True
    )

else:
    st.info("No publication dates available for the selected filters.")


# --------------------------------------------------
# 14. SENTIMENT OVER TIME
# --------------------------------------------------

st.subheader("📈 Sentiment Over Time")

if not trend_data.empty:

    daily_sentiment = (
        trend_data.groupby(
            ["PublishedDate", "Sentiment"]
        )
        .size()
        .reset_index(name="Articles")
        .sort_values("PublishedDate")
    )

    fig_sentiment_trend = px.line(
        daily_sentiment,
        x="PublishedDate",
        y="Articles",
        color="Sentiment",
        markers=True,
        title="Daily News Sentiment Trends",
        category_orders={
            "Sentiment": ["Positive", "Neutral", "Negative"]
        }
    )

    fig_sentiment_trend.update_layout(
        xaxis_title="Publication Date",
        yaxis_title="Number of Articles",
        legend_title="Sentiment"
    )

    st.plotly_chart(
        fig_sentiment_trend,
        use_container_width=True
    )

else:
    st.info("No sentiment trend data available.")
