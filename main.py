# from fastapi import FastAPI, HTTPException, UploadFile, File
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from typing import Optional, List, Dict, Any
# import uvicorn
# import os
# from datetime import datetime

# # Import your custom classes (assuming they're in separate files)
# # from data_transformer import DataTransformer
# # from sql_chatbot import SQLChatbotAgent

# app = FastAPI(
#     title="Sales Data Chatbot API",
#     description="LLM-powered chatbot for querying sales data",
#     version="1.0.0"
# )

# # Enable CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Global chatbot instance
# chatbot = None

# class QueryRequest(BaseModel):
#     query: str
    
# class QueryResponse(BaseModel):
#     query: str
#     response: str
#     sql_query: Optional[str] = None
#     execution_time: float
#     timestamp: str

# class UploadResponse(BaseModel):
#     message: str
#     rows_loaded: int
#     status: str

# @app.on_event("startup")
# async def startup_event():
#     """Initialize chatbot on startup"""
#     global chatbot
#     try:
#         # Initialize your SQLChatbotAgent here
#         # chatbot = SQLChatbotAgent(db_path='sales_data.db')
#         print("✓ Chatbot initialized successfully")
#     except Exception as e:
#         print(f"✗ Failed to initialize chatbot: {e}")

# @app.get("/")
# async def root():
#     """Health check endpoint"""
#     return {
#         "status": "online",
#         "service": "Sales Data Chatbot API",
#         "version": "1.0.0",
#         "timestamp": datetime.now().isoformat()
#     }

# @app.post("/upload", response_model=UploadResponse)
# async def upload_excel(file: UploadFile = File(...)):
#     """
#     Upload and process Excel file
    
#     This endpoint:
#     1. Accepts Excel file upload
#     2. Transforms data to normalized format
#     3. Loads into SQLite database
#     """
#     try:
#         # Save uploaded file temporarily
#         temp_path = f"temp_{file.filename}"
#         with open(temp_path, "wb") as buffer:
#             content = await file.read()
#             buffer.write(content)
        
#         # Transform and load data
#         # transformer = DataTransformer(temp_path)
#         # df = transformer.load_and_clean_data()
#         # df_long = transformer.transform_to_long_format()
#         # transformer.create_database_schema()
#         # row_count = transformer.load_to_database(df_long)
        
#         # Clean up temp file
#         os.remove(temp_path)
        
#         # Reinitialize chatbot with new data
#         global chatbot
#         # chatbot = SQLChatbotAgent(db_path='sales_data.db')
        
#         return UploadResponse(
#             message="File processed successfully",
#             rows_loaded=0,  # row_count would go here
#             status="success"
#         )
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# @app.post("/query", response_model=QueryResponse)
# async def query_data(request: QueryRequest):
#     """
#     Query sales data using natural language
    
#     Examples:
#     - "What is the sales value of Product X in March?"
#     - "Total quantity sold in 2024"
#     - "Show me top 5 products by sales"
#     """
#     global chatbot
    
#     if not chatbot:
#         raise HTTPException(
#             status_code=503, 
#             detail="Chatbot not initialized. Please upload data first."
#         )
    
#     try:
#         start_time = datetime.now()
        
#         # Process query through chatbot
#         response = chatbot.chat(request.query)
        
#         execution_time = (datetime.now() - start_time).total_seconds()
        
#         return QueryResponse(
#             query=request.query,
#             response=response,
#             execution_time=execution_time,
#             timestamp=datetime.now().isoformat()
#         )
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

# @app.get("/schema")
# async def get_schema():
#     """Get database schema information"""
#     global chatbot
    
#     if not chatbot:
#         raise HTTPException(
#             status_code=503,
#             detail="Chatbot not initialized"
#         )
    
#     return {
#         "schema": chatbot.schema_info,
#         "database": chatbot.db_path
#     }

# @app.get("/examples")
# async def get_example_queries():
#     """Get example queries users can try"""
#     return {
#         "examples": [
#             {
#                 "category": "Simple Lookup",
#                 "queries": [
#                     "What is the sales value of Product X in March?",
#                     "Show me quantity for Product Y in January 2024"
#                 ]
#             },
#             {
#                 "category": "Aggregations",
#                 "queries": [
#                     "Total sales value across all products in 2024",
#                     "Average quantity sold per month",
#                     "Sum of sales values for country USA"
#                 ]
#             },
#             {
#                 "category": "Comparisons",
#                 "queries": [
#                     "Top 5 products by sales value",
#                     "Which country has the highest total sales?",
#                     "Compare sales between January and February"
#                 ]
#             },
#             {
#                 "category": "Filters & Groups",
#                 "queries": [
#                     "Sales values by product category in Q1",
#                     "Total quantity by brand",
#                     "Monthly sales trend for 2024"
#                 ]
#             }
#         ]
#     }

# @app.post("/direct-sql")
# async def execute_direct_sql(sql_query: str):
#     """
#     Execute SQL query directly (admin use)
#     WARNING: Use with caution
#     """
#     global chatbot
    
#     if not chatbot:
#         raise HTTPException(
#             status_code=503,
#             detail="Chatbot not initialized"
#         )
    
#     try:
#         result = chatbot.execute_query(sql_query)
#         return result
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"SQL execution failed: {str(e)}")

# @app.get("/stats")
# async def get_database_stats():
#     """Get database statistics"""
#     global chatbot
    
#     if not chatbot:
#         raise HTTPException(
#             status_code=503,
#             detail="Chatbot not initialized"
#         )
    
#     try:
#         import sqlite3
#         conn = sqlite3.connect(chatbot.db_path)
#         cursor = conn.cursor()
        
#         # Get total rows
#         cursor.execute("SELECT COUNT(*) FROM sales_facts")
#         total_rows = cursor.fetchone()[0]
        
#         # Get unique products
#         cursor.execute("SELECT COUNT(DISTINCT product_cat) FROM sales_facts")
#         unique_products = cursor.fetchone()[0]
        
#         # Get date range
#         cursor.execute("SELECT DISTINCT year FROM sales_facts ORDER BY year")
#         years = [row[0] for row in cursor.fetchall()]
        
#         # Get metrics
#         cursor.execute("SELECT DISTINCT metric_type FROM sales_facts")
#         metrics = [row[0] for row in cursor.fetchall()]
        
#         conn.close()
        
#         return {
#             "total_records": total_rows,
#             "unique_products": unique_products,
#             "years": years,
#             "available_metrics": metrics,
#             "database_size": os.path.getsize(chatbot.db_path)
#         }
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")

# if __name__ == "__main__":
#     uvicorn.run(
#         "main:app",
#         host="0.0.0.0",
#         port=8000,
#         reload=True,
#         log_level="info"
#     )


from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import os
from datetime import datetime
import sqlite3

# Import your custom classes (assuming they're in separate files)
from data_transformer import DataTransformer
# SQLChatbotAgent is imported lazily where needed to avoid startup errors when DB is empty

app = FastAPI(
    title="Sales Data Chatbot API",
    description="LLM-powered chatbot for querying sales data",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global chatbot instance
chatbot = None

class QueryRequest(BaseModel):
    query: str
    
class QueryResponse(BaseModel):
    query: str
    response: str
    sql_query: Optional[str] = None
    execution_time: float
    timestamp: str

class UploadResponse(BaseModel):
    message: str
    rows_loaded: int
    status: str

@app.on_event("startup")
async def startup_event():
    """Initialize chatbot on startup if database is ready"""
    global chatbot
    try:
        db_path = 'sales_data.db'
        # Check if the required table exists before initializing the chatbot
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sales_facts'")
        table_exists = cur.fetchone() is not None
        conn.close()

        if not table_exists:
            print("ℹ️ Database not initialized yet (missing table 'sales_facts'). Upload data first.")
            return

        # Initialize SQLChatbotAgent with Ollama
        from sql_chatbot import SQLChatbotAgent
        ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        ollama_model = os.getenv('OLLAMA_MODEL', 'llama3.1')
        
        chatbot = SQLChatbotAgent(
            db_path=db_path,
            ollama_url=ollama_url,
            model=ollama_model
        )
        print(f"✓ Chatbot initialized with Ollama ({ollama_model})")
    except Exception as e:
        print(f"✗ Failed to initialize chatbot: {e}")
        print("  Make sure Ollama is running: ollama serve")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Sales Data Chatbot API",
        "llm_backend": "Ollama (Llama 3.1)",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/upload", response_model=UploadResponse)
async def upload_excel(file: UploadFile = File(...)):
    """
    Upload and process Excel file
    
    This endpoint:
    1. Accepts Excel file upload
    2. Transforms data to normalized format
    3. Loads into SQLite database
    """
    try:
        # Save uploaded file temporarily
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Transform and load data
        transformer = DataTransformer(temp_path)
        df = transformer.load_and_clean_data()
        df_long = transformer.transform_to_long_format()
        # Ensure schema exists and then load data
        transformer.create_database_schema(db_path='sales_data.db')
        row_count = transformer.load_to_database(df_long, db_path='sales_data.db')
        
        # Clean up temp file
        os.remove(temp_path)
        
        # Reinitialize chatbot with new data
        global chatbot
        from sql_chatbot import SQLChatbotAgent
        
        ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        ollama_model = os.getenv('OLLAMA_MODEL', 'llama3.1')
        
        chatbot = SQLChatbotAgent(
            db_path='sales_data.db',
            ollama_url=ollama_url,
            model=ollama_model
        )
        
        return UploadResponse(
            message="File processed successfully",
            rows_loaded=row_count,
            status="success"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query_data(request: QueryRequest):
    """
    Query sales data using natural language
    
    Examples:
    - "What is the sales value of Product X in March?"
    - "Total quantity sold in 2024"
    - "Show me top 5 products by sales"
    """
    global chatbot
    
    if not chatbot:
        raise HTTPException(
            status_code=503, 
            detail="Chatbot not initialized. Please upload data first."
        )
    
    try:
        start_time = datetime.now()
        
        # Process query through chatbot
        response = chatbot.chat(request.query)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResponse(
            query=request.query,
            response=response,
            execution_time=execution_time,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.get("/schema")
async def get_schema():
    """Get database schema information"""
    global chatbot
    
    if not chatbot:
        raise HTTPException(
            status_code=503,
            detail="Chatbot not initialized"
        )
    
    return {
        "schema": chatbot.schema_info,
        "database": chatbot.db_path
    }

@app.get("/examples")
async def get_example_queries():
    """Get example queries users can try"""
    return {
        "examples": [
            {
                "category": "Simple Lookup",
                "queries": [
                    "What is the sales value of Product X in March?",
                    "Show me quantity for Product Y in January 2024"
                ]
            },
            {
                "category": "Aggregations",
                "queries": [
                    "Total sales value across all products in 2024",
                    "Average quantity sold per month",
                    "Sum of sales values for country USA"
                ]
            },
            {
                "category": "Comparisons",
                "queries": [
                    "Top 5 products by sales value",
                    "Which country has the highest total sales?",
                    "Compare sales between January and February"
                ]
            },
            {
                "category": "Filters & Groups",
                "queries": [
                    "Sales values by product category in Q1",
                    "Total quantity by brand",
                    "Monthly sales trend for 2024"
                ]
            }
        ]
    }

@app.post("/direct-sql")
async def execute_direct_sql(sql_query: str):
    """
    Execute SQL query directly (admin use)
    WARNING: Use with caution
    """
    global chatbot
    
    if not chatbot:
        raise HTTPException(
            status_code=503,
            detail="Chatbot not initialized"
        )
    
    try:
        result = chatbot.execute_query(sql_query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SQL execution failed: {str(e)}")

@app.get("/stats")
async def get_database_stats():
    """Get database statistics"""
    global chatbot
    
    if not chatbot:
        raise HTTPException(
            status_code=503,
            detail="Chatbot not initialized"
        )
    
    try:
        import sqlite3
        conn = sqlite3.connect(chatbot.db_path)
        cursor = conn.cursor()
        
        # Get total rows
        cursor.execute("SELECT COUNT(*) FROM sales_facts")
        total_rows = cursor.fetchone()[0]
        
        # Get unique brands and product groups
        cursor.execute("SELECT COUNT(DISTINCT brand) FROM sales_facts")
        unique_brands = cursor.fetchone()[0]
        try:
            cursor.execute("SELECT COUNT(DISTINCT product_group) FROM sales_facts")
            unique_product_groups = cursor.fetchone()[0]
        except Exception:
            unique_product_groups = None
        
        # Get date range
        cursor.execute("SELECT DISTINCT year FROM sales_facts ORDER BY year")
        years = [row[0] for row in cursor.fetchall()]
        
        # Get metrics
        cursor.execute("SELECT DISTINCT metric_type FROM sales_facts")
        metrics = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "total_records": total_rows,
            "unique_brands": unique_brands,
            "unique_product_groups": unique_product_groups,
            "years": years,
            "available_metrics": metrics,
            "database_size": os.path.getsize(chatbot.db_path)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")

@app.get("/ollama/health")
async def check_ollama_health():
    """Check if Ollama service is running and responsive"""
    global chatbot
    
    if not chatbot:
        return {
            "status": "error",
            "message": "Chatbot not initialized"
        }
    
    try:
        import requests
        response = requests.get(f"{chatbot.ollama_url}/api/tags", timeout=5)
        
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            
            return {
                "status": "healthy",
                "ollama_url": chatbot.ollama_url,
                "current_model": chatbot.model,
                "available_models": model_names,
                "model_loaded": any(chatbot.model in name for name in model_names)
            }
        else:
            return {
                "status": "unhealthy",
                "message": f"Ollama returned status {response.status_code}"
            }
    except requests.exceptions.Timeout:
        return {
            "status": "timeout",
            "message": "Ollama service not responding"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )