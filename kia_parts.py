import os
from navigate_kia_parts_undetected import KiaPartsScraper
from scrape_kia_parts_undetected import scrape_parts_from_page, setup_driver
import pandas as pd
import json
import logging
from datetime import datetime
import time
import random

def setup_logging(output_dir: str) -> logging.Logger:
    """Set up logging configuration."""
    log_filename = os.path.join(output_dir, f"kia_parts_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def create_vin_directory(vin: str) -> str:
    """Create directory structure for VIN and return the path."""
    # Create main output directory if it doesn't exist
    base_output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(base_output_dir, exist_ok=True)
    
    # Create VIN-specific directory
    vin_dir = os.path.join(base_output_dir, vin)
    os.makedirs(vin_dir, exist_ok=True)
    
    return vin_dir

def main():
    # Get VIN from user
    vin = input("Please enter the VIN number: ").strip()
    if not vin:
        print("VIN number is required.")
        return
    
    # Initialize KiaPartsScraper first to validate VIN
    logger = logging.getLogger(__name__)
    logger.info(f"Starting process for VIN: {vin}")
    
    try:
        # Step 1: Use KiaPartsScraper to get assembly URLs and validate VIN
        logger.info("Initializing KIA parts scraper...")
        link_scraper = KiaPartsScraper()
        
        try:
            # Search for VIN and get model URL
            logger.info("Searching for VIN...")
            model_url = link_scraper.search_vin(vin)
            
            # Only create directory if VIN is valid
            if not model_url:
                logger.error("Invalid VIN: Could not find vehicle with provided VIN")
                return
                
            # Create VIN-specific directory after validation
            output_dir = create_vin_directory(vin)
            
            # Set up file logging now that we have a valid directory
            logger = setup_logging(output_dir)
            logger.info(f"VIN validated successfully. Created output directory.")
            
            if not model_url:
                logger.error("Could not find vehicle with provided VIN")
                return
            
            # Generate and scrape category links
            logger.info("Generating category links...")
            category_links = link_scraper.generate_category_links(model_url)
            
            logger.info("Scraping assembly URLs...")
            assembly_urls = link_scraper.scrape_category_pages(category_links)
            
            # Save assembly URLs to VIN-specific directory
            urls_file = os.path.join(output_dir, "assembly_urls.txt")
            with open(urls_file, 'w') as f:
                for url in assembly_urls:
                    f.write(f"{url}\n")
            logger.info(f"Saved {len(assembly_urls)} assembly URLs to {urls_file}")
            
        finally:
            link_scraper.close()
        
        # Step 2: Use scraping functionality to get parts data
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(output_dir, f"kia_parts_data_{timestamp}.csv")
        compressed_file = os.path.join(output_dir, f"kia_parts_compressed_{timestamp}.csv")
        
        all_parts_data = []
        successful_urls = set()
        failed_urls = set()
        
        logger.info("Starting parts data scraping...")
        driver = setup_driver()
        
        try:
            # Process each assembly URL
            total_urls = len(assembly_urls)
            for i, url in enumerate(assembly_urls, 1):
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
            
            # Save compressed version
            compressed_df = df[['Assembly', 'Part Name', 'Part Number']].copy()
            compressed_df.to_csv(compressed_file, index=False)
            logger.info(f"Compressed data saved to {compressed_file}")
            
            # Save as JSON for backup
            json_file = os.path.join(output_dir, f"kia_parts_data_{timestamp}.json")
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
        VIN: {vin}
        Total URLs: {total_urls}
        Successfully scraped: {len(successful_urls)}
        Failed: {len(failed_urls)}
        Total parts collected: {len(all_parts_data)}
        Output directory: {output_dir}
        Output CSV: {output_file}
        Compressed CSV: {compressed_file}
        Output JSON: {json_file if all_parts_data else 'N/A'}
        """)
        
    except Exception as e:
        logger.error(f"Critical error in main process: {e}")
        raise

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
    except Exception as e:
        print(f"Fatal error: {e}")
