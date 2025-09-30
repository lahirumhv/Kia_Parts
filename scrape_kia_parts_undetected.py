import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
import os
import random
from datetime import datetime
from typing import List, Dict, Optional
import json

# Create output directory if it doesn't exist
output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(output_dir, exist_ok=True)

# Set up logging
log_filename = os.path.join(output_dir, f"kia_parts_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
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

def setup_driver():
    """Initialize undetected-chromedriver with anti-detection measures."""
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    
    # Add random user agent and other headers to appear more human-like
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    driver = uc.Chrome(options=options)
    driver.set_window_size(1920, 1080)  # Full HD resolution
    return driver

def scrape_parts_from_page(driver, url: str, wait_time: int = 30) -> List[Dict]:
    """Scrape parts data from a single page using Selenium with undetected-chromedriver."""
    parts_data = []
    try:
        logger.info(f"Navigating to {url}")
        driver.get(url)
        
        # Wait for the main content to load
        wait = WebDriverWait(driver, wait_time)
        parts_elements = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.assemblyProdDetails"))
        )
        
        # Get assembly name if available
        assembly_name = ""
        try:
            breadcrumb = driver.find_element(By.CSS_SELECTOR, "ol.breadcrumb")
            crumbs = breadcrumb.find_elements(By.TAG_NAME, "li")
            if crumbs:
                assembly_name = crumbs[-1].text.strip()
        except Exception as e:
            logger.warning(f"Could not get assembly name: {e}")
        
        # Parse the page with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")
        parts = soup.find_all("li", class_="assemblyProdDetails")
        
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
        
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return parts_data

def main():
    urls_file = "assembly_urls.txt"
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f"kia_parts_data_{timestamp}.csv")
    compressed_file = os.path.join(output_dir, f"kia_parts_compressed_{timestamp}.csv")
    all_parts_data = []
    successful_urls = set()
    failed_urls = set()
    
    try:
        urls = read_assembly_urls(urls_file)
        total_urls = len(urls)
        
        driver = setup_driver()
        
        try:
            # Process each URL
            for i, url in enumerate(urls, 1):
                try:
                    logger.info(f"Processing URL {i}/{total_urls}")
                    parts_data = scrape_parts_from_page(driver, url)
                    
                    if parts_data:
                        all_parts_data.extend(parts_data)
                        successful_urls.add(url)
                        
                        # Save progress periodically (every 5 URLs)
                        if i % 5 == 0:
                            df = pd.DataFrame(all_parts_data)
                            df.to_csv(output_file, index=False)
                            # Also save the compressed version
                            compressed_df = df[['Assembly', 'Part Name', 'Part Number']].copy()
                            compressed_df.to_csv(compressed_file, index=False)
                            logger.info(f"Progress saved: {i}/{total_urls} URLs processed")
                    else:
                        failed_urls.add(url)
                        logger.warning(f"No data scraped from {url}")
                    
                    # Random delay between requests (3-7 seconds)
                    delay = 3 + random.random() * 4
                    time.sleep(delay)
                    
                except Exception as e:
                    logger.error(f"Failed to process URL {url}: {e}")
                    failed_urls.add(url)
                    continue
                
        finally:
            driver.quit()
        
        # Save final results
        if all_parts_data:
            # Save full data to CSV
            df = pd.DataFrame(all_parts_data)
            df.to_csv(output_file, index=False)
            logger.info(f"Final data saved to {output_file}")
            
            # Save compressed version with only Assembly, Part Name, and Part Number
            compressed_df = df[['Assembly', 'Part Name', 'Part Number']].copy()
            compressed_df.to_csv(compressed_file, index=False)
            logger.info(f"Compressed data saved to {compressed_file}")
            
            # Also save as JSON for backup
            json_file = os.path.join(output_dir, os.path.basename(output_file).replace('.csv', '.json'))
            with open(json_file, 'w') as f:
                json.dump(all_parts_data, f, indent=4)
            logger.info(f"Backup JSON saved to {json_file}")
        
        # Save failed URLs if any
        if failed_urls:
            failed_file = os.path.join(output_dir, "failed_urls.txt")
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
        Output CSV: {output_file}
        Output JSON: {json_file if all_parts_data else 'N/A'}
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