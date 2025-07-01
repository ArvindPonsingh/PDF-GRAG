import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from neo4j import GraphDatabase
import json
from dotenv import load_dotenv
import os
import re

load_dotenv()

# --- Configuration ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NEO4J_URI = "bolt://localhost:7687" 
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "12345678"

llm = ChatGroq(api_key=GROQ_API_KEY, model_name="llama-3.3-70b-versatile", temperature=0.2)
llm2 = ChatGroq(api_key=GROQ_API_KEY, model_name="qwen/qwen3-32b", temperature=0.5)  # for RAG-style chat

neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# --- Helper Functions ---
def extract_text_from_pdfs(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        reader = PdfReader(pdf)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text

def chunk_text(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=200)
    return splitter.split_text(text)

def extract_triplets(text_chunk):
    prompt = PromptTemplate(
        input_variables=["chunk"],
        template="""
        you are an expert in extracting triplets from text.
        Your task is to extract all subject-predicate-object triplets from the provided text chunk.
        Each triplet should be represented as a JSON object with keys "subject", "predicate", and "object".
        Here is the provided    

        Text:
        {chunk}

        Output as a JSON array like:
        [
          {{"subject": "...", "predicate": "...", "object": "..."}},
          ...
        ]

        ⚠️ Return only a JSON array. Do NOT include explanations or commentary.

        Also try to form relations among the triplets, e.g., if a subject appears in multiple triplets, try to use the same subject name.
        this makes sure that the triplets are consistent and can be used to build a knowledge graph and not too much noise is generated.
        this is important for the next step to work correctly. 
        """
    )
    response = llm2.invoke(prompt.format(chunk=text_chunk))
    content = response.content

    # Extract the JSON array part using regex
    match = re.search(r"\[\s*{.*?}\s*\]", content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception as e:
            print(f"JSON parse error: {e}")
            return []
    else:
        print("No JSON found in LLM response.")
        return []

def insert_triplet_to_neo4j(driver, subject, predicate, object):
    with driver.session() as session:
        session.execute_write(
            lambda tx: tx.run(
                """
                MERGE (s:Entity {name: $subject})
                MERGE (o:Entity {name: $object})
                MERGE (s)-[:RELATION {type: $predicate}]->(o)
                """,
                subject=subject,
                predicate=predicate,
                object=object
            )
        )

def process_pdf_to_graph(pdf_docs):
    raw_text = extract_text_from_pdfs(pdf_docs)
    chunks = chunk_text(raw_text)
    all_triplets = []
    for chunk in chunks:
        triplets = extract_triplets(chunk)
        all_triplets.extend(triplets)

    st.success(f"{len(all_triplets)} Entities extracted successfully.")


    if st.button("Generate Graph in Neo4j"):
        for t in all_triplets:
            insert_triplet_to_neo4j(neo4j_driver, t['subject'], t['predicate'], t['object'])
        st.success("Neo4j Graph Generated successfully!")


    return raw_text  

# --- Streamlit UI ---
st.title("PDF to GraphRAG Chatbot")
st.sidebar.header("Upload PDFs")
pdf_docs = st.sidebar.file_uploader("Choose PDF files", type="pdf", accept_multiple_files=True)

# --- Initialize Chat History ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

doc_text = ""
if pdf_docs:
    doc_text = process_pdf_to_graph(pdf_docs)

# --- Chatbot (RAG over extracted context) ---
st.subheader("Ask Questions (RAG over Document)")

# Display Chat History
for message in st.session_state.chat_history:
    st.chat_message(message["role"]).write(message["content"])

user_question = st.chat_input("Ask a question about the uploaded document:")

if user_question:
    st.chat_message("user").write(user_question)
    st.session_state.chat_history.append({"role": "user", "content": user_question})

    if not doc_text:
        response_text = "Please upload a PDF first to enable question answering."
    else:
        rag_prompt = f"""
You are a helpful assistant. Answer the user's question based on the provided context from the document.
If you do not have enough context, just politely say you cannot answer.

Context:
{doc_text}

Question:
{user_question}

Answer:
"""
        response = llm.invoke(rag_prompt)
        response_text = response.content

    st.chat_message("assistant").write(response_text)
    st.session_state.chat_history.append({"role": "assistant", "content": response_text})
