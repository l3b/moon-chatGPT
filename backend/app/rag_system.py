import os
from typing import List, Dict, Optional
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.models import VectorizedQuery
import openai
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import AzureSearch
from langchain.chains import RetrievalQA
from langchain.llms import AzureOpenAI
import json

class RAGSystem:
    def __init__(self):
        # Azure Search setup
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.search_key = os.getenv("AZURE_SEARCH_KEY")
        self.index_name = os.getenv("AZURE_SEARCH_INDEX", "itcan-knowledge")
        
        # OpenAI setup
        self.openai_api_key = os.getenv("AZURE_OPENAI_KEY")
        self.openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        self.embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
        
        # Initialize components
        self._init_components()
        
    def _init_components(self):
        """Initialize RAG components"""
        # Embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=self.openai_api_key,
            openai_api_base=self.openai_endpoint,
            deployment=self.embedding_deployment,
            chunk_size=1
        )
        
        # Vector store
        self.vector_store = AzureSearch(
            azure_search_endpoint=self.search_endpoint,
            azure_search_key=self.search_key,
            index_name=self.index_name,
            embedding_function=self.embeddings.embed_query
        )
        
        # LLM
        self.llm = AzureOpenAI(
            deployment_name=self.deployment_name,
            openai_api_key=self.openai_api_key,
            openai_api_base=self.openai_endpoint,
            temperature=0
        )
        
    def add_documents(self, documents: List[Dict[str, str]]):
        """Add documents to vector store"""
        texts = [doc['content'] for doc in documents]
        metadatas = [{'source': doc.get('source', 'unknown')} for doc in documents]
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        split_texts = text_splitter.split_texts(texts)
        self.vector_store.add_texts(split_texts, metadatas)
        
    def search_similar(self, query: str, k: int = 5) -> List[Dict]:
        """Search for similar documents"""
        results = self.vector_store.similarity_search_with_score(query, k=k)
        return [
            {
                'content': doc.page_content,
                'metadata': doc.metadata,
                'score': score
            }
            for doc, score in results
        ]
        
    def generate_sql_context(self, question: str) -> str:
        """Generate SQL context from question"""
        # Search for relevant schema information
        schema_results = self.search_similar(f"SQL schema table structure {question}", k=3)
        
        context = "Relevant database information:\n"
        for result in schema_results:
            context += f"{result['content']}\n"
            
        return context