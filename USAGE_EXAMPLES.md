# Sales Agent Usage Examples

## Product Lookup Examples

### Detailed Product Search (uses product_group)
```
Query: "Show me sales for Hip Screw in March 2024"
→ Searches in product_group column first (21 distinct products)
→ If found: Returns results
→ If not found: Automatically tries product_group_1, then product_group_2
```

### Broad Category Search (may use product_group_1)
```
Query: "Total sales for Hip products"
→ First searches product_group for anything with "hip"
→ If no results, searches product_group_1 (Hip/Knee categories)
```

### Brand-Level Search
```
Query: "Sales by Freedom brand"
→ Searches the 'brand' column directly
→ Brand column has: Freedom, Latitud, Libertas, PCK + STBP
```

## General Query Examples

### Time-Based Queries
```
"Sales value in January 2024"
"Quantity sold in Q1" (Jan, Feb, Mar)
"Total sales for 2024"
"Compare March vs April sales"
```

### Aggregation Queries
```
"Total sales by product group"
"Average quantity per month"
"Sum of sales values for each country"
"Top 5 products by revenue"
```

### Filtering Queries
```
"Sales in USA"
"Quantity sold in Europe"
"Products sold by specific sales head"
"Sales for continent Asia"
```

### Complex Queries
```
"Top 3 products by sales in March for Hip category"
"Monthly sales trend for Freedom brand"
"Total quantity by country sorted descending"
```

## Column Reference

### Key Dimensions
- `year` - Year (string)
- `period` - Month (Jan, Feb, Mar, etc.)
- `country` - Country name
- `continent` - Continent name
- `zone` - Sales zone
- `division` - Division
- `city` - City name
- `entity` - Entity name
- `zsm` - ZSM
- `sales_head` - Sales head name

### Product Columns (in priority order)
1. `product_group` - Detailed product (21 types) ⭐ PRIMARY
2. `product_group_1` - Category (Hip/Knee) 
3. `product_group_2` - Brand grouping (4 types)
4. `brand` - Brand name (4 brands)

### Metrics
- `metric_type` - Type of metric:
  - "Quantity" - Unit count
  - "Value" - Sales value/revenue
- `value` - The numeric value

## Running the Chatbot

### Via Main API
```bash
# Start the FastAPI server
python main.py

# The API will be available at http://localhost:8000
# Use POST /query endpoint with your natural language question
```

### Direct Testing
```bash
# Test the chatbot directly
python sql_chatbot.py

# Then type your queries interactively
```

### Example API Request
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Total sales for Hip Screw in March"}'
```

## Understanding Results

### Normal Result
```
📊 Query Results

Getting sales value for Hip Screw in March from product_group

Result: 45,234.50
```

### Fallback Used
```
📊 Query Results

Getting sales value for Hip products

⚠️ Note: Results found using 'product_group_1' (no matches in primary product_group)

Result: 123,456.78
```

This indicates the query didn't find exact matches in product_group, 
but found results in the broader product_group_1 category.

## Tips for Better Results

1. **Be Specific**: "Hip Screw sales in March" is better than "hip sales"
2. **Use Time Periods**: Specify months (Jan-Dec) or years
3. **Metric Type**: Specify "quantity" or "sales value" when needed
4. **Natural Language**: The chatbot understands conversational queries
5. **Check Fallbacks**: If results seem broader than expected, check for fallback notification

## Troubleshooting

### No Results Found
- Try broader terms (e.g., "Hip" instead of specific product names)
- Check spelling of product/country/brand names
- Verify the time period has data

### Unexpected Results
- Check if fallback column was used (indicated in response)
- Verify you're asking about the right metric (Quantity vs Value)
- Ensure date/period format matches (Jan, Feb, etc.)

## Getting Started

1. Upload your Excel/CSV file via the `/upload` endpoint
2. Wait for data transformation (shown in console)
3. Start querying via `/query` endpoint or interactive mode
4. Check `/stats` endpoint to see available data ranges
