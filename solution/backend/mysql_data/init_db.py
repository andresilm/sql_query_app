import os
import pandas as pd
import mysql.connector

MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "mydatabase")
TABLE_NAME = "inferred_table"
CSV_FILE = "/docker-entrypoint-initdb.d/data.csv"

conn = mysql.connector.connect(
    host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DATABASE
)
cursor = conn.cursor()

# Check if the table exists
cursor.execute(f"SHOW TABLES LIKE '{TABLE_NAME}';")
table_exists = cursor.fetchone()

if not table_exists:
    print("Database is empty. Initializing...")

    # Load CSV and infer schema
    df = pd.read_csv(CSV_FILE)
    
    # Infer MySQL data types
    def infer_mysql_type(col):
        if df[col].dtype == "int64":
            return "INT"
        elif df[col].dtype == "float64":
            return "FLOAT"
        else:
            return "VARCHAR(255)"

    columns = ", ".join([f"`{col}` {infer_mysql_type(col)}" for col in df.columns])
    
    # Create table dynamically
    create_table_sql = f"CREATE TABLE {TABLE_NAME} (id INT AUTO_INCREMENT PRIMARY KEY, {columns});"
    cursor.execute(create_table_sql)
    print("Table created successfully.")

    # Insert data
    cols = ", ".join([f"`{col}`" for col in df.columns])
    placeholders = ", ".join(["%s"] * len(df.columns))
    insert_sql = f"INSERT INTO {TABLE_NAME} ({cols}) VALUES ({placeholders})"

    for _, row in df.iterrows():
        cursor.execute(insert_sql, tuple(row))

    conn.commit()
    print("Data imported successfully.")
else:
    print("Database already initialized.")

cursor.close()
conn.close()
