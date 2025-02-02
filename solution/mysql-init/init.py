import pandas as pd
import mysql.connector
from sqlalchemy import create_engine

CSV_FILE = "data.csv"
PRODUCTS_TABLE_NAME = 'products'

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
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS product (
        id INT AUTO_INCREMENT PRIMARY KEY,
        date DATE NOT NULL,
        week_day VARCHAR(20) NOT NULL,
        hour TIME NOT NULL,
        ticket_number INT NOT NULL,
        waiter VARCHAR(100) NOT NULL,
        product_name VARCHAR(255) NOT NULL,
        quantity INT NOT NULL,
        unitary_price DECIMAL(10, 2) NOT NULL,
        total DECIMAL(10, 2) NOT NULL
    );
    """)

    df = pd.read_csv(CSV_FILE)
    connection_string = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:3306/{DB_CONFIG['database']}"
    # Create the engine
    engine = create_engine(connection_string) 
    df.to_sql(PRODUCTS_TABLE_NAME, engine, if_exists='append', index=False)
    # Commit and close connection
    conn.commit()
    conn.close()
    
    print(f"{len(df)} rows from {CSV_FILE} successfully loaded into {DB_CONFIG['database']} ({PRODUCTS_TABLE_NAME})")

if __name__ == "__main__":
    initialize_db()
