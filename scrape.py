from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import selenium.webdriver as webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service
import requests
import time
from requests.exceptions import ProxyError, HTTPError

import re

from selenium.webdriver.support.wait import WebDriverWait

CHROMEDRIVER_EXE = "./chromedriver.exe"

pattern = re.compile(r'^.*[A-Za-z0-9]{24}$')

# Fake browser-like headers
BASE_HEADERS = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "accept": "application/json",
    "accept-language": "en-US",
    "accept-encoding": "gzip, deflate, br, zstd",
}

BASE_URL = "https://www.4zida.rs"

LOCATION = "/beograd"

TYPE_RENT = "/izdavanje-stanova"

def get_apart_links_from_the_page(page_number):
    test_url = f"{BASE_URL}{TYPE_RENT}{LOCATION}/jednosoban?struktura=jednoiposoban&struktura=garsonjera&strana={page_number}"
    print("Extracting links from the page {}", test_url)
    max_retries = 5
    backoff_factor = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(test_url, headers=BASE_HEADERS)#/proxies can be enabled if needed/, proxies=proxies)
            print(response)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            apart_links = []
            all_links = soup.find_all('a', href=True)
            print(all_links)

            for a_tag in all_links:
                print(a_tag['href'])
                if pattern.match(a_tag['href']):
                    apart_links.append(a_tag['href'])

            return apart_links
        except ProxyError as e:
            wait_time = backoff_factor ** attempt
            print(f"Proxy error: {e}. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        except HTTPError as e:
            if e.response.status_code == 412:
                print(f"Precondition Failed (412): {e}. Skipping URL.")
                break
            wait_time = backoff_factor ** attempt
            print(f"HTTP error: {e}. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        except Exception as e:
            print(f"Failed to get product links for query: {test_url}. Error: {e}")
            break

def scrape_apartment(apart_link):
    apart_url = f"{BASE_URL}{apart_link}"
    response = requests.get(apart_url, headers=BASE_HEADERS)#/proxies can be enabled if needed/, proxies=proxies)
    print(response)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    apartment = {}
    apartment["id"] = apart_link.rstrip('/').split('/')[-1]
    apartment["link"] = apart_link
    apartment["price"] = scrape_price(soup)
    apartment["telephone_number"] = scrape_telephone_number(apart_url)
    apartment["image_urls"] = scrape_image_urls(soup)
    apartment["native_id"] = scrape_native_id(soup)  # like sifra oglasa
    print(apartment)

def scrape_native_id(soup):
    # Find <span class="font-medium"> elements whose text begins with "4zida"
    spans = soup.find_all(
        "span",
        class_="font-medium",
        string=re.compile(r"^4zida")
    )

    for span in spans:
        # Get the full text (e.g., "4zida-4759")
        zid_id = span.get_text(strip=True)
        print("Found ID:", zid_id)
        return zid_id

def scrape_image_urls(soup):
    # Find all <img> tags
    img_tags = soup.find_all('img')

    # Extract 'src' from each <img>
    image_urls = []
    for img in img_tags:
        src = img.get('src')
        if src:
            image_urls.append(src)

    return image_urls

def scrape_price(soup):
    p_tags_with_test_data = soup.find_all('p', attrs={'test-data': 'ad-price'})
    print(p_tags_with_test_data)
    price = p_tags_with_test_data[0].get_text()
    print(price)
    return price


def scrape_telephone_number(apart_url):
    print(f"scrape_telephone_number - {apart_url}")

    chrome_driver_path = CHROMEDRIVER_EXE
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)

    try:
        driver.get(apart_url)
        print("Page loaded...")
        # Wait until the span is present on the page
        wait = WebDriverWait(driver, 10)  # 10-second timeout
        link_element = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, '//button[contains(., "Prikaži")]')
            )
        )
        # Click the span
        link_element.click()
        print("Clicked 'Prikaži broj telefona'...")

        # Wait for the phone number link to appear in the popup
        # Here, we look for an <a> that starts with href="tel:"
        phone_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href^="tel:"]'))
        )

        # Extract the text directly from the newly appeared <a> element
        phone_number_text = phone_element.text
        print("Phone number text:", phone_number_text)
        return phone_number_text
    finally:
        driver.quit()


def scrape_website(website):
    print("Launching chrome browser...")

    chrome_driver_path = "./chromedriver.exe"
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)

    try:
        driver.get(website)
        print("Page loaded...")

        html = driver.page_source
        return html
    finally:
        driver.quit()


def extract_body_content(html_body):
    soup = BeautifulSoup(html_body, "html.parser")
    body_content = soup.body
    if body_content:
        return str(body_content)
    return ""

def clean_body_content(body_content):
    soup = BeautifulSoup(body_content, "html.parser")

    for script_or_style in soup(['script', 'style']):
        script_or_style.extract()

    cleaned_content = soup.get_text(separator="\n")
    cleaned_content = "\n".join(
        line.strip() for line in cleaned_content.splitlines() if line.strip()
    )

    return cleaned_content

def split_dom_content(dom_content, max_length=6000):
    return [
        dom_content[i: i+ max_length] for i in range(0, len(dom_content), max_length)
    ]