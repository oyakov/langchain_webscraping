import re
import time

import dateparser
import requests
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from requests.exceptions import ProxyError, HTTPError
from selenium.common import ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from custom_parser import parse_serbian_relative_time

CHROMEDRIVER_EXE = "./chromedriver.exe"

# Fake browser-like headers
BASE_HEADERS = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "accept": "application/json",
    "accept-language": "en-US",
    "accept-encoding": "gzip, deflate, br, zstd",
}

BASE_URL = "https://www.4zida.rs"

LOCATION_BEOGRAD = "/beograd"

LOCATIONS = [LOCATION_BEOGRAD]

DEAL_TYPE_RENT = "/izdavanje-stanova"

DEAL_TYPES = [DEAL_TYPE_RENT]

def get_apart_links_from_the_page(page_number, location, deal_type):
    search_url = f"{BASE_URL}{deal_type}{location}/jednosoban?struktura=jednoiposoban&struktura=garsonjera&strana={page_number}&sortiranje=najnoviji"
    print(f"Extracting links from the search page {search_url}")
    max_retries = 5
    backoff_factor = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(search_url, headers=BASE_HEADERS) #/proxies can be enabled if needed/, proxies=proxies)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            apart_links = []
            all_links = soup.find_all('a', href=True)
            apart_url_pattern = re.compile(r'^.*[A-Za-z0-9]{24}$') # ends with 24 symbol alphanumeric id
            for a_tag in all_links:
                if apart_url_pattern.match(a_tag['href']):
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
            print(f"Failed to get product links for query: {search_url}. Error: {e}")
            break

def scrape_apartment(apart_link):
    print(f"Scraping apartment link {apart_link}")
    apart_url = f"{BASE_URL}{apart_link}"
    print(f"Full apart URL: {apart_url}")
    response = requests.get(apart_url, headers=BASE_HEADERS)#/proxies can be enabled if needed/, proxies=proxies)
    print(response)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    apartment = {}
    apartment["id"] = apart_link.rstrip('/').split('/')[-1]
    apartment["link"] = f"{BASE_URL}{apart_link}"
    apartment["header"] = scrape_header(soup)
    apartment["price"] = scrape_price(soup)
    apartment["contact_info"] = scrape_contact_info(apart_url)
    apartment["image_urls"] = scrape_image_urls(soup)
    apartment["native_id"] = scrape_native_id(soup)  # like sifra oglasa on 4zida.rs
    apartment["created_ago"] = scrape_created_ago(soup)
    apartment["features"] = scrape_features(soup)
    print(apartment)
    return apartment

def scrape_created_ago(soup):
    # Find <span class="font-medium"> elements whose text begins with "Oglas ažuriran:"
    spans = soup.find_all(
        "span",
        class_="text-gray-600"
    )

    for span in spans:
        print(span)
        # Get the full text (e.g., "Oglas ažuriran")
        text = span.get_text(strip=True)
        if text.startswith("Oglas ažuriran"):
            cre_ago = text.split(":")[1]
            print("Found Created Ago:", cre_ago)
            dt = parse_serbian_relative_time(cre_ago)  # Force Serbian language
            print(dt)
            return dt

def scrape_features(soup):
    features = []
    # 1. Find the <strong> with text "O stanu"
    strong_tag = soup.find("strong", text="O stanu")
    if strong_tag:
        # 2. Go up to the parent <section>
        section_tag = strong_tag.find_parent("section")
        if section_tag:
            # 3. Find the <ul> (or directly all the <li> tags)
            ul_tag = section_tag.find("ul")
            if ul_tag:
                li_tags = ul_tag.find_all("li")
                for li in li_tags:
                    # 4. Each <li> has a <span>; get its text
                    span = li.find("span")
                    if span:
                        item_text = span.get_text(strip=True)
                        print(item_text)
                        features.append(item_text)

    return features

def scrape_header(soup):
    # Find all <h1> elements with these exact classes
    h1_tags = soup.find_all('h1', class_='text-2xl font-medium leading-none')
    return h1_tags[0].get_text()

def scrape_native_id(soup):
    # Find <span class="font-medium"> elements whose text begins with "4zida"
    spans = soup.find_all(
        "span",
        class_="font-medium"
    )

    for span in spans:
        print(span)
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

    return [url for url in image_urls if url.endswith("webp#1920")]

def scrape_price(soup):
    p_tags_with_test_data = soup.find_all('p', attrs={'test-data': 'ad-price'})
    print(p_tags_with_test_data)
    price = p_tags_with_test_data[0].get_text()
    print(price)
    return price


def scrape_contact_info(apart_url):
    print(f"scrape_contact_info - {apart_url}")

    # Need to click button so use Selenium here
    # chrome_driver_path = CHROMEDRIVER_EXE
    # options = webdriver.ChromeOptions()
    # options.add_argument('--ignore-certificate-errors')
    # options.add_argument('--headless')  # Run in headless mode
    # driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)

    options = uc.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--headless')  # Run in headless mode
    driver = uc.Chrome(headless=True, options=options)

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
        time.sleep(2)
        # Wait for the phone number link to appear in the popup
        # Here, we look for an <a> that starts with href="tel:"
        phone_elements = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[href^="tel:"]'))
        )

        # Extract text from each phone link
        phone_numbers = []
        for elem in phone_elements:
            text = elem.text.strip()
            if text:
                phone_numbers.append(text)
        print("Phone numbers:", phone_numbers)

        # Wait for the <span class="font-medium text-primary-500">Name</span> and get the text
        name_element = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'span.font-medium.text-primary-500')
            )
        )
        name_text = name_element.text.strip()
        print("Name:", name_text)

        # Return the scraped info
        return {"phone_numbers": phone_numbers, "name": name_text}
    except ElementClickInterceptedException as e:
        return ["Click intercepted error"]
    except Exception as exc:
        return ["Error scraping phone number"]
    finally:
        driver.quit()


def scrape_website(website):
    print("Launching chrome browser...")

    chrome_driver_path = "./chromedriver.exe"
    options = uc.ChromeOptions()
    driver = uc.Chrome(headless=True, options=options)

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