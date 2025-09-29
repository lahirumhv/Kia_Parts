import re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import random

def generate_kia_parts_links(input_url):
    """
    Generate a list of Kia parts category links from a base model URL.
    
    Args:
        input_url (str): The base URL like 'https://parts.kia.com/Kia_2024_Sorento.html'
    
    Returns:
        list: List of category URLs
    """
    # Validate the input URL format
    if not input_url.startswith('https://parts.kia.com/Kia_'):
        raise ValueError("Invalid Kia parts URL format")
    
    # Extract the base model identifier (e.g., "Kia_2024_Sorento")
    match = re.search(r'https://parts\.kia\.com/(Kia_[^\.]+)\.html', input_url)
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
    category_links = []
    for category in categories:
        category_url = f"https://parts.kia.com/{base_model}/{category}.html"
        category_links.append(category_url)
    
    return category_links

def extract_assembly_urls(page_content):
    """
    Extract assembly URLs from page HTML content using BeautifulSoup.
    
    Args:
        page_content (str): HTML content of the page
    
    Returns:
        list: List of assembly URLs
    """
    soup = BeautifulSoup(page_content, 'html.parser')
    assembly_cards = soup.find_all('div', class_='assemblyCard')
    
    urls = []
    for card in assembly_cards:
        link = card.find('a', class_='assemblyCardLink')
        if link and link.get('href'):
            full_url = f"https://parts.kia.com{link['href']}"
            urls.append(full_url)
    
    return urls

def scrape_category_pages(category_links):
    """
    Visit each category page and extract assembly URLs using Playwright.
    
    Args:
        category_links (list): List of category URLs to scrape
    
    Returns:
        list: Combined list of all assembly URLs
    """
    all_assembly_urls = []
    
    with sync_playwright() as p:
        browser_context = p.chromium.launch_persistent_context(
            user_data_dir=".pw_user",
            headless=False,
            viewport={'width': 1920, 'height': 1080}
        )
        
        try:
            page = browser_context.new_page()
            
            for category_url in category_links:
                print(f"Scraping category: {category_url}")
                
                try:
                    # Navigate to category page
                    response = page.goto(
                        category_url,
                        timeout=60000,
                        wait_until="networkidle"
                    )
                    
                    if response.status == 200:
                        # Wait for assembly cards to load
                        page.wait_for_selector("div.assemblyCard", timeout=30000)
                        
                        # Extract URLs from the page
                        content = page.content()
                        assembly_urls = extract_assembly_urls(content)
                        all_assembly_urls.extend(assembly_urls)
                        
                        print(f"Found {len(assembly_urls)} assembly URLs")
                        
                        # Random delay between requests
                        time.sleep(random.uniform(2, 4))
                    else:
                        print(f"Failed to load page: {response.status}")
                
                except Exception as e:
                    print(f"Error processing category {category_url}: {str(e)}")
                    continue
            
        finally:
            browser_context.close()
    
    return all_assembly_urls

# Modified example usage
if __name__ == "__main__":
    input_url = "https://parts.kia.com/Kia_2024_Sorento.html"
    
    # Generate category links
    print("Generating category links...")
    category_links = generate_kia_parts_links(input_url)
    print(f"Found {len(category_links)} categories")
    
    # Scrape assembly URLs from each category
    print("\nScraping assembly URLs from categories...")
    assembly_urls = scrape_category_pages(category_links)
    
    # Print results
    print(f"\nTotal assembly URLs found: {len(assembly_urls)}")
    print("\nAssembly URLs:")
    for url in assembly_urls:
        print(url)
    
    # Optionally save to file
    with open('assembly_urls.txt', 'w') as f:
        for url in assembly_urls:
            f.write(f"{url}\n")
    print("\nURLs saved to assembly_urls.txt")

