from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import time

def scrape_kia_parts():
    with sync_playwright() as p:
        # Launch browser with persistent context
        browser_context = p.chromium.launch_persistent_context(
            user_data_dir=".pw_user",
            headless=False,  # Set to True once everything works
            viewport={'width': 1280, 'height': 800}
        )
        
        page = browser_context.new_page()
        
        # Navigate to the page
        url = "https://parts.kia.com/a/Kia_2024_Sorento/_93811_12259916/ACCELERATOR-PEDAL/AKMAPHY24_32-327.html?assemblySearchGuid=0E5330FF-889C-4B09-97EB-2FE549D9C61D"
        page.goto(url, wait_until="networkidle")
        
        # Wait for the content to load
        page.wait_for_selector("li.assemblyProdDetails", timeout=30000)
        
        # Get the page content
        content = page.content()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(content, "html.parser")
        parts_data = []
        
        # Select all <li> elements with class containing "assemblyProdDetails"
        parts = soup.find_all("li", class_="assemblyProdDetails")
        
        for part in parts:
            # Part Name
            name_tag = part.find("div", class_="assemblyProductDescription")
            part_name = name_tag.get_text(strip=True) if name_tag else None
            
            # Part Number
            number_tag = part.find("a", class_="btn btn-tertiary")
            part_number = number_tag.get_text(strip=True) if number_tag else None
            
            # Price
            price_tag = part.find("div", class_="money-4")
            part_price = price_tag.get_text(strip=True).replace("(Current price)", "") if price_tag else None
            
            # Quantity
            qty_tag = part.find("input", {"class": "form-control input-sm text-center"})
            part_qty = qty_tag["value"] if qty_tag else None
            
            # Product URL
            product_url = None
            if number_tag and number_tag.get("href"):
                product_url = "https://parts.kia.com" + number_tag["href"]
            
            # Store result
            parts_data.append({
                "Part Name": part_name,
                "Part Number": part_number,
                "Price": part_price,
                "Quantity": part_qty,
                "Product URL": product_url
            })
        
        # Save results to a JSON file
        with open('kia_parts.json', 'w') as f:
            json.dump(parts_data, f, indent=4)
            
        print(f"Scraped {len(parts_data)} parts. Data saved to kia_parts.json")
        
        # Close the browser
        browser_context.close()

if __name__ == "__main__":
    scrape_kia_parts()
