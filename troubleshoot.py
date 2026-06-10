import asyncio
import json
import traceback
import time
from pathlib import Path
from news_mcp_server import (
    DATA_DIR, 
    _fetch_feed, 
    get_global_news, 
    get_stock_news, 
    get_market_snapshot,
    read_portfolio,
    daily_briefing
)
from mcp.server.fastmcp.exceptions import ToolError

async def run_diagnostics():
    print("====== COMPONENT 1: DATA LAYER ======")
    portfolio_path = DATA_DIR / "portfolio.json"
    print(f"Checking {portfolio_path}...")
    if portfolio_path.exists():
        try:
            with open(portfolio_path) as f:
                data = json.load(f)
            print("  ✅ Portfolio JSON is valid.")
            if "tickers" in data:
                print(f"  ✅ Found {len(data['tickers'])} tickers.")
        except Exception as e:
            print(f"  ❌ Portfolio JSON Error: {e}")
    else:
        print("  ❌ Portfolio file missing!")

    print("\n====== COMPONENT 2: NETWORK LAYER (RSS) ======")
    print("Testing valid RSS feed...")
    start = time.time()
    try:
        entries = await _fetch_feed("https://news.google.com/rss/search?q=apple&hl=en-US&gl=US&ceid=US:en", context_label="test")
        print(f"  ✅ Fetched {len(entries.entries)} entries in {time.time()-start:.2f}s")
    except Exception as e:
        print(f"  ❌ RSS Fetch failed: {e}")

    print("Testing invalid RSS feed handling...")
    try:
        # Give it a URL that doesn't exist to see if httpx handles it safely
        await _fetch_feed("https://this-does-not-exist.google.com/rss", context_label="test")
        print("  ❌ Failed to catch bad URL!")
    except Exception as e:
        print(f"  ✅ Caught bad URL correctly: {type(e).__name__}")

    print("\n====== COMPONENT 3: MCP TOOLS ======")
    print("Testing get_stock_news with bad ticker...")
    try:
        await get_stock_news("!@#$BAD")
        print("  ❌ Failed to catch bad ticker!")
    except ToolError as e:
        print(f"  ✅ Caught bad ticker correctly: {e}")

    print("Testing get_market_snapshot concurrency...")
    start = time.time()
    try:
        snap = await get_market_snapshot(["AAPL", "MSFT", "GOOGL"], limit_per_symbol=1)
        print(f"  ✅ Concurrent snapshot of 3 tickers took {time.time()-start:.2f}s")
        assert len(snap) == 3
    except Exception as e:
        print(f"  ❌ Snapshot failed: {e}")

    print("\n====== COMPONENT 4: RESOURCES & PROMPTS ======")
    try:
        port_data = read_portfolio()
        print(f"  ✅ Resource 'portfolio' read successfully ({len(port_data)} bytes)")
    except Exception as e:
        print(f"  ❌ Resource read failed: {e}")
        
    try:
        prompt = daily_briefing('{"articles": []}')
        print(f"  ✅ Prompt 'daily_briefing' generated ({len(prompt)} messages)")
    except Exception as e:
        print(f"  ❌ Prompt generation failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_diagnostics())
