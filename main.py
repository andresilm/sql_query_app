import sqlite3
import os
import torch
from transformers import T5Tokenizer, T5ForConditionalGeneration
from transformers import AutoTokenizer, AutoModelForCausalLM

import pandas as pd
import sqlite3

SCHEMA = ""
DB_NAME = 'database.db'
TABLE_NAME = 'products'
CSV_FILE = 'data.csv'

def get_table_create_query(csv_file, db_name, table_name=TABLE_NAME):
    # Load CSV into Pandas DataFrame
    df = pd.read_csv(csv_file)
    df.waiter = df.waiter.astype(int)
    df.quantity = df.quantity.astype(int)
    df.unitary_price = df.unitary_price.astype(int)
    df.total = df.total.astype(int)
    # Connect to SQLite (create if not exists)
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    # Generate schema based on DataFrame structure
    global SCHEMA;
    columns = ",\n".join([f'"{col}" VARCHAR(100)' if df[col].dtype == 'object' else f'"{col}" INTEGER' for col in df.columns])
    # Create table
    SCHEMA = f'TABLE {table_name} ({columns});'

    return "CREATE IF NOT EXISTS " + SCHEMA

def load_csv_to_sqlite(csv_file, db_name, create_table_query, table_name):
    # Load CSV into Pandas DataFrame
    df = pd.read_csv(csv_file)
    # Connect to SQLite (create if not exists)
    conn = sqlite3.connect(db_name)
    # Insert sample data into the database
    df.to_sql(table_name, conn, if_exists='append', index=False)
    # Commit and close connection
    conn.commit()
    conn.close()
    
    print(f"{len(df)} rows from {csv_file} successfully loaded into {db_name} ({table_name})")



def text_to_sql(device, model, tokenizer, question, schema):
    # Combine the schema and the user's question
    prompt = f"""### Task
Generate a SQL query to answer question: {question}

### Database Schema
This query will run on a database whose table name and columns are:
{schema}
where
"quantity": number of units sold of the product in that date
"total": amount of money due to sales of the product in a date
"week_day": Day of the week (Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday)
"date": date in format %m/%d/%y

"""
    print(prompt)
    inputs = tokenizer(prompt, padding=True, truncation=True, return_tensors="pt").to(device)
    
    # Forward pass
    with torch.no_grad():
        outputs = model.generate(**inputs, max_length=512)
    
    # Decode the output IDs to a string (SQL query in this case)
    generated_sql = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    return generated_sql


def do_query(db, query):
    cursor = db.cursor()
    # Execute the schema to create the table
    cursor.execute(query)
    results = cursor.fetchall()
    return results

def main():
    create_table_query = get_table_create_query(CSV_FILE, DB_NAME, TABLE_NAME)
    print(f'Loading {CSV_FILE} into {DB_NAME}')
    load_csv_to_sqlite(CSV_FILE, DB_NAME, create_table_query, TABLE_NAME)
    db = sqlite3.connect(DB_NAME)
    tokenizer = T5Tokenizer.from_pretrained('t5-small')

    # Load the model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = T5ForConditionalGeneration.from_pretrained('cssupport/t5-small-awesome-text-to-sql')
    model = model.to(device)
    model.eval()
    


    # Example natural language questions
    questions = [
        "What is the most bought product on Fridays?",
    ]
    print(f'SCHEMAAAAA {SCHEMA}')
    # Generate SQL queries for each question
    for question in questions:
        print(f"Question:\n{question}")
        sql_query = text_to_sql(device, model, tokenizer, question, SCHEMA)
        #sql_query = sql_query.replace('\"', '\'')
        sql_query = sql_query.replace('Fridays', 'Friday')
        sql_query = sql_query.replace('Mondays', 'Monday')


        print(f"Generated SQL Query:\n{sql_query}")
        try:
            result = do_query(db, sql_query)
            print(f'Query result:\n{result}')
        except Exception as e:
            print(e)
            print(f'Bad SQL query: {sql_query}\n')


    db.close()

main()