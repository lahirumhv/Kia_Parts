import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import time


url = "https://parts.kia.com/a/Kia_2024_Sorento/_52022_12268602/WINDSHIELD-GLASS/AKMAPHY24_86-861.html?assemblySearchGuid=D9029FCD-1319-467D-8B51-6FBBD9FA14DE"

def get_partnum(url = url):
    parts_num = []
    driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(5)  # wait for the page to load

    soup = BeautifulSoup(driver.page_source, "html.parser")
    meta_tag = soup.find("meta", attrs={"id": "ctl00_metaKeywords"})

    if meta_tag:
        content_str = meta_tag["content"]
        parts_list = [item.strip() for item in content_str.split(",") if item.strip()]
        print(parts_list)
        return parts_list
        #print("Found content:", meta_tag["content"])
    else:
        print("Meta tag not found")

    driver.quit()
    
     
get_partnum(url = url)    

