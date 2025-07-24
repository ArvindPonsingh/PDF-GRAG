# PDF to GraphRAG Chatbot (Flask)

This project implements a chatbot that leverages a Graph-based Retrieval Augmented Generation (GraphRAG) approach to answer questions about PDF documents. Users can upload PDF files, extract entities and relationships to form a knowledge graph in Neo4j, and then chat with an AI assistant that uses this graph for more contextualized and accurate answers.

The frontend is built with Flask, HTML, CSS, and JavaScript, providing a user-friendly interface for document uploads and chat interactions.

## Features

* **PDF Upload:** Upload one or more PDF files for processing.
* **Entity & Relationship Extraction:** Extracts subject-predicate-object triplets from PDF content using an LLM (Groq).
* **Neo4j Graph Generation:** Stores the extracted triplets as a knowledge graph in a Neo4j database.
* **GraphRAG Chatbot:** Answers user questions by querying the generated knowledge graph and leveraging a Large Language Model (LLM) for contextual responses.
* **Interactive Frontend:** A clean Flask-based web interface for seamless interaction.

## Technologies Used

* **Backend:**
    * Python 3.9+
    * Flask: Web framework
    * PyPDF2: For PDF text extraction
    * LangChain: For text chunking, prompt management, and LLM integration
    * Groq: As the LLM provider (llama-3.3-70b-versatile, qwen/qwen3-32b)
    * Neo4j Python Driver: For interacting with the Neo4j graph database
    * python-dotenv: For managing environment variables
* **Frontend:**
    * HTML5
    * CSS3
    * JavaScript (Fetch API for AJAX)
* **Database:**
    * Neo4j Graph Database

https://github.com/user-attachments/assets/521d8d8c-266e-47b8-9eb7-8afff5eed012

c-4560-a09f-0027ed884efb" />
