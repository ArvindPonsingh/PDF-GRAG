# services/pdf_processor.py

from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re
import json
from services.llm_service import llm_triplet_extraction # Corrected import name

def extract_text_from_pdfs(pdf_docs): # pdf_docs is expected to be an iterable (list)
    text = ""
    for pdf in pdf_docs: # Loop over each PDF in the provided iterable
        reader = PdfReader(pdf)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text

def chunk_text(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=200)
    return splitter.split_text(text)

def extract_triplets(text_chunk):
    prompt = """
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

    keep the triplets within the limit of 90000 tokens.
    """
    # Removed temporary print statements
    response = llm_triplet_extraction.invoke(prompt.format(chunk=text_chunk))
    content = response.content

    match = re.search(r"\[\s*{.*?}\s*\]", content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception as e:
            print(f"JSON parse error in extract_triplets: {e}")
            return []
    else:
        print("No JSON found in LLM response for triplet extraction.")
        return []