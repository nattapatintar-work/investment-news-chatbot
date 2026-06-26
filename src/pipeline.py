import os 
import json
import requests
from anthropic import Anthropic
from dotenv import load_dotenv
from newspaper import Article
from monitor import log_request, log_error

load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
client = Anthropic()

# ─────────────────────────────────────────────
def fetch_news(ticker: str, num_articles: int = 5) -> list:
    """
    Fetch top news articles for a given stock ticker.

    Args:
        ticker       : stock symbol e.g. "NVDA"
        num_articles : how many articles to fetch (default 5)

    Returns:
        list of dicts containing article title, url, and description
    """
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={ticker}&"
        f"language=en&"
        f"sortBy=publishedAt&"
        f"pageSize={num_articles}&"
        f"apiKey={NEWS_API_KEY}"
    )

    response = requests.get(url)
    data     = response.json()

    articles = []
    for article in data["articles"]:
        articles.append({
            "title"      : article["title"],
            "url"        : article["url"],
            "description": article["description"]
        })

    return articles

def scrape_article(url: str) -> str:
    """
    Visit a URL and extract the full article text.

    Args:
        url : the article URL from fetch_news()

    Returns:
        full article text as a string
    """
    article = Article(url)
    article.download()
    article.parse()
    return article.text


def summarize_article(article_text: str, ticker: str = "") -> dict:
    """
    Send a news article to Claude and get back a structured summary.

    Args:
        article_text : the raw news article text
        ticker       : optional stock symbol e.g. "NVDA"

    Returns:
        dict with english_summary, thai_summary, impact, sentiment, confidence
    """

    # YOU WRITE THIS — few-shot system prompt with examples
    system_prompt = """You are a financial analyst assistant specializing in investment news.
You must respond in raw JSON only.
No markdown. No backticks. No explanation.
Start your response with { and end with }

Here are examples of correct analysis:

Example 1:
Article: Apple reported record iPhone sales of 80 million units,
beating analyst expectations by 15%. CEO Tim Cook said demand
remains strong heading into the holiday season.
Output:
{
    "english_summary": "Apple reported record iPhone sales of 80 million units, beating analyst expectations by 15%. CEO Tim Cook expressed confidence in continued strong demand heading into the holiday season.",
    "thai_summary": "Apple รายงานยอดขาย iPhone สูงสุดที่ 80 ล้านเครื่อง เกินความคาดหมายของนักวิเคราะห์ 15%",
    "impact": "Positive for AAPL investors as record sales suggest continued revenue growth.",
    "sentiment": "Bullish",
    "confidence": "High"
}

Example 2:
Article: Tesla missed quarterly earnings expectations with revenue
falling 8% year-over-year. The company cited production challenges
and increased competition from Chinese EV makers.
Output:
{
    "english_summary": "Tesla missed quarterly earnings with revenue declining 8% year-over-year due to production challenges and intensifying competition from Chinese EV manufacturers.",
    "thai_summary": "Tesla พลาดเป้าหมายรายได้รายไตรมาส โดยรายได้ลดลง 8% เมื่อเทียบปีต่อปี",
    "impact": "Negative for TSLA investors as declining revenue and competitive pressure may compress margins.",
    "sentiment": "Bearish",
    "confidence": "High"
}"""

    # YOU WRITE THIS — user prompt with optional ticker focus
    user_prompt = f"""Analyze this financial news article and return JSON only.
{"Focus on impact to " + ticker + " investors." if ticker else ""}

Article:
{article_text}"""
    
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )

    # BOILERPLATE — clean and parse JSON response
    raw_text   = response.content[0].text
    clean_text = raw_text.replace("```json", "").replace("```", "").strip()
    result     = json.loads(clean_text)

    # BOILERPLATE — add metadata
    result["ticker"]      = ticker
    result["token_used"]  = response.usage.input_tokens + response.usage.output_tokens

    return result


def run_pipeline(ticker: str, num_articles: int = 3) -> list:
    """
    Full pipeline — fetch, scrape, and summarize news for a ticker.

    Args:
        ticker       : stock symbol e.g. "NVDA"
        num_articles : how many articles to process

    Returns:
        list of summaries
    """
    total_tokens = 0
    try:
        print(f"Fetching {num_articles} articles for {ticker}...")
        articles = fetch_news(ticker, num_articles)

        results = []
        for i, article in enumerate(articles):
            print(f"Processing article {i+1} of {num_articles}...")

            # Step 1 — scrape full text from URL
            full_text = scrape_article(article["url"])

            # Step 2 — send to Claude for summary
            summary = summarize_article(full_text, ticker)

            total_tokens += summary["token_used"]

            # Step 3 — collect results
            results.append({
                "title"      : article["title"],
                "url"        : article["url"],
                "summary"    : summary["english_summary"],
                "thai"       : summary["thai_summary"],
                "impact"     : summary["impact"],
                "sentiment"  : summary["sentiment"],
                "confidence" : summary["confidence"],
                "token_used" : summary["token_used"]
            })
        log_request(ticker, num_articles, total_tokens, success=True)
        return results
    except Exception as e :
        log_error(ticker , e)
        log_request(ticker , num_articles ,total_tokens ,success=False)
        raise

if __name__ == '__main__':
    print("pipeline.py is running...")  
    results = run_pipeline("NVDA", num_articles = 3)
    for i, result in enumerate(results):
        print(f"\nArticle {i+1}")
        print("Title     :", result["title"])
        print("Sentiment :", result["sentiment"])
        print("Summary   :", result["summary"])
        print("Thai      :", result["thai"])
        print("Impact    :", result["impact"])
        print("-" * 50)