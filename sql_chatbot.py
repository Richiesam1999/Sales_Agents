# import sqlite3
# import anthropic
# import os
# from typing import Dict, List, Any
# import json

# class SQLChatbotAgent:
#     """
#     LLM-powered chatbot that converts natural language to SQL queries
#     and executes them against the sales database
#     """
    
#     def __init__(self, db_path='sales_data.db', api_key=None):
#         self.db_path = db_path
#         self.client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
#         self.model = "claude-sonnet-4-5-20250929"
        
#         # Get database schema for context
#         self.schema_info = self.get_schema_info()
        
#     def get_schema_info(self) -> str:
#         """Get database schema information"""
#         conn = sqlite3.connect(self.db_path)
#         cursor = conn.cursor()
        
#         cursor.execute("""
#             SELECT sql FROM sqlite_master 
#             WHERE type='table' AND name='sales_facts'
#         """)
#         schema = cursor.fetchone()[0]
        
#         # Get sample data
#         cursor.execute("SELECT * FROM sales_facts LIMIT 3")
#         sample_data = cursor.fetchall()
        
#         # Get distinct values for key columns
#         cursor.execute("SELECT DISTINCT metric_type FROM sales_facts")
#         metrics = [row[0] for row in cursor.fetchall()]
        
#         cursor.execute("SELECT DISTINCT period FROM sales_facts")
#         periods = [row[0] for row in cursor.fetchall()]
        
#         conn.close()
        
#         schema_context = f"""
# DATABASE SCHEMA:
# {schema}

# AVAILABLE METRICS: {', '.join(metrics)}
# AVAILABLE PERIODS: {', '.join(periods)}

# SAMPLE DATA (first 3 rows):
# {sample_data}

# KEY INFORMATION:
# - metric_type: Type of metric (Quantity, Sales_Value, etc.)
# - period: Month abbreviation (Jan, Feb, Mar, etc.)
# - year: Year as string
# - value: Numeric value for the metric
# - product_cat: Product category
# - country: Country name
# - All text columns are case-sensitive
# """
#         return schema_context
    
#     def query_to_sql(self, user_query: str) -> Dict[str, Any]:
#         """Convert natural language query to SQL using Claude"""
        
#         system_prompt = f"""You are an expert SQL query generator for a sales database. 
# Your job is to convert natural language questions into valid SQLite queries.

# {self.schema_info}

# RULES:
# 1. Generate ONLY valid SQLite syntax
# 2. Use appropriate aggregation functions (SUM, AVG, COUNT, etc.)
# 3. Always handle case-sensitivity for text fields using LOWER() when comparing
# 4. For month queries, match the period column (Jan, Feb, Mar, etc.)
# 5. Return results in a clear, organized manner
# 6. Use WHERE clauses to filter data accurately
# 7. When asked for totals or sums, use SUM() function
# 8. Group by relevant dimensions when aggregating

# OUTPUT FORMAT:
# Return a JSON object with:
# {{
#     "sql": "the SQL query",
#     "explanation": "brief explanation of what the query does",
#     "query_type": "select|aggregate|count"
# }}
# """
        
#         messages = [
#             {
#                 "role": "user",
#                 "content": f"""Convert this question to SQL: "{user_query}"

# Example queries:
# - "What is the sales value of Product X in March?" 
#   -> SELECT value FROM sales_facts WHERE metric_type='Sales_Value' AND LOWER(product_cat) LIKE '%x%' AND period='Mar'
  
# - "Total quantity sold for all products in 2024"
#   -> SELECT SUM(value) as total FROM sales_facts WHERE metric_type='Quantity' AND year='2024'

# Now convert: "{user_query}"
# """
#             }
#         ]
        
#         response = self.client.messages.create(
#             model=self.model,
#             max_tokens=1000,
#             system=system_prompt,
#             messages=messages
#         )
        
#         # Parse response
#         content = response.content[0].text
        
#         # Extract JSON from response
#         try:
#             # Try to find JSON in the response
#             start_idx = content.find('{')
#             end_idx = content.rfind('}') + 1
#             if start_idx != -1 and end_idx != 0:
#                 json_str = content[start_idx:end_idx]
#                 result = json.loads(json_str)
#             else:
#                 # Fallback: create structured response
#                 result = {
#                     "sql": content,
#                     "explanation": "SQL query generated",
#                     "query_type": "select"
#                 }
#         except json.JSONDecodeError:
#             result = {
#                 "sql": content,
#                 "explanation": "SQL query generated",
#                 "query_type": "select"
#             }
        
#         return result
    
#     def execute_query(self, sql_query: str) -> List[tuple]:
#         """Execute SQL query and return results"""
#         try:
#             conn = sqlite3.connect(self.db_path)
#             cursor = conn.cursor()
            
#             cursor.execute(sql_query)
#             results = cursor.fetchall()
            
#             # Get column names
#             column_names = [description[0] for description in cursor.description]
            
#             conn.close()
            
#             return {
#                 "success": True,
#                 "results": results,
#                 "columns": column_names,
#                 "row_count": len(results)
#             }
#         except Exception as e:
#             return {
#                 "success": False,
#                 "error": str(e),
#                 "results": [],
#                 "columns": []
#             }
    
#     def format_response(self, query_result: Dict, execution_result: Dict) -> str:
#         """Format the final response for the user"""
        
#         if not execution_result["success"]:
#             return f"❌ Query execution failed: {execution_result['error']}"
        
#         results = execution_result["results"]
#         columns = execution_result["columns"]
        
#         if not results:
#             return "No results found for your query."
        
#         # Format response based on result type
#         response = f"📊 **Query Results**\n\n"
#         response += f"_{query_result.get('explanation', 'Query executed successfully')}_\n\n"
        
#         # If single value (aggregate), show it prominently
#         if len(results) == 1 and len(results[0]) == 1:
#             response += f"**Result:** {results[0][0]:,.2f}" if isinstance(results[0][0], (int, float)) else f"**Result:** {results[0][0]}"
#         else:
#             # Table format for multiple results
#             response += "```\n"
#             # Header
#             response += " | ".join(columns) + "\n"
#             response += "-" * (len(" | ".join(columns))) + "\n"
            
#             # Rows (limit to first 20)
#             for row in results[:20]:
#                 formatted_row = []
#                 for val in row:
#                     if isinstance(val, float):
#                         formatted_row.append(f"{val:,.2f}")
#                     else:
#                         formatted_row.append(str(val))
#                 response += " | ".join(formatted_row) + "\n"
            
#             if len(results) > 20:
#                 response += f"\n... and {len(results) - 20} more rows\n"
            
#             response += "```\n"
#             response += f"\n**Total rows:** {len(results)}"
        
#         return response
    
#     def chat(self, user_query: str) -> str:
#         """Main chat interface - handle user query end-to-end"""
        
#         print(f"\n🤔 Processing: {user_query}")
        
#         # Step 1: Convert to SQL
#         print("🔄 Converting to SQL...")
#         sql_result = self.query_to_sql(user_query)
        
#         print(f"📝 Generated SQL: {sql_result['sql']}")
        
#         # Step 2: Execute query
#         print("⚡ Executing query...")
#         execution_result = self.execute_query(sql_result['sql'])
        
#         # Step 3: Format response
#         response = self.format_response(sql_result, execution_result)
        
#         return response

# # Usage Example
# if __name__ == "__main__":
#     # Initialize chatbot
#     chatbot = SQLChatbotAgent(db_path='sales_data.db')
    
#     # Example queries
#     test_queries = [
#         "What is the sales value of Product X in March?",
#         "Total quantity sold across all products in 2024",
#         "Show me sales values for all countries in January",
#         "What's the average sales value per product category?",
#         "Give me the top 5 products by quantity sold"
#     ]
    
#     print("=" * 60)
#     print("SQL CHATBOT - Ready to answer your questions!")
#     print("=" * 60)
    
#     # Interactive mode
#     while True:
#         user_input = input("\n💬 You: ")
        
#         if user_input.lower() in ['exit', 'quit', 'bye']:
#             print("👋 Goodbye!")
#             break
        
#         response = chatbot.chat(user_input)
#         print(f"\n🤖 Assistant:\n{response}")




import sqlite3
import requests
import json
from typing import Dict, List, Any

class SQLChatbotAgent:
    """
    LLM-powered chatbot using Ollama (Llama 3.1) that converts 
    natural language to SQL queries and executes them
    """
    
    def __init__(self, db_path='sales_data.db', ollama_url='http://localhost:11434', model='llama3.1'):
        self.db_path = db_path
        self.ollama_url = ollama_url
        self.model = model
        
        # Get database schema for context
        self.schema_info = self.get_schema_info()
        
        # Test Ollama connection
        self._test_ollama_connection()
        
    def _test_ollama_connection(self):
        """Test if Ollama is running and model is available"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                
                if not any(self.model in name for name in model_names):
                    print(f"⚠️  Warning: Model '{self.model}' not found. Available models: {model_names}")
                    print(f"    Run: ollama pull {self.model}")
                else:
                    print(f"✓ Connected to Ollama - Model '{self.model}' ready")
            else:
                print(f"⚠️  Warning: Could not connect to Ollama at {self.ollama_url}")
        except Exception as e:
            print(f"⚠️  Warning: Ollama connection error: {e}")
            print(f"    Make sure Ollama is running: ollama serve")
    
    def get_schema_info(self) -> str:
        """Get database schema information (safe if table is missing)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verify table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sales_facts'")
        if cursor.fetchone() is None:
            conn.close()
            return (
                "sales_facts table not found. Upload an Excel file to initialize the database."
            )
        
        # Fetch schema and sample metadata
        cursor.execute(
            """
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='sales_facts'
            """
        )
        row = cursor.fetchone()
        schema = row[0] if row else "CREATE TABLE sales_facts (...)"
        
        # Get sample data
        cursor.execute("SELECT * FROM sales_facts LIMIT 3")
        sample_data = cursor.fetchall()
        
        # Get distinct values for key columns
        cursor.execute("SELECT DISTINCT metric_type FROM sales_facts")
        metrics = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT period FROM sales_facts")
        periods = [row[0] for row in cursor.fetchall()]
        
        # Get sample values for key dimension columns
        cursor.execute("SELECT DISTINCT zone FROM sales_facts WHERE zone IS NOT NULL LIMIT 5")
        zones = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT zsm FROM sales_facts WHERE zsm IS NOT NULL LIMIT 5")
        zsms = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT sales_head FROM sales_facts WHERE sales_head IS NOT NULL LIMIT 5")
        sales_heads = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT product_group FROM sales_facts WHERE product_group IS NOT NULL LIMIT 5")
        products = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        schema_context = f"""
DATABASE SCHEMA:
{schema}

AVAILABLE DATA:
- Metrics: {', '.join(metrics)}
- Periods: {', '.join(periods)}
- Zones: {', '.join(zones)}
- Sample ZSMs: {', '.join(zsms)}
- Sample Sales Heads: {', '.join(sales_heads)}
- Sample Products: {', '.join(products)}

SAMPLE DATA (first 3 rows):
{sample_data}

KEY COLUMNS & THEIR PURPOSE:

DIMENSIONS:
- year: Year (e.g., 'FY24', '2024')
- period: Month abbreviation (Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec)
- zone: Sales zone (e.g., 'South', 'North & East', 'West')
- zsm: ZSM name (e.g., 'Sivaneshan', 'Md. Nadim', 'Jatin Bhatt')
- sales_head: Sales head name (e.g., 'Sanjay Yadav', 'Rajesh Pandey')
- entity: Entity name (e.g., 'MLSIPL')
- continent: Continent name
- country: Country name
- division: Division
- brand: Brand name

PRODUCT COLUMNS (HIERARCHY):
1. product_group: PRIMARY detailed product (e.g., 'Patella', 'Hip Screw', 'Liner PS') ⭐ USE THIS FIRST
2. product_group_1: Broader category (e.g., 'Hip', 'Knee')
3. product_group_2: Brand grouping (e.g., 'Freedom', 'Latitud')

METRICS:
- metric_type: 'Quantity' or 'Value'
- value: Numeric value for the metric

IMPORTANT NOTES:
- Names like 'Sivaneshan', 'Md. Nadim', 'Jatin Bhatt' are in the 'zsm' column, NOT 'entity'
- Product names like 'Patella', 'Hip Screw' are in 'product_group' column
- Always use LOWER() for case-insensitive text matching
- Zones are: 'South', 'North & East', 'West'
"""
        return schema_context
    
    def query_to_sql(self, user_query: str) -> Dict[str, Any]:
        """Convert natural language query to SQL using Ollama"""
        
        system_prompt = f"""You are an expert SQL query generator for a sales database. 
Your job is to convert natural language questions into valid SQLite queries.

{self.schema_info}

RULES:
1. Generate ONLY valid SQLite syntax
2. Use appropriate aggregation functions (SUM, AVG, COUNT, etc.)
3. Always handle case-sensitivity for text fields using LOWER() when comparing
4. For month queries, match the period column (Jan, Feb, Mar, etc.)
5. Return results in a clear, organized manner
6. Use WHERE clauses to filter data accurately
7. When asked for totals or sums, use SUM() function
8. Group by relevant dimensions when aggregating
9. IMPORTANT: For product lookups, ALWAYS search 'product_group' column FIRST
   - Use: WHERE LOWER(product_group) LIKE '%search_term%'
   - Only use product_group_1 or product_group_2 if specifically mentioned or as fallback

OUTPUT FORMAT:
You must return ONLY a valid JSON object with this exact structure:
{{
    "sql": "the SQL query here",
    "explanation": "brief explanation of what the query does",
    "query_type": "select"
}}

Do not include any other text, markdown formatting, or explanations outside the JSON object."""
        
        prompt = f"""{system_prompt}

USER QUESTION: "{user_query}"

EXAMPLE CONVERSIONS:

Question: "What is the sales value of Product X in March?"
Response: {{"sql": "SELECT SUM(value) as total_value FROM sales_facts WHERE metric_type='Value' AND LOWER(product_group) LIKE '%x%' AND period='Mar'", "explanation": "Getting sales value for Product X in March from product_group", "query_type": "aggregate"}}

Question: "Total quantity sold for all products in 2024"
Response: {{"sql": "SELECT SUM(value) as total FROM sales_facts WHERE metric_type='Quantity' AND year='2024'", "explanation": "Calculating total quantity sold in 2024", "query_type": "aggregate"}}

Question: "Show sales by product group"
Response: {{"sql": "SELECT product_group, SUM(value) as total_value FROM sales_facts WHERE metric_type='Value' GROUP BY product_group ORDER BY total_value DESC", "explanation": "Aggregating sales by primary product_group column", "query_type": "aggregate"}}

Question: "How many units did Sivaneshan sell for Patella in June FY24 in South zone?"
Response: {{"sql": "SELECT SUM(value) as total_quantity FROM sales_facts WHERE metric_type='Quantity' AND LOWER(zsm) LIKE '%sivaneshan%' AND LOWER(product_group) LIKE '%patella%' AND period='Jun' AND year='FY24' AND LOWER(zone) LIKE '%south%'", "explanation": "Getting quantity sold by Sivaneshan for Patella product in June FY24 in South zone", "query_type": "aggregate"}}

Question: "Sales by Jatin Bhatt in West zone"
Response: {{"sql": "SELECT SUM(value) as total_sales FROM sales_facts WHERE metric_type='Value' AND LOWER(zsm) LIKE '%jatin%' AND LOWER(zone) LIKE '%west%'", "explanation": "Getting total sales by ZSM Jatin Bhatt in West zone", "query_type": "aggregate"}}

Now convert this question to SQL: "{user_query}"

Remember: Return ONLY the JSON object, nothing else."""
        
        try:
            # Call Ollama API
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for more deterministic output
                        "top_p": 0.9,
                    }
                },
                timeout=60
            )
            
            if response.status_code != 200:
                return {
                    "sql": "",
                    "explanation": f"Error: Ollama API returned status {response.status_code}",
                    "query_type": "error"
                }
            
            # Parse Ollama response
            ollama_response = response.json()
            content = ollama_response.get('response', '')
            
            # Extract JSON from response
            result = self._extract_json_from_response(content)
            
            return result
            
        except requests.exceptions.Timeout:
            return {
                "sql": "",
                "explanation": "Error: Request to Ollama timed out",
                "query_type": "error"
            }
        except Exception as e:
            return {
                "sql": "",
                "explanation": f"Error: {str(e)}",
                "query_type": "error"
            }
    
    def _extract_json_from_response(self, content: str) -> Dict[str, Any]:
        """Extract and parse JSON from LLM response"""
        try:
            # Try to find JSON in the response
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = content[start_idx:end_idx]
                result = json.loads(json_str)
                
                # Validate required fields
                if 'sql' in result:
                    return {
                        "sql": result.get('sql', ''),
                        "explanation": result.get('explanation', 'SQL query generated'),
                        "query_type": result.get('query_type', 'select')
                    }
            
            # If no valid JSON found, try to extract SQL directly
            # Look for SQL keywords
            if 'SELECT' in content.upper():
                lines = content.split('\n')
                for line in lines:
                    if 'SELECT' in line.upper():
                        return {
                            "sql": line.strip(),
                            "explanation": "SQL query extracted from response",
                            "query_type": "select"
                        }
            
            # Fallback
            return {
                "sql": content.strip(),
                "explanation": "Response processed",
                "query_type": "select"
            }
            
        except json.JSONDecodeError:
            # Try to extract SQL even if JSON parsing fails
            if 'SELECT' in content.upper():
                return {
                    "sql": content.strip(),
                    "explanation": "SQL query extracted",
                    "query_type": "select"
                }
            
            return {
                "sql": "",
                "explanation": "Could not parse response",
                "query_type": "error"
            }
    
    def execute_query(self, sql_query: str) -> Dict:
        """Execute SQL query and return results"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(sql_query)
            results = cursor.fetchall()
            
            # Get column names
            column_names = [description[0] for description in cursor.description] if cursor.description else []
            
            conn.close()
            
            return {
                "success": True,
                "results": results,
                "columns": column_names,
                "row_count": len(results)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "columns": []
            }
    
    def execute_query_with_fallback(self, sql_query: str) -> Dict:
        """Execute SQL query with automatic fallback to alternative product columns"""
        # First, try the original query
        result = self.execute_query(sql_query)
        
        # If successful but no results, and query contains product_group, try fallbacks
        if result["success"] and result["row_count"] == 0 and "product_group" in sql_query.lower():
            print("  ℹ️  No results from product_group, trying product_group_1...")
            
            # Try product_group_1
            fallback_query_1 = sql_query.replace("product_group", "product_group_1")
            result = self.execute_query(fallback_query_1)
            
            # If still no results, try product_group_2
            if result["success"] and result["row_count"] == 0:
                print("  ℹ️  No results from product_group_1, trying product_group_2...")
                fallback_query_2 = sql_query.replace("product_group", "product_group_2")
                result = self.execute_query(fallback_query_2)
                
                if result["success"] and result["row_count"] > 0:
                    result["fallback_used"] = "product_group_2"
            elif result["success"] and result["row_count"] > 0:
                result["fallback_used"] = "product_group_1"
        
        return result
    
    def format_response(self, query_result: Dict, execution_result: Dict) -> str:
        """Format the final response for the user"""
        
        if not execution_result["success"]:
            return f"❌ Query execution failed: {execution_result['error']}"
        
        results = execution_result["results"]
        columns = execution_result["columns"]
        
        if not results:
            return "No results found for your query."
        
        # Format response based on result type
        response = f"📊 **Query Results**\n\n"
        response += f"_{query_result.get('explanation', 'Query executed successfully')}_\n"
        
        # Show if fallback column was used
        if execution_result.get("fallback_used"):
            response += f"\n⚠️ _Note: Results found using '{execution_result['fallback_used']}' (no matches in primary product_group)_\n"
        
        response += "\n"
        
        # If single value (aggregate), show it prominently
        if len(results) == 1 and len(results[0]) == 1:
            value = results[0][0]
            if isinstance(value, (int, float)):
                response += f"**Result:** {value:,.2f}"
            else:
                response += f"**Result:** {value}"
        else:
            # Table format for multiple results
            response += "```\n"
            # Header
            response += " | ".join(columns) + "\n"
            response += "-" * (len(" | ".join(columns))) + "\n"
            
            # Rows (limit to first 20)
            for row in results[:20]:
                formatted_row = []
                for val in row:
                    if isinstance(val, float):
                        formatted_row.append(f"{val:,.2f}")
                    else:
                        formatted_row.append(str(val))
                response += " | ".join(formatted_row) + "\n"
            
            if len(results) > 20:
                response += f"\n... and {len(results) - 20} more rows\n"
            
            response += "```\n"
            response += f"\n**Total rows:** {len(results)}"
        
        return response
    
    def chat(self, user_query: str) -> str:
        """Main chat interface - handle user query end-to-end"""
        
        print(f"\n🤔 Processing: {user_query}")
        
        # Step 1: Convert to SQL
        print("🔄 Converting to SQL with Llama 3.1...")
        sql_result = self.query_to_sql(user_query)
        
        if not sql_result['sql']:
            return f"❌ Could not generate SQL query: {sql_result.get('explanation', 'Unknown error')}"
        
        print(f"📝 Generated SQL: {sql_result['sql']}")
        
        # Step 2: Execute query with automatic fallback to alternative product columns
        print("⚡ Executing query...")
        execution_result = self.execute_query_with_fallback(sql_result['sql'])
        
        # Step 3: Format response
        response = self.format_response(sql_result, execution_result)
        
        return response


# Usage Example
if __name__ == "__main__":
    # Initialize chatbot with Ollama
    chatbot = SQLChatbotAgent(
        db_path='sales_data.db',
        ollama_url='http://localhost:11434',
        model='llama3.1'
    )
    
    # Example queries
    test_queries = [
        "What is the sales value of Product X in March?",
        "Total quantity sold across all products in 2024",
        "Show me sales values for all countries in January",
        "What's the average sales value per product category?",
        "Give me the top 5 products by quantity sold"
    ]
    
    print("=" * 60)
    print("SQL CHATBOT (Powered by Llama 3.1 via Ollama)")
    print("=" * 60)
    
    # Interactive mode
    while True:
        user_input = input("\n💬 You: ")
        
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("👋 Goodbye!")
            break
        
        response = chatbot.chat(user_input)
        print(f"\n🤖 Assistant:\n{response}")