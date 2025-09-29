from playwright.sync_api import sync_playwright
import time

def search_vin():
    with sync_playwright() as p:
        # Launch browser with persistent context
        browser_context = p.chromium.launch_persistent_context(
            user_data_dir=".pw_user",
            headless=False,  # Set to False to see the automation
            viewport={'width': 1280, 'height': 800}
        )
        
        try:
            page = browser_context.new_page()
            
            # Navigate to the website
            print("Navigating to parts.kia.com...")
            page.goto("https://parts.kia.com", wait_until="networkidle")
            
            # Wait for the VIN input field and fill it
            print("Entering VIN number...")
            page.wait_for_selector("#vinInput")
            page.fill("#vinInput", "KNARH81BWR5297431")
            
            # Click the search button
            print("Clicking search button...")
            page.click("#vin-input-button-submit")
            
            # Wait for the results link to appear
            print("Waiting for results...")
            page.wait_for_selector(".vin-result-link")
            
            # Get the href attribute from the result link
            result_link = page.evaluate('() => document.querySelector(".vin-result-link").href')
            
            print("\nGenerated Link:")
            print(result_link)
            
            # Optional: wait a moment to see the result before closing
            time.sleep(2)
            
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            
        finally:
            browser_context.close()

if __name__ == "__main__":
    search_vin()