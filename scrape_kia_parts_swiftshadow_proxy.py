from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from swiftshadow.classes import ProxyInterface
import json
import time

def scrape_kia_parts():
    # Initialize ProxyInterface with auto-rotation
    proxy_manager = ProxyInterface(
        protocol="http",  # or "https" if needed
        autoRotate=True,
        maxProxies=20,
        countries=["US"]  # Add specific countries if needed
    )
    
    with sync_playwright() as p:
        # Launch browser with persistent context and proxy
        try:
            current_proxy = proxy_manager.get()
            proxy_url = current_proxy.as_string()
            print(f"Using proxy: {proxy_url}")
            
            browser_context = p.chromium.launch_persistent_context(
                user_data_dir=".pw_user",
                headless=False,
                viewport={'width': 1280, 'height': 800},
                proxy={
                    "server": proxy_url
                }
            )
            
            page = browser_context.new_page()
            
            # Set headers
            page.set_extra_http_headers({
                'Accept-Language': 'en-US,en;q=0.9',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
            })
            
            # Navigate to the page with retry logic
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    print(f"Attempt {attempt + 1} of {max_retries}")
                    response = page.goto(
                        "https://parts.kia.com/a/Kia_2024_Sorento/_93811_12259916/ACCELERATOR-PEDAL/AKMAPHY24_32-327.html?assemblySearchGuid=0E5330FF-889C-4B09-97EB-2FE549D9C61D",
                        timeout=60000,
                        wait_until="networkidle"
                    )
                    
                    if response.status == 200:
                        break
                    else:
                        print(f"Got status code: {response.status}, rotating proxy...")
                        proxy_manager.rotate()
                        current_proxy = proxy_manager.get()
                        proxy_url = current_proxy.as_string()
                        print(f"New proxy: {proxy_url}")
                        
                except Exception as e:
                    print(f"Error occurred: {str(e)}")
                    if attempt < max_retries - 1:
                        proxy_manager.rotate()
                        current_proxy = proxy_manager.get()
                        proxy_url = current_proxy.as_string()
                        print(f"Rotating to new proxy: {proxy_url}")
                        time.sleep(2)
                    else:
                        raise Exception("Max retries reached")
            
            # Wait for content
            page.wait_for_selector("li.assemblyProdDetails", timeout=30000)
            
            # Get the page content
            content = page.content()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, "html.parser")
            parts_data = []
            
            # Rest of your existing scraping code...
            parts = soup.find_all("li", class_="assemblyProdDetails")
            
            for part in parts:
                # Your existing part extraction code...
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
            
            # Save results
            with open('kia_parts.json', 'w') as f:
                json.dump(parts_data, f, indent=4)
                
            print(f"Scraped {len(parts_data)} parts. Data saved to kia_parts.json")
            
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        
        finally:
            browser_context.close()

if __name__ == "__main__":
    scrape_kia_parts()