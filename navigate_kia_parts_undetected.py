import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import os
import re
import random

class KiaPartsScraper:
    def __init__(self):
        self.setup_driver()
    
    def setup_driver(self):
        """Initialize the undetected-chromedriver with anti-detection measures"""
        options = uc.ChromeOptions()
        options.add_argument('--start-maximized')
        
        # Create user data directory if it doesn't exist
        user_data_dir = os.path.abspath(".pw_user_undetected")
        os.makedirs(user_data_dir, exist_ok=True)
        
        # Initialize undetected-chromedriver with persistent profile
        self.driver = uc.Chrome(
            options=options,
            user_data_dir=user_data_dir,
            headless=False  # Headless mode often doesn't work well with Cloudflare
        )
        
        self.wait = WebDriverWait(self.driver, 30)

    def search_vin(self, vin):
        """Search for a vehicle by VIN and return the model URL"""
        try:
            print("Navigating to parts.kia.com...")
            self.driver.get("https://parts.kia.com")
            
            # Wait for and locate the VIN input field
            print("Entering VIN number...")
            vin_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "vinInput"))
            )
            vin_input.send_keys(vin)
            
            # Find and click the search button
            print("Clicking search button...")
            search_button = self.wait.until(
                EC.element_to_be_clickable((By.ID, "vin-input-button-submit"))
            )
            search_button.click()
            
            # Wait for the results link to appear
            print("Waiting for results...")
            result_link = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "vin-result-link"))
            )
            
            # Get the href attribute
            model_url = result_link.get_attribute('href')
            print(f"\nGenerated Model URL: {model_url}")
            
            return model_url
            
        except Exception as e:
            print(f"Error in VIN search: {str(e)}")
            return None

    def generate_category_links(self, model_url):
        """Generate category links from the model URL"""
        try:
            # Validate the input URL format
            if not model_url.startswith('https://parts.kia.com/Kia_'):
                raise ValueError("Invalid Kia parts URL format")
            
            # Extract the base model identifier
            match = re.search(r'https://parts\.kia\.com/(Kia_[^\.]+)\.html', model_url)
            if not match:
                raise ValueError("Could not extract model identifier from URL")
            
            base_model = match.group(1)
            
            # Define the category suffixes
            categories = [
                "Body-and-Trim",
                "Chassis", 
                "Electric",
                "Engine-and-Motor",
                "Transmission"
            ]
            
            # Generate the full URLs
            return [f"https://parts.kia.com/{base_model}/{category}.html" 
                   for category in categories]
            
        except Exception as e:
            print(f"Error generating category links: {str(e)}")
            return []

    def extract_assembly_urls(self, page_source):
        """Extract assembly URLs from page source using BeautifulSoup"""
        try:
            soup = BeautifulSoup(page_source, 'html.parser')
            assembly_cards = soup.find_all('div', class_='assemblyCard')
            
            urls = []
            for card in assembly_cards:
                link = card.find('a', class_='assemblyCardLink')
                if link and link.get('href'):
                    full_url = f"https://parts.kia.com{link['href']}"
                    urls.append(full_url)
            
            return urls
            
        except Exception as e:
            print(f"Error extracting assembly URLs: {str(e)}")
            return []

    def scrape_category_pages(self, category_links):
        """Visit each category page and extract assembly URLs"""
        all_assembly_urls = []
        
        for category_url in category_links:
            print(f"\nScraping category: {category_url}")
            
            try:
                # Navigate to category page
                self.driver.get(category_url)
                
                # Wait for assembly cards to load
                self.wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "assemblyCard"))
                )
                
                # Extract URLs from the page
                assembly_urls = self.extract_assembly_urls(self.driver.page_source)
                all_assembly_urls.extend(assembly_urls)
                
                print(f"Found {len(assembly_urls)} assembly URLs")
                
                # Random delay between requests
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"Error processing category {category_url}: {str(e)}")
                continue
        
        return all_assembly_urls

    def close(self):
        """Close the browser"""
        try:
            self.driver.quit()
        except:
            pass

def main():
    scraper = KiaPartsScraper()
    
    try:
        # You can either start with a VIN search
        vin = "KNARH81BWR5297431"  # Example VIN
        model_url = scraper.search_vin(vin)
        
        # Or directly use a model URL
        # model_url = "https://parts.kia.com/Kia_2024_Sorento.html"
        
        if model_url:
            # Generate category links
            print("\nGenerating category links...")
            category_links = scraper.generate_category_links(model_url)
            print(f"Found {len(category_links)} categories")
            
            # Scrape assembly URLs from each category
            print("\nScraping assembly URLs from categories...")
            assembly_urls = scraper.scrape_category_pages(category_links)
            
            # Print results
            print(f"\nTotal assembly URLs found: {len(assembly_urls)}")
            
            # Save to file
            with open('assembly_urls.txt', 'w') as f:
                for url in assembly_urls:
                    f.write(f"{url}\n")
            print("\nURLs saved to assembly_urls.txt")
    
    finally:
        scraper.close()

if __name__ == "__main__":
    main()