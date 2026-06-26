# src/portfolio.py

# LIBRARY MAGIC — use, don't memorize
import requests
import os
from dotenv import load_dotenv

# BOILERPLATE — load API key
load_dotenv()
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY", "demo")

# YOU WRITE THIS — your personal portfolio
MY_PORTFOLIO = {
    "AAPL": 10,
    "MSFT": 5,
    "NVDA": 3,
}

# YOU WRITE THIS — fetch live price from Alpha Vantage
def get_price(ticker: str) -> tuple[float, str]:
    """Fetch live price from Alpha Vantage."""
    url = (
        f"https://www.alphavantage.co/query"
        f"?function=GLOBAL_QUOTE&symbol={ticker}&apikey={ALPHA_VANTAGE_KEY}"
    )
    try:
        data = requests.get(url, timeout=10).json()
        quote = data.get("Global Quote", {})
        price = float(quote.get("05. price", 0))
        change = quote.get("10. change percent", "N/A")
        return price, change
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return 0.0, "N/A"

# YOU WRITE THIS — print portfolio report
def portfolio_report(portfolio: dict) -> None:
    """Print a summary report of the portfolio."""
    print("=" * 45)
    print("   MY INVESTMENT PORTFOLIO REPORT")
    print("=" * 45)

    total_value = 0.0

    for ticker, shares in portfolio.items():
        price, change = get_price(ticker)
        value = price * shares
        total_value += value
        arrow = "▲" if "+" in str(change) else "▼"

        print(f"\n  {ticker}")
        print(f"    Price  : ${price:>10.2f}")
        print(f"    Shares : {shares}")
        print(f"    Value  : ${value:>10.2f}")
        print(f"    Today  : {arrow} {change}")

    print("\n" + "-" * 45)
    print(f"  TOTAL VALUE: ${total_value:,.2f}")
    print("=" * 45)

if __name__ == "__main__":
    portfolio_report(MY_PORTFOLIO)