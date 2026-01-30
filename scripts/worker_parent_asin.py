import asyncio
import re
from playwright.async_api import async_playwright
from pathlib import Path

async def find_parent_asin(asin: str):
    """
    Scrape Amazon DP page to find the parentAsin using Regex.
    """
    url = f"https://www.amazon.com/dp/{asin}"
    print(f"🕵️ Searching for parent of {asin} at {url}...")
    
    async with async_playwright() as p:
        # Launch browser (non-headless as per requirement)
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="load", timeout=30000)
            content = await page.content()
            
            # Simple Regex to find parentAsin
            match = re.search(r'"parentAsin"\s*:\s*"(B[A-Z0-9]{9})"', content)
            if match:
                parent = match.group(1)
                print(f"✅ Found Parent ASIN: {parent}")
                return parent
            else:
                print(f"❌ Could not find parentAsin in page source for {asin}")
                # Fallback: maybe it's its own parent?
                return None
        except Exception as e:
            print(f"⚠️ Error scraping {asin}: {e}")
            return None
        finally:
            await browser.close()

async def main(asins: list):
    results = {}
    for asin in asins:
        parent = await find_parent_asin(asin)
        results[asin] = parent
        await asyncio.sleep(2) # Delay to avoid detection
    return results

if __name__ == "__main__":
    import sys
    asins = sys.argv[1:] if len(sys.argv) > 1 else ["B00P8XQPY4"]
    asyncio.run(main(asins))
