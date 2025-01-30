import mysql.connector
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os

DB_NAME = 'database.db'
TABLE_NAME = 'products'
CSV_FILE = 'data/data.csv'

USER = os.getenv('MYSQL_USER')
PASSWORD = os.getenv('MYSQL_PASSWORD')
HOST = os.getenv('MYSQL_HOST')
PORT = os.getenv('MYSQL_PORT', '3306')
DB = os.getenv('MYSQL_DB')

DATABASE_URL = f"mysql+aiomysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}"

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with SessionLocal() as session:
        yield session

def get_database_schema():
    # Connect to MySQL
    conn = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=DB
    )
    
    cursor = conn.cursor()

    # Query to get schema details
    query = f"""
    SELECT 
        TABLE_NAME, 
        COLUMN_NAME, 
        DATA_TYPE, 
        CHARACTER_MAXIMUM_LENGTH, 
        IS_NULLABLE, 
        COLUMN_KEY 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = '{DB}'
    ORDER BY TABLE_NAME, ORDINAL_POSITION;
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    # Format the result as a string
    schema_str = ""
    current_table = None
    
    for row in rows:
        table_name, column_name, data_type, char_max_length, is_nullable, column_key = row
        
        # If we encounter a new table, add a header
        if table_name != current_table:
            schema_str += f"\nTable: {table_name}\n" + "=" * (7 + len(table_name)) + "\n"
            current_table = table_name
        
        # Append column details
        schema_str += f"- {column_name} ({data_type}"
        if char_max_length:
            schema_str += f"({char_max_length})"
        schema_str += f", NULLABLE: {is_nullable}, KEY: {column_key})\n"
    
    # Close connection
    cursor.close()
    conn.close()
    
    return schema_str.strip()





