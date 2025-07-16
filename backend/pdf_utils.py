import os
import requests
from typing import List, Tuple
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

# Load environment variables
load_dotenv()

# Embedding model
embeddings_model = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

llm = ChatOpenAI(
    openai_api_base="https://api-inference.huggingface.co/models/",
    openai_api_key=os.getenv("HUGGINGFACE_API_KEY"),
    model_name="facebook/blenderbot-400M-distill",
)
# FAISS index path root - Corrected to be relative to this file's directory
FAISS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vector_store", "faiss_index")

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file."""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")

def split_text_into_docs(text: str) -> List[Document]:
    """Split text into manageable chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len
    )
    docs = splitter.create_documents([text])
    return docs

def embed_and_store(pdf_id: str, text: str) -> int:
    """Embed text and store in vector database."""
    try:
        docs = split_text_into_docs(text)
        print(f"Processing {len(docs)} document chunks for PDF {pdf_id}")

        # Create embeddings and store
        db = FAISS.from_documents(docs, embeddings_model)

        # Save to persistent storage
        persist_path = os.path.join(FAISS_DIR, pdf_id)
        os.makedirs(persist_path, exist_ok=True) # Ensure specific PDF's directory exists
        db.save_local(persist_path)

        return len(docs)
    except Exception as e:
        raise Exception(f"Error embedding and storing documents: {str(e)}")

def get_combined_vectorstore(pdf_ids: List[str]) -> FAISS:
    """Combine multiple vector stores."""
    try:
        stores = []
        for pdf_id in pdf_ids:
            path = os.path.join(FAISS_DIR, pdf_id)
            if os.path.exists(path):
                db = FAISS.load_local(path, embeddings_model, allow_dangerous_deserialization=True)
                stores.append(db)
            else:
                print(f"Warning: Vector store for PDF {pdf_id} not found at {path}. Skipping.")

        if not stores:
            raise ValueError("No valid vector stores found for the provided PDF IDs.")

        combined_store = stores[0]
        for store in stores[1:]:
            combined_store.merge_from(store)

        return combined_store
    except Exception as e:
        raise Exception(f"Error combining vector stores: {str(e)}")

def query_huggingface(prompt: str, max_length: int = 200) -> str:
    """Query Hugging Face model."""
    try:
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": max_length,
                "temperature": 0.7,
                "do_sample": True,
                "top_p": 0.9
            }
        }

        response = requests.post(HF_API_URL, headers=headers, json=payload)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            # Handle potential model issues where it just repeats the prompt
            generated_text = result[0].get("generated_text", "").strip()
            if generated_text.startswith(prompt):
                return generated_text[len(prompt):].strip()
            return generated_text
        
        return str(result) # Fallback in case of unexpected JSON structure

    except requests.exceptions.RequestException as e:
        print(f"Hugging Face API request failed: {e}")
        return "I'm currently unable to connect to the Hugging Face model."
    except Exception as e:
        print(f"Error querying Hugging Face: {str(e)}")
        return "I'm having trouble generating a response right now."

def query_documents(question: str, pdf_ids: List[str]) -> Tuple[str, List[str]]:
    """Query documents and generate answer."""
    try:
        vectorstore = get_combined_vectorstore(pdf_ids)

        relevant_docs = vectorstore.similarity_search(question, k=3)

        if not relevant_docs:
            return "I couldn't find relevant information in the provided documents.", []

        context = "\n\n".join([doc.page_content for doc in relevant_docs])

        prompt = f"""Based on the following context from the documents, please answer the question.

Context:
{context}

Question: {question}

Answer:"""

        answer = query_huggingface(prompt)

        # Fallback if the model gives a generic or empty answer
        if not answer or "I apologize" in answer or "I'm sorry" in answer or "I am just a language model" in answer:
            # Provide a direct summary from context if LLM fails
            answer = "Based on the documents, here's some relevant information:\n\n" + context

        sources = [doc.page_content[:100] + "..." for doc in relevant_docs] # Truncate for display

        return answer, sources

    except Exception as e:
        raise Exception(f"Error querying documents: {str(e)}")

# Fallback no-API version (kept for completeness but main query_documents uses HF)
def simple_query_documents(question: str, pdf_ids: List[str]) -> Tuple[str, List[str]]:
    """Simple document querying without external API for debugging or fallback."""
    try:
        vectorstore = get_combined_vectorstore(pdf_ids)
        relevant_docs = vectorstore.similarity_search(question, k=3)

        if not relevant_docs:
            return "I couldn't find relevant information in the provided documents.", []

        context_parts = []
        for i, doc in enumerate(relevant_docs, 1):
            context_parts.append(f"Source {i}: {doc.page_content[:300]}...")

        answer = f"Based on the documents, here's what I found:\n\n" + "\n\n".join(context_parts)
        sources = [doc.page_content[:100] + "..." for doc in relevant_docs]

        return answer, sources

    except Exception as e:
        raise Exception(f"Error simple querying documents: {str(e)}")