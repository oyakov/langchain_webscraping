import streamlit as st
from sqlalchemy.dialects.postgresql import array
from streamlit import session_state
import time
from elastic_repository import index_apartment_to_elastic, search
from parse_apart_llm import parse_apart_with_ollama
from scrape_4z import get_apart_links_from_the_page, scrape_apartment, LOCATION_BEOGRAD, DEAL_TYPE_RENT

st.title("Belgrade Apartment Web Scraper")

# Create tab objects
paged, specific_apart, apart_query = st.tabs(["4zida beograd by page", "4zida specific apart url checker", "Apart query"])

MAX_PAGE = 10

# Add content to each tab
with paged:
    if st.button("Scrape 4zida.rs", key="scrape_all"):
        st.write("Scraping 4zida.rs")

        all_apart_links = []
        for page_number in range(1, MAX_PAGE):
            print(f"Scraping page {page_number}")
            try:
                apart_links: array[str] = get_apart_links_from_the_page(page_number=page_number,
                                                                        location=LOCATION_BEOGRAD,
                                                                        deal_type=DEAL_TYPE_RENT)
                print(f"There were {len(apart_links)} total apart links scraped")
                unique_apart_links = list(set(apart_links))
                print(f"There were {len(unique_apart_links)} unique apart links")
                all_apart_links.extend(unique_apart_links)
                print(f"Total apart size after scraping page {page_number} is {len(all_apart_links)}")
                print("Waiting 5 seconds")
                time.sleep(5)
            except Exception as e:
                print("Error getting links from the page: {}", e)
                break

        print(f"Apartment link scraping is over, current size is {len(all_apart_links)} deduplicate the list again")
        all_unique_apart_links = list(set(all_apart_links))
        print(f"Scraped total {len(all_unique_apart_links)} unique apartment links, now scraping individual apartments")


        for apart_page in range(0, len(all_unique_apart_links)):
            apart = all_unique_apart_links[apart_page]
            print(f"Processing apart {apart}")
            apartment = scrape_apartment(apart)
            print("Apartment scraped, adding to elastic")
            index_apartment_to_elastic(apartment)
            print("Apartment added to elastic, waiting before making next request")
            time.sleep(5)

with specific_apart:
    rl = st.text_input("Enter a 4zida.rs apart URL", key="spec_url")

    if st.button("Scrape 4zida.rs", key="scrape_url"):
        st.write("Scraping 4zida.rs apart link")

        apartment = scrape_apartment(rl)

        index_apartment_to_elastic(apartment)

        st.session_state.dom_content = apartment
        with st.expander("View Apartments"):
            st.text_area("Apartments", apartment, height=300)

    if "dom_content" in session_state:
        if st.button("Parse Content with LLM", key="tab_2_llm_parse_btn"):
                st.write("Parsing the content")
                parsed_result = parse_apart_with_ollama(st.session_state.dom_content)
                st.write(parsed_result)

with apart_query:
    if st.button("Query ES", key="query_es"):
        st.write("Querying ES")
        exist_apart = search("apartments", {})
        print(exist_apart)