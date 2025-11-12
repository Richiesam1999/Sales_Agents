import pandas as pd
import sqlite3
from datetime import datetime
import re
from pathlib import Path

class DataTransformer:
    """Transform Excel data into normalized SQL database"""
    
    def __init__(self, excel_path):
        self.excel_path = excel_path
        self.df = None
        
    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names: lower-case, trim, replace non-alnum with underscore"""
        def norm(col: str) -> str:
            col = col.strip().lower()
            # Replace non-alphanumeric with underscore
            col = re.sub(r"[^0-9a-z]+", "_", col)
            col = re.sub(r"_+", "_", col).strip("_")
            return col
        df = df.copy()
        df.columns = [norm(c) for c in df.columns]
        
        # Handle duplicate column names by appending numbers
        cols = df.columns.tolist()
        seen = {}
        new_cols = []
        for col in cols:
            if col in seen:
                seen[col] += 1
                new_cols.append(f"{col}_{seen[col]}")
            else:
                seen[col] = 0
                new_cols.append(col)
        df.columns = new_cols
        
        return df
        
    def load_and_clean_data(self):
        """Load tabular file (Excel or CSV) and perform initial cleaning"""
        path = Path(self.excel_path)
        suffix = path.suffix.lower()

        try:
            if suffix in {'.xlsx', '.xlsm', '.xltx', '.xltm'}:
                # Explicitly set engine to avoid pandas guessing errors
                self.df = pd.read_excel(self.excel_path, engine='openpyxl')
            elif suffix == '.csv':
                self.df = pd.read_csv(self.excel_path)
            else:
                # Try reading as modern Excel as a fallback (for files without extension)
                self.df = pd.read_excel(self.excel_path, engine='openpyxl')
        except Exception as e:
            raise ValueError(
                "Could not read the uploaded file. Please upload a valid .xlsx Excel file or a .csv file."
                f" Details: {e}"
            )
        
        # Normalize column names
        self.df = self._normalize_columns(self.df)
        
        print(f"Loaded {len(self.df)} rows with {len(self.df.columns)} columns")
        return self.df
    
    def transform_to_long_format(self):
        """Transform wide format to long format (unpivot)"""
        
        # Identify metric columns by pattern: <mon>_(qty|value)
        months = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
        metric_cols = []
        for col in self.df.columns:
            for m in months:
                if col.startswith(f"{m}_") and (col.endswith("_qty") or col.endswith("_value")):
                    metric_cols.append(col)
                    break
        
        # All other columns are identifiers/static dims (including 'year')
        id_vars = [c for c in self.df.columns if c not in metric_cols]
        
        # Ensure we have metric columns to melt
        if not metric_cols:
            raise ValueError("No metric columns found matching pattern <month>_(qty|value)")
        
        # Manual melt using stack/unstack to avoid pandas 2.x bug
        # Split dataframe into id columns and metric columns
        df_id = self.df[id_vars].copy()
        df_metrics = self.df[metric_cols].copy()
        
        # Add index to maintain row relationships
        df_id['_temp_idx'] = range(len(df_id))
        df_metrics['_temp_idx'] = range(len(df_metrics))
        
        # Melt metrics using stack which is more reliable
        df_metrics_stacked = df_metrics.set_index('_temp_idx').stack().reset_index()
        df_metrics_stacked.columns = ['_temp_idx', 'metric_period', 'value']
        
        # Merge with id columns
        df_long = df_id.merge(df_metrics_stacked, on='_temp_idx')
        df_long = df_long.drop('_temp_idx', axis=1)
        
        # Parse metric and period from column name, e.g., "apr_qty" -> (Quantity, Apr)
        def parse_metric(col_name: str):
            col_name = str(col_name).lower()
            metric = 'Unknown'
            if col_name.endswith('_qty'):
                metric = 'Quantity'
            elif col_name.endswith('_value'):
                metric = 'Value'
            return metric
        
        def parse_period(col_name: str):
            col_name = str(col_name).lower()
            for m in months:
                if col_name.startswith(f"{m}_"):
                    return m.capitalize()
            return 'Unknown'
        
        df_long['metric_type'] = df_long['metric_period'].apply(parse_metric)
        df_long['period'] = df_long['metric_period'].apply(parse_period)
        
        # Drop the combined column
        df_long = df_long.drop('metric_period', axis=1)
        
        # Remove rows with null values (or empty strings)
        df_long = df_long.dropna(subset=['value'])
        
        print(f"Transformed to {len(df_long)} rows in long format")
        return df_long
    
    def extract_metric(self, col_name):
        """Extract metric type from column name"""
        # Examples: Mar_Qty -> Qty, Sales_Value -> Sales_Value
        metrics_map = {
            'Qty': 'Quantity',
            'Sales_Value': 'Sales_Value',
            'Contribution': 'Contribution',
            'Value': 'Value'
        }
        
        for key in metrics_map:
            if key in col_name:
                return metrics_map[key]
        return 'Unknown'
    
    def extract_period(self, col_name):
        """Extract period (month) from column name"""
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        for month in months:
            if month in col_name:
                return month
        return 'Unknown'
    
    def extract_year(self, col_name):
        """Extract year from column name"""
        # Look for 4-digit year
        year_match = re.search(r'20\d{2}', col_name)
        if year_match:
            return year_match.group()
        
        # Default to current year if not found
        return str(datetime.now().year)
    
    def create_database_schema(self, db_path='sales_data.db'):
        """Create SQLite database with optimized schema"""
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create main sales fact table (includes common dimensions)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales_facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year TEXT,
            entity TEXT,
            zsm TEXT,
            sales_head TEXT,
            continent TEXT,
            country TEXT,
            division TEXT,
            zone TEXT,
            product_group TEXT,
            product_group_1 TEXT,
            product_group_2 TEXT,
            brand TEXT,
            city TEXT,
            metric_type TEXT,
            period TEXT,
            value REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create indexes for faster querying
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_brand 
        ON sales_facts(brand)
        ''')
        
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_period_year 
        ON sales_facts(period, year)
        ''')
        
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_metric 
        ON sales_facts(metric_type)
        ''')
        
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_country 
        ON sales_facts(country)
        ''')
        
        conn.commit()
        conn.close()
        print(f"Database schema created at {db_path}")
    
    def load_to_database(self, df_long, db_path='sales_data.db'):
        """Load transformed data into SQLite database"""
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Prepare data for insertion
        df_long_clean = df_long.copy()
        
        # df_long already has normalized columns; rename to match schema
        column_mapping = {
            'year': 'year',
            'entity': 'entity',
            'zsm': 'zsm',
            'sales_head': 'sales_head',
            'continent': 'continent',
            'country': 'country',
            'division': 'division',
            'zone': 'zone',
            'product_group': 'product_group',
            'product_group_1': 'product_group_1',
            'product_group_2': 'product_group_2',
            'brand': 'brand',
            'city': 'city',
            'metric_type': 'metric_type',
            'period': 'period',
            'value': 'value'
        }
        df_long_clean = df_long_clean.rename(columns=column_mapping)
        
        # Keep only the columns defined in schema if present
        allowed_cols = list(column_mapping.values())
        existing_cols = [c for c in allowed_cols if c in df_long_clean.columns]
        df_long_clean = df_long_clean[existing_cols]
        
        # Load to database (replace, then recreate indexes)
        df_long_clean.to_sql('sales_facts', conn, if_exists='replace', index=False)
        
        # Recreate indexes lost due to replace
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_brand ON sales_facts(brand)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_period_year ON sales_facts(period, year)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metric ON sales_facts(metric_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_country ON sales_facts(country)')
        conn.commit()
        
        row_count = len(df_long_clean)
        conn.close()
        
        print(f"Loaded {row_count} rows into database")
        return row_count

# Usage Example
if __name__ == "__main__":
    # Initialize transformer
    transformer = DataTransformer('MLSIPL.csv')
    
    # Step 1: Load and clean
    df = transformer.load_and_clean_data()
    
    # Step 2: Transform to long format
    df_long = transformer.transform_to_long_format()
    
    # Step 3: Create database schema
    transformer.create_database_schema()
    
    # Step 4: Load to database
    transformer.load_to_database(df_long)
    
    print("\n✓ Data transformation and loading complete!")