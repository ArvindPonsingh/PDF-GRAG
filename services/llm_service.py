# services/llm_service.py

from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from config import GROQ_API_KEY, LLM_MODEL_GRAPH_EXTRACTION, LLM_MODEL_RAG

# Removed temporary print statements and try-except for initialization
llm_rag = ChatGroq(api_key=GROQ_API_KEY, model_name=LLM_MODEL_RAG, temperature=0.2)
llm_triplet_extraction = ChatGroq(api_key=GROQ_API_KEY, model_name=LLM_MODEL_GRAPH_EXTRACTION, temperature=0.5)

def get_rag_response(question, context):
    # Removed temporary None check
    rag_prompt = f"""
You are a helpful assistant. Answer the user's question based on the provided context from the document.
If you do not have enough context, just politely say you cannot answer.

Context:
{context}

Question:
{question}

Answer:
"""
    response = llm_rag.invoke(rag_prompt)
    return response.content