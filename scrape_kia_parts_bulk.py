from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
import os
from datetime import datetime
from typing import List, Dict, Optional

# Set up logging with timestamp
log_filename = f"kia_parts_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def read_assembly_urls(filename: str) -> List[str]:
    """Read assembly URLs from file."""
    try:
        with open(filename, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        logger.info(f"Loaded {len(urls)} URLs from {filename}")
        return urls
    except FileNotFoundError:
        logger.error(f"File not found: {filename}")
        raise
    except Exception as e:
        logger.error(f"Error reading URLs file: {e}")
        raise

def scrape_parts_from_page(page, url: str) -> List[Dict]:
    """Scrape parts data from a single page."""
    parts_data = []
    try:
        # Navigate to the page
        logger.info(f"Navigating to {url}")
        response = page.goto(url, timeout=60000, wait_until="networkidle")
        
        if not response.ok:
            logger.error(f"Failed to load page: {url}, status: {response.status}")
            return parts_data
            
        # Wait for parts to load
        page.wait_for_selector("li.assemblyProdDetails", timeout=30000)
        content = page.content()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(content, "html.parser")
        parts = soup.find_all("li", class_="assemblyProdDetails")
        
        # Extract assembly name/category if available
        assembly_name = ""
        breadcrumb = soup.find("ol", class_="breadcrumb")
        if breadcrumb:
            crumbs = breadcrumb.find_all("li")
            if len(crumbs) > 0:
                assembly_name = crumbs[-1].get_text(strip=True)
        
        # Extract parts data
        for part in parts:
            name_tag = part.find("div", class_="assemblyProductDescription")
            number_tag = part.find("a", class_="btn btn-tertiary")
            price_tag = part.find("div", class_="money-4")
            qty_tag = part.find("input", {"class": "form-control input-sm text-center"})
            
            part_data = {
                "Assembly": assembly_name,
                "Part Name": name_tag.get_text(strip=True) if name_tag else None,
                "Part Number": number_tag.get_text(strip=True) if number_tag else None,
                "Price": price_tag.get_text(strip=True).replace("(Current price)", "").strip() if price_tag else None,
                "Quantity": qty_tag["value"] if qty_tag else None,
                "Product URL": f"https://parts.kia.com{number_tag['href']}" if number_tag and number_tag.get('href') else None,
                "Assembly URL": url
            }
            parts_data.append(part_data)
            
        logger.info(f"Successfully scraped {len(parts_data)} parts from assembly: {assembly_name}")
        return parts_data
        
    except PlaywrightTimeout:
        logger.error(f"Timeout while scraping {url}")
        return parts_data
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return parts_data

def main():
    # Initialize variables
    urls_file = "assembly_urls.txt"
    output_file = f"kia_parts_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    all_parts_data = []
    successful_urls = set()
    failed_urls = set()
    
    try:
        # Read URLs
        urls = read_assembly_urls(urls_file)
        total_urls = len(urls)
        
        with sync_playwright() as p:
            # Launch browser
            browser_context = p.chromium.launch_persistent_context(
                user_data_dir=".pw_user",
                headless=False,  # Set to True for production
                viewport={'width': 1280, 'height': 800}
            )
            
            page = browser_context.new_page()
            
            # Set headers
            page.set_extra_http_headers({
                'Accept-Language': 'en-US,en;q=0.9',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
            })
            
            # Process each URL
            for i, url in enumerate(urls, 1):
                try:
                    logger.info(f"Processing URL {i}/{total_urls}")
                    parts_data = scrape_parts_from_page(page, url)
                    
                    if parts_data:
                        all_parts_data.extend(parts_data)
                        successful_urls.add(url)
                        
                        # Save progress periodically (every 5 URLs)
                        if i % 5 == 0:
                            df = pd.DataFrame(all_parts_data)
                            df.to_csv(output_file, index=False)
                            logger.info(f"Progress saved: {i}/{total_urls} URLs processed")
                    else:
                        failed_urls.add(url)
                    
                    # Small delay between requests
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Failed to process URL {url}: {e}")
                    failed_urls.add(url)
                    continue
            
            browser_context.close()
        
        # Save final results
        if all_parts_data:
            df = pd.DataFrame(all_parts_data)
            df.to_csv(output_file, index=False)
            logger.info(f"Final data saved to {output_file}")
        
        # Save failed URLs if any
        if failed_urls:
            failed_file = "failed_urls.txt"
            with open(failed_file, 'w') as f:
                for url in failed_urls:
                    f.write(f"{url}\n")
            logger.warning(f"Failed URLs saved to {failed_file}")
        
        # Print summary
        logger.info(f"""
        Scraping Summary:
        ----------------
        Total URLs: {total_urls}
        Successfully scraped: {len(successful_urls)}
        Failed: {len(failed_urls)}
        Total parts collected: {len(all_parts_data)}
        Output file: {output_file}
        """)
        
    except Exception as e:
        logger.error(f"Critical error in main process: {e}")
        raise

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")