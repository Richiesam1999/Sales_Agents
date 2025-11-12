# Product Lookup Configuration Guide

## Overview
The SQL chatbot has been configured to prioritize product lookups in the correct hierarchy as requested.

## Product Column Hierarchy

### 1. **product_group** (PRIMARY)
- **Priority**: Search FIRST
- **Description**: The main product group column with most detailed categorization
- **Unique values**: 21 distinct product groups
- **Examples**: Hip Screw, Liner PS, Patella, Femoral PS, Tibial Base Plate, etc.

### 2. **product_group_1** (ALTERNATIVE)
- **Priority**: Search if no results from product_group
- **Description**: Broader product category
- **Unique values**: 2 categories
- **Examples**: Hip, Knee

### 3. **product_group_2** (SECONDARY ALTERNATIVE)
- **Priority**: Search if no results from product_group_1
- **Description**: Brand-level grouping
- **Unique values**: 4 categories
- **Examples**: Latitud, Freedom, PCK + STBP, Libertas

### 4. **brand**
- **Separate field**: Used specifically when asking about brands
- **Unique values**: 4 brands
- **Examples**: Freedom, Latitud, Libertas, PCK + STBP

## How It Works

### LLM Instruction
The SQL chatbot's system prompt has been updated to:
1. Always use `product_group` column FIRST for product searches
2. Include clear examples showing `product_group` usage
3. Explain the hierarchy in the schema documentation

### Automatic Fallback
The `execute_query_with_fallback()` method automatically:
1. Executes the query with `product_group` first
2. If no results found, automatically retries with `product_group_1`
3. If still no results, retries with `product_group_2`
4. Informs the user which column was used to find results

### Example Queries

**Query**: "Show me sales for Hip Screw in March"
```sql
-- Generated SQL (uses product_group first):
SELECT SUM(value) as total_value 
FROM sales_facts 
WHERE metric_type='Value' 
  AND LOWER(product_group) LIKE '%hip screw%' 
  AND period='Mar'
```

**Query**: "Total quantity for Hip products"
```sql
-- Will first try:
SELECT SUM(value) as total 
FROM sales_facts 
WHERE metric_type='Quantity' 
  AND LOWER(product_group) LIKE '%hip%'

-- If no results, automatically retries with:
SELECT SUM(value) as total 
FROM sales_facts 
WHERE metric_type='Quantity' 
  AND LOWER(product_group_1) LIKE '%hip%'
```

## User Notifications

When fallback columns are used, the chatbot will display:

```
⚠️ Note: Results found using 'product_group_1' (no matches in primary product_group)
```

This ensures transparency about which data source was used.

## Testing

Run the test script to verify the configuration:
```bash
python test_product_lookup.py
```

This will show:
- Unique values in each product column
- Sample data from each column
- Configured lookup priority

## Files Modified

1. **sql_chatbot.py**:
   - Updated `get_schema_info()` to document column hierarchy
   - Updated `query_to_sql()` system prompt with product lookup rules
   - Added `execute_query_with_fallback()` method
   - Updated `format_response()` to show fallback usage
   - Updated `chat()` to use fallback logic

2. **test_product_lookup.py**:
   - Created test script to analyze product columns

## Summary

✅ Product lookups now prioritize `product_group` (21 distinct values)
✅ Automatic fallback to `product_group_1` (2 categories) if needed
✅ Final fallback to `product_group_2` (4 categories) if still no results
✅ User is notified when fallback columns are used
✅ LLM is instructed to use correct column hierarchy
