from typing import Mapping, Any

from elasticsearch import Elasticsearch

def index_apartment_to_elastic(apartment_data, es_index="apartments"):
    """
    Indexes a single apartment record into Elasticsearch.
    """
    es = Elasticsearch("http://localhost:9200")  # Adjust host/port as needed

    # If you're using Elasticsearch 8.x, you can do:
    # es.index(index=es_index, id=apartment_data["id"], document=apartment_data)

    # If you're on older versions, do:
    es.index(index=es_index, id=apartment_data["id"], body=apartment_data)

    print(f"Apartment {apartment_data['id']} indexed into '{es_index}' index.")

def search(index: str, body: Mapping[str, Any] | None):
    """
    Search for documents in the specified index.
    """
    es = Elasticsearch("http://localhost:9200")
    try:
        return es.search(index=index.lower(), body=body)
    except Exception as e:
        print(f"Error searching index '{index}': {e.__class__}\n{e}")