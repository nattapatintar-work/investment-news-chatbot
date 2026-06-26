import streamlit as st
from src.pipeline import fetch_news, scrape_article, summarize_article
from src.portfolio import get_price, MY_PORTFOLIO

st.set_page_config(page_title="Stock News Summarizer", page_icon="📈", layout="wide")
st.title("📈 Stock News Summarizer")

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Settings")
    ticker = st.text_input("Stock Ticker", value="NVDA").upper().strip()
    num_articles = st.slider("Number of Articles", min_value=1, max_value=10, value=3)
    run = st.button("Fetch & Summarize", type="primary", use_container_width=True)

    st.divider()
    st.subheader("My Portfolio")
    for sym, shares in MY_PORTFOLIO.items():
        price, change = get_price(sym)
        arrow = "▲" if "+" in str(change) else "▼"
        st.metric(
            label=f"{sym} ({shares} shares)",
            value=f"${price:.2f}",
            delta=change,
        )

# ── Main area ─────────────────────────────────────────────────────────────────
if run:
    if not ticker:
        st.warning("Please enter a stock ticker.")
        st.stop()

    with st.spinner(f"Fetching {num_articles} articles for **{ticker}**…"):
        try:
            articles = fetch_news(ticker, num_articles)
        except Exception as e:
            st.error(f"Failed to fetch news: {e}")
            st.stop()

    if not articles:
        st.info("No articles found for this ticker.")
        st.stop()

    st.subheader(f"News Summary for {ticker}")

    for i, article in enumerate(articles):
        with st.expander(f"📰 {article['title']}", expanded=(i == 0)):
            with st.spinner("Analyzing with Claude…"):
                try:
                    full_text = scrape_article(article["url"])
                    result = summarize_article(full_text, ticker)
                except Exception as e:
                    st.error(f"Could not process article: {e}")
                    continue

            sentiment_color = {
                "Bullish": "green",
                "Bearish": "red",
                "Neutral": "orange",
            }.get(result.get("sentiment", ""), "gray")

            col1, col2, col3 = st.columns(3)
            col1.metric("Sentiment", result.get("sentiment", "N/A"))
            col2.metric("Confidence", result.get("confidence", "N/A"))
            col3.metric("Tokens Used", result.get("token_used", 0))

            st.markdown("**Summary (EN)**")
            st.write(result.get("english_summary", ""))

            st.markdown("**สรุป (TH)**")
            st.write(result.get("thai_summary", ""))

            st.markdown("**Impact**")
            st.info(result.get("impact", ""))

            st.caption(f"[Read full article]({article['url']})")
else:
    st.info("Enter a ticker in the sidebar and click **Fetch & Summarize** to get started.")
