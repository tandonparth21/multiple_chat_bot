# langchain_utils.py
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def query_huggingface_api(prompt, model="google/flan-t5-small"):
    api_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
    if not api_token:
        return None, "No API token found"

    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {api_token}"}

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_length": 200,
            "temperature": 0.1,
            "do_sample": True,
            "return_full_text": False
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()

        if isinstance(result, list) and len(result) > 0:
            if "generated_text" in result[0]:
                return result[0]["generated_text"].strip(), None
            elif "summary_text" in result[0]:
                return result[0]["summary_text"].strip(), None
        elif isinstance(result, dict):
            if "generated_text" in result:
                return result["generated_text"].strip(), None
            elif "error" in result:
                return None, result["error"]

        return None, f"Unexpected response format: {result}"

    except requests.exceptions.Timeout:
        return None, "API request timed out"
    except requests.exceptions.RequestException as e:
        return None, f"API request failed: {str(e)}"
    except Exception as e:
        return None, f"Error processing API response: {str(e)}"

def process_pdf(file_path, session_id):
    try:
        loader = PyPDFLoader(file_path)
        documents = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        docs = text_splitter.split_documents(documents)

        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )

        vectorstore = FAISS.from_documents(docs, embeddings)

        index_path = f"uploads/faiss_index_{session_id}"
        os.makedirs("uploads", exist_ok=True)
        vectorstore.save_local(index_path)

        return vectorstore

    except Exception as e:
        raise Exception(f"Error processing PDF: {str(e)}")

def query_pdf(vectorstore, query):
    try:
        docs_with_scores = vectorstore.similarity_search_with_score(query, k=5)
        # Relaxed threshold from 0.5 to 0.8
        docs = [doc for doc, score in docs_with_scores if score < 0.8]

        # If nothing under threshold, fallback to top k docs
        if not docs:
            docs = [doc for doc, _ in docs_with_scores]

        context = "\n".join([doc.page_content for doc in docs])
        if len(context) > 1500:
            context = context[:1500] + "..."

        prompt = f"""You are a helpful assistant. Use the following context to answer the question. If the answer is unclear, do your best to provide a useful related response.

[Context Start]
{context}
[Context End]

Question: {query}
Answer:"""

        answer, error = query_huggingface_api(prompt, model="google/flan-t5-small")

        if answer and len(answer.strip()) > 5:
            cleaned_answer = answer.strip()
            if "Answer:" in cleaned_answer:
                cleaned_answer = cleaned_answer.split("Answer:")[-1].strip()
            return cleaned_answer

        return generate_extractive_answer(docs, query)

    except Exception as e:
        return f"I encountered an error while processing your question: {str(e)}. Please try asking in a different way."

def generate_extractive_answer(docs, query):
    try:
        query_words = set(query.lower().split())
        best_score = 0
        best_chunk = ""

        for doc in docs:
            content = doc.page_content
            content_words = set(content.lower().split())
            overlap = len(query_words.intersection(content_words))
            if overlap > best_score:
                best_score = overlap
                best_chunk = content

        if best_chunk:
            return best_chunk[:300] + "..." if len(best_chunk) > 300 else best_chunk
        else:
            return "I found some related information but couldn't extract a specific answer."

    except Exception as e:
        return f"Error generating answer: {str(e)}"

def load_existing_vectorstore(session_id):
    try:
        index_path = f"uploads/faiss_index_{session_id}"
        if os.path.exists(index_path):
            embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
            return FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
        else:
            return None
    except Exception as e:
        raise Exception(f"Error loading vector store: {str(e)}")

def get_document_summary(vectorstore, max_chunks=5):
    try:
        all_docs = vectorstore.similarity_search("", k=max_chunks)
        if not all_docs:
            return "No content found in the document."
        combined_content = "\n\n".join([doc.page_content[:300] + "..." for doc in all_docs])
        return f"Document contains information about:\n\n{combined_content}"
    except Exception as e:
        return f"Error generating summary: {str(e)}"
