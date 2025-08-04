from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import json
import asyncio
from datetime import datetime

from app.sql_connector import SQLConnector
from app.rag_system import RAGSystem
import openai

app = FastAPI()
sql_connector = SQLConnector()
rag_system = RAGSystem()

class ChatRequest(BaseModel):
    messages: List[dict]
    use_sql: bool = False
    use_rag: bool = True

class SQLQueryRequest(BaseModel):
    question: str

@app.on_event("startup")
async def startup_event():
    """Initialize RAG system with database schema"""
    # Load ITCAN database schema into RAG
    schema_docs = [
        {
            "content": """
            Table: coupon_performance_bi
            Key columns:
            - net_revenue_aed: Revenue after cancellations (numeric)
            - client_name: Brand name (text) - Examples: Ounass, Sephora
            - team_name: Team (text) - Values: CPX, Influencer, SSC
            - coupon_code: Promotional code (text)
            - order_date: Transaction date (datetime)
            - cancellation_rate: Percentage cancelled (numeric)
            
            Important: Each row is one transaction. Aggregate for totals.
            """,
            "source": "database_schema"
        }
    ]
    rag_system.add_documents(schema_docs)

@app.post("/chat")
async def chat(request: ChatRequest):
    """Enhanced chat endpoint with SQL and RAG"""
    
    messages = request.messages
    last_message = messages[-1]["content"]
    
    # Determine if SQL query is needed
    sql_keywords = ["revenue", "sales", "performance", "top", "total", "compare", "trend"]
    needs_sql = request.use_sql or any(keyword in last_message.lower() for keyword in sql_keywords)
    
    if needs_sql:
        # Generate SQL query using RAG context
        context = rag_system.generate_sql_context(last_message)
        
        sql_prompt = f"""
        {context}
        
        User question: {last_message}
        
        Generate a SQL query for the coupon_performance_bi table.
        Only use SELECT statements.
        Include appropriate aggregations (SUM, COUNT, AVG) and GROUP BY as needed.
        Limit results appropriately.
        
        Return ONLY the SQL query, no explanation.
        """
        
        # Get SQL from GPT
        sql_response = openai.ChatCompletion.create(
            engine=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            messages=[
                {"role": "system", "content": "You are a SQL expert for ITCAN database."},
                {"role": "user", "content": sql_prompt}
            ],
            temperature=0,
            max_tokens=500
        )
        
        sql_query = sql_response.choices[0].message.content.strip()
        
        try:
            # Execute SQL
            results = sql_connector.execute_query(sql_query)
            
            # Add results to context
            messages.append({
                "role": "system",
                "content": f"SQL Query: {sql_query}\nResults: {json.dumps(results[:50])}"  # Limit results
            })
            
        except Exception as e:
            messages.append({
                "role": "system",
                "content": f"SQL Error: {str(e)}"
            })
    
    # Use RAG for additional context
    if request.use_rag:
        rag_results = rag_system.search_similar(last_message, k=3)
        rag_context = "\n".join([r['content'] for r in rag_results])
        
        messages.insert(-1, {
            "role": "system",
            "content": f"Relevant information:\n{rag_context}"
        })
    
    # Stream response
    async def generate():
        response = openai.ChatCompletion.create(
            engine=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            messages=messages,
            temperature=0.7,
            stream=True
        )
        
        for chunk in response:
            if chunk.choices[0].delta.get("content"):
                yield f"data: {json.dumps({'content': chunk.choices[0].delta.content})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/sql/generate")
async def generate_sql(request: SQLQueryRequest):
    """Generate SQL from natural language"""
    context = rag_system.generate_sql_context(request.question)
    
    prompt = f"""
    {context}
    
    Convert this question to SQL: {request.question}
    
    Rules:
    1. Use coupon_performance_bi table
    2. Only SELECT queries
    3. Use appropriate aggregations
    4. Include ORDER BY for rankings
    5. Add TOP or LIMIT clause
    
    Return SQL query only.
    """
    
    response = openai.ChatCompletion.create(
        engine=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=[
            {"role": "system", "content": "You are a SQL expert."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    
    return {"sql": response.choices[0].message.content.strip()}

@app.post("/knowledge/add")
async def add_knowledge(documents: List[Dict[str, str]]):
    """Add documents to RAG system"""
    rag_system.add_documents(documents)
    return {"message": f"Added {len(documents)} documents"}