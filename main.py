import streamlit as st
from sqlalchemy.dialects.postgresql import array
from streamlit import session_state

from scrape import scrape_website, extract_body_content, clean_body_content, split_dom_content, \
    get_apart_links_from_the_page, scrape_apartment
from parse import parse_with_ollama

st.title("Belgrade Apartment Web Scraper")


rl = st.text_input("Enter a website URL")

if st.button("Scrape 4zida.rs"):
    st.write("Scraping 4zida.rs")

    all_apart_links = []

    for page_number in range(1, 3):
        apart_links: array[str] = get_apart_links_from_the_page(page_number=page_number)
        print(apart_links)
        print(len(apart_links))
        unique_apart_links = list(set(apart_links))
        print(unique_apart_links)
        print(len(unique_apart_links))
        all_apart_links.append(unique_apart_links)

    first_apart = all_apart_links[0][0]
    print(f"First apart {first_apart}")
    scrape_apartment(first_apart)

    st.session_state.dom_content = all_apart_links
    with st.expander("View Apartments"):
        st.text_area("Apart links", all_apart_links, height=300)



if "dom_content" in session_state:
    parse_description = st.text_area("Describe what you want to parse")
    if st.button("Parse Content"):
        if parse_description:
            st.write("Parsing the content")

            dom_chunks = split_dom_content(st.session_state.dom_content)
            parsed_result = parse_with_ollama(dom_chunks, parse_description)
            st.write(parsed_result)