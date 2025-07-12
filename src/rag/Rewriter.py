from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

from langchain_community.llms import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

from config.llm_config import LLM_MODEL

model_id = LLM_MODEL  # ou qualquer modelo LLaMA compatível

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id)

pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=4000)

re_write_llm = HuggingFacePipeline(pipeline=pipe)

import os
from dotenv import load_dotenv

query_rewrite_template = """You are an AI assistant tasked with reformulating user queries to improve retrieval in a RAG system. 
Given the original query, rewrite it to be more specific, detailed, and likely to retrieve relevant information.

Original query: {original_query}

Rewritten query:"""

query_rewrite_prompt = PromptTemplate(
    input_variables=["original_query"],
    template=query_rewrite_template
)

# Create an LLMChain for query rewriting
query_rewriter = query_rewrite_prompt | re_write_llm


def rewrite_query(original_query):
    """
    Rewrite the original query to improve retrieval.

    Args:
    original_query (str): The original user query

    Returns:
    str: The rewritten query
    """
    response = query_rewriter.invoke(original_query)
    return response.content

def main():
    query = "Em que disciplina e em que semestre ou ano é abordado o conceito de conjunto numérico?"
    requery = rewrite_query(query)

    print(query)
    print(requery)

if __name__ == "__main__":
    main()