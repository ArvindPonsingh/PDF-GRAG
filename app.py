# app.py
from dotenv import load_dotenv
load_dotenv() # Load environment variables from .env file

from flask import Flask, render_template, request, jsonify
from services.pdf_processor import extract_text_from_pdfs, chunk_text, extract_triplets
from services.neo4j_handler import insert_triplet_to_neo4j, neo4j_driver
from services.llm_service import get_rag_response
# No need for SECRET_KEY or direct NEO4J_URI/USER/PASSWORD imports if handled by config.py/os.getenv
import os # Keep for potential os.getenv if config.py is not used for all vars

app = Flask(__name__)
# If you don't need sessions at all, DO NOT set app.secret_key.
# It's explicitly removed here.

# In this version, we will not use Flask's session object for storing data across requests.
# All necessary data (extracted triplets, document text for RAG) will be passed
# directly from the frontend (JavaScript) to the backend API endpoints.

@app.route('/')
def index():
    """Renders the main index HTML page."""
    return render_template('index.html')

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    """
    Handles PDF file uploads.
    Extracts text and triplets, and returns them to the frontend.
    Does NOT store data in Flask session.
    """
    if 'pdf_files' not in request.files:
        return jsonify({"success": False, "message": "No PDF files part in the request"}), 400

    pdf_files = request.files.getlist('pdf_files')
    if not pdf_files:
        return jsonify({"success": False, "message": "No selected files"}), 400
    pdf_file = pdf_files[0]

    try:
        raw_text = extract_text_from_pdfs([pdf_file])
        chunks = chunk_text(raw_text)

        extracted_triplets = []
        for chunk in chunks:
            triplets_from_chunk = extract_triplets(chunk)
            extracted_triplets.extend(triplets_from_chunk)

        # Return the actual extracted triplets and the full document text to the frontend.
        return jsonify({
            "success": True,
            "message": f"{len(extracted_triplets)} entities extracted. Click 'Generate Graph' to visualize.",
            "uploaded_doc_name": pdf_file.filename,
            "extracted_triplets": extracted_triplets, # IMPORTANT: Sending triplets back to frontend
            "document_text": raw_text # IMPORTANT: Sending document text back to frontend
        })
    except Exception as e:
        # Log the full exception for debugging server-side issues
        print(f"ERROR: Exception during PDF processing: {e}", exc_info=True)
        return jsonify({"success": False, "message": f"Error processing PDF: {str(e)}"}), 500

@app.route('/generate_graph', methods=['POST'])
def generate_graph():
    """
    Receives extracted triplets from the frontend and inserts them into Neo4j.
    Does NOT rely on Flask session for triplets.
    """
    data = request.json
    triplets_to_insert = data.get('triplets', []) # Get triplets directly from request body

    if not triplets_to_insert:
        return jsonify({"success": False, "message": "No triplets found in request to generate graph. Please upload a PDF first."}), 400

    try:
        with neo4j_driver.session() as neo4j_sess:
            for t in triplets_to_insert:
                insert_triplet_to_neo4j(neo4j_sess, t.get('subject', 'Unknown'), t.get('predicate', 'UNKNOWN_RELATION'), t.get('object', 'Unknown'))
        return jsonify({"success": True, "message": f"Neo4j Graph Generated successfully with {len(triplets_to_insert)} entities!"})
    except Exception as e:
        print(f"ERROR: Exception during graph generation: {e}", exc_info=True)
        return jsonify({"success": False, "message": f"Error generating graph: {str(e)}"}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """
    Receives user question and document text from the frontend,
    then uses LLM for RAG-style response.
    Does NOT rely on Flask session for document text or chat history.
    """
    data = request.json
    user_question = data.get('question')
    doc_text = data.get('document_text', '') # Get document text directly from request body

    if not user_question:
        return jsonify({"success": False, "message": "No question provided"}), 400

    if not doc_text:
        response_text = "Please upload a PDF first to enable question answering."
    else:
        response_text = get_rag_response(user_question, doc_text)

    # Chat history is entirely managed by the frontend in this "no sessions" approach.
    return jsonify({"success": True, "response": response_text})

# IMPORTANT: No Flask session-related endpoints like /clear_chat_history, /get_chat_history, /get_docs_info are needed or included here.
# The frontend will manage the display state.

if __name__ == '__main__':
    # Ensure debug is set to False for production deployments for security.
    # The port can be changed if 5001 is in use.
    app.run(debug=True, port=5001)