import pandas as pd
import mysql.connector
from sqlalchemy import create_engine
import logging

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

CSV_FILE = "data.csv"
PRODUCT_TABLE_NAME = 'product'

DB_CONFIG = {
    "host": "mysql",
    "user": "root",
    "password": "root",
    "database": "product_sales"
}

def initialize_db():
    conn = mysql.connector.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password']
    )
    
    cursor = conn.cursor()
    
    # Create the database if it doesn't exist
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
    
    # Select the database
    cursor.execute(f"USE {DB_CONFIG['database']}")
    
    # Create table if it doesn't exist
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {PRODUCT_TABLE_NAME} (
        date VARCHAR(20) NOT NULL,
        week_day VARCHAR(20) NOT NULL,
        hour VARCHAR(20) NOT NULL,
        ticket_number VARCHAR(20) NOT NULL,
        waiter VARCHAR(100) NOT NULL,
        product_name VARCHAR(100) NOT NULL,
        quantity INT NOT NULL,
        unitary_price DECIMAL(10, 2) NOT NULL,
        total INT NOT NULL
    );
    """)
    
    # Init only if the table is empty
    cursor.execute(f"SELECT COUNT(*) FROM {PRODUCT_TABLE_NAME}")
    row_count = cursor.fetchone()[0]

    if row_count == 0:
        df = pd.read_csv(CSV_FILE)
        connection_string = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:3306/{DB_CONFIG['database']}"
        # Create the engine
        engine = create_engine(connection_string) 
        df.to_sql(PRODUCT_TABLE_NAME, engine, if_exists='append', index=False)
        logger.info(f"{len(df)} rows from {CSV_FILE} loaded into {DB_CONFIG['database']} ({PRODUCT_TABLE_NAME})")
        engine.dispose()
    else:
        logger.info(f"Table {PRODUCT_TABLE_NAME} with {row_count} rows already exists in {DB_CONFIG['database']}, skipping initialization")
   
    # Commit and close connection
    conn.commit()
    conn.close()
    

if __name__ == "__main__":
    initialize_db()
