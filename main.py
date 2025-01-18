import streamlit as st
from sqlalchemy.dialects.postgresql import array
from streamlit import session_state

from elastic_repository import index_apartment_to_elastic
from parse_apart_llm import parse_apart_with_ollama
from scrape_4z import get_apart_links_from_the_page, scrape_apartment, LOCATION_BEOGRAD, DEAL_TYPE_RENT

st.title("Belgrade Apartment Web Scraper")

# Create tab objects
paged, specific_apart, tab3 = st.tabs(["4zida beograd by page", "4zida specific apart url checker", "Tab 3"])

MAX_PAGE = 3

# Add content to each tab
with paged:
    if st.button("Scrape 4zida.rs", key="scrape_all"):
        st.write("Scraping 4zida.rs")

        all_apart_links = []
        for page_number in range(1, MAX_PAGE):
            apart_links: array[str] = get_apart_links_from_the_page(page_number=page_number,
                                                                    location=LOCATION_BEOGRAD,
                                                                    deal_type=DEAL_TYPE_RENT)
            print(apart_links)
            print(len(apart_links))
            unique_apart_links = list(set(apart_links))
            print(unique_apart_links)
            print(len(unique_apart_links))
            all_apart_links.append(unique_apart_links)

        first_apart = all_apart_links[0][0]
        print(f"First apart {first_apart}")
        apartment = scrape_apartment(first_apart)

        index_apartment_to_elastic(apartment)

        st.session_state.dom_content = apartment
        with st.expander("View Apartments"):
            st.text_area("Apartments", apartment, height=300)

    if "dom_content" in session_state:
        if st.button("Parse Content with LLM", key="tab_1_llm_parse_btn"):
                st.write("Parsing the content")
                parsed_result = parse_apart_with_ollama(st.session_state.dom_content)
                st.write(parsed_result)

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

with tab3:
    st.write("Content for Tab 3")

