from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import time
import os
import logging
from rotating_free_proxies.expire import Proxies
from rotating_free_proxies.utils import fetch_new_proxies

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def scrape_kia_parts():
    # Initialize proxy list
    proxy_path = "proxies.txt"  # Local file to store proxies
    max_proxies = 10  # Number of proxies to fetch
    
    # Fetch and initialize proxies
    proxy_list = fetch_new_proxies(proxy_path, max_proxies)
    proxies = Proxies(proxy_list)
    
    with sync_playwright() as p:
        try:
            # Get a random proxy
            proxy = proxies.get_random()
            if not proxy:
                logger.error("No proxies available")
                return
            
            logger.info(f"Using proxy: {proxy}")
            
            # Launch browser with persistent context and proxy
            browser_context = p.chromium.launch_persistent_context(
                user_data_dir=".pw_user",
                headless=False,  # Set to True once everything works
                viewport={'width': 1280, 'height': 800},
                proxy={
                    "server": proxy
                }
            )
            
            page = browser_context.new_page()
            
            # Set headers to appear more like a real browser
            page.set_extra_http_headers({
                'Accept-Language': 'en-US,en;q=0.9',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
            })
            
            # Navigate to the page with retry logic
            max_retries = 3
            url = "https://parts.kia.com/a/Kia_2024_Sorento/_93811_12259916/ACCELERATOR-PEDAL/AKMAPHY24_32-327.html?assemblySearchGuid=0E5330FF-889C-4B09-97EB-2FE549D9C61D"
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"Attempt {attempt + 1} of {max_retries}")
                    response = page.goto(
                        url,
                        timeout=60000,
                        wait_until="networkidle"
                    )
                    
                    # Check if page loaded successfully
                    if page.url == url:
                        break
                    else:
                        logger.warning(f"Got redirected or failed, rotating proxy...")
                        proxies.mark_dead(proxy)  # Mark current proxy as dead
                        proxy = proxies.get_random()  # Get a new proxy
                        if not proxy:
                            logger.error("No more proxies available")
                            return
                        logger.info(f"New proxy: {proxy}")
                        browser_context.close()
                        browser_context = p.chromium.launch_persistent_context(
                            user_data_dir=".pw_user",
                            headless=False,
                            viewport={'width': 1280, 'height': 800},
                            proxy={"server": proxy}
                        )
                        page = browser_context.new_page()
                        page.set_extra_http_headers({
                            'Accept-Language': 'en-US,en;q=0.9',
                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
                        })
                        time.sleep(2)  # Small delay before retry
                        
                except Exception as e:
                    logger.error(f"Error occurred: {str(e)}")
                    if attempt < max_retries - 1:
                        proxies.mark_dead(proxy)  # Mark failed proxy as dead
                        proxy = proxies.get_random()
                        if not proxy:
                            logger.error("No more proxies available after error")
                            return
                        logger.info(f"Rotating to new proxy: {proxy}")
                        time.sleep(2)
                    else:
                        raise Exception("Max retries reached")
            
            # Wait for content to load
            page.wait_for_selector("li.assemblyProdDetails", timeout=30000)
            
            # Get and parse the page content
            content = page.content()
            soup = BeautifulSoup(content, "html.parser")
            parts_data = []
            
            # Find all parts
            parts = soup.find_all("li", class_="assemblyProdDetails")
            
            for part in parts:
                # Extract part details
                name_tag = part.find("div", class_="assemblyProductDescription")
                part_name = name_tag.get_text(strip=True) if name_tag else None
                
                number_tag = part.find("a", class_="btn btn-tertiary")
                part_number = number_tag.get_text(strip=True) if number_tag else None
                
                price_tag = part.find("div", class_="money-4")
                part_price = price_tag.get_text(strip=True).replace("(Current price)", "") if price_tag else None
                
                qty_tag = part.find("input", {"class": "form-control input-sm text-center"})
                part_qty = qty_tag["value"] if qty_tag else None
                
                product_url = None
                if number_tag and number_tag.get("href"):
                    product_url = "https://parts.kia.com" + number_tag["href"]
                
                parts_data.append({
                    "Part Name": part_name,
                    "Part Number": part_number,
                    "Price": part_price,
                    "Quantity": part_qty,
                    "Product URL": product_url
                })
            
            # Save results to JSON
            with open('kia_parts.json', 'w') as f:
                json.dump(parts_data, f, indent=4)
                
            logger.info(f"Scraped {len(parts_data)} parts. Data saved to kia_parts.json")
            
            # Mark the successful proxy as good
            proxies.mark_good(proxy)
            
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            if proxy:
                proxies.mark_dead(proxy)
        
        finally:
            if 'browser_context' in locals():
                browser_context.close()

if __name__ == "__main__":
    scrape_kia_parts()