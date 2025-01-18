from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

template = (
    "You are tasked with extracting specific information from the following text content: {apartment_descriptor}. "
    "Please follow these instructions carefully: \n\n"
    "1. Provide the human readable summary of apartment descriptor"
)


model = OllamaLLM(model="llama3.1")

def parse_apart_with_ollama(apart):
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model

    response = chain.invoke(
        {"apartment_descriptor": apart}
    )

    return response