import sqlite3
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import sqlparse
import pandas as pd
import sqlite3
import sqlparse

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

def load_csv_to_sqlite(csv_file, db_name, table_name):
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


def generate_query(model, tokenizer, question, schema):
    prompt = f"""### Task
Generate a SQL query to answer [QUESTION]{question}[/QUESTION]

### Instructions
- If you cannot answer the question with the available database schema, return 'I do not know'
- Remember that revenue is price multiplied by quantity
- Remember that cost is supply_price multiplied by quantity

### Database Schema
This query will run on a database whose schema is represented in this string:
{schema}

### Answer
Given the database schema, here is the SQL query that answers [QUESTION]{question}[/QUESTION]
[SQL]
"""
  
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    generated_ids = model.generate(
        **inputs,
        num_return_sequences=1,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.eos_token_id,
        max_new_tokens=400,
        do_sample=False,
        num_beams=1,
    )
    outputs = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)

    torch.cuda.empty_cache()
    torch.cuda.synchronize()
    # empty cache so that you do generate more results w/o memory crashing
    # particularly important on Colab – memory management is much more straightforward
    # when running on an inference service
    return sqlparse.format(outputs[0].split("[SQL]")[-1], reindent=True)
     
def interpret_query_results(model, tokenizer, question, schema, sql_query, results):
    prompt = f"""### Task
Given the original question [QUESTION]{question}[/QUESTION],
the SQL query [SQL_QUERY]{sql_query}[/SQL_QUERY]  that looks in the DB
that has a schema [SCHEMA]{schema}[/SCHEMA], 
we obtained results to answer the question by running the sql_query and then obtained the results [RESULTS]{results}[/RESULTS] from the database.
Explain these results trying to answer the original question, in natural language
"""
  


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

    model_name = "defog/sqlcoder-7b-2"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    print(f'CUDA: {torch.cuda.is_available()}')

    available_memory = torch.cuda.get_device_properties(0).total_memory
    print(f'CUDA Memory: {int(available_memory / 1024 / 1024)} MB')

    # else, load in 8 bits – this is a bit slower
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        trust_remote_code=True,
        # torch_dtype=torch.float16,
        load_in_4bit=True,
        #quantization_config=bnb_config,
        device_map="auto",
        use_cache=True,
    )


    # Example natural language questions
    questions = [
        "What is the most bought product on Fridays?",
         "What is the least bought product on Mondays?"
    ]

    # Generate SQL queries for each question
    for question in questions:
        print(f"Question:\n{question}")
        sql_query = generate_query(model, tokenizer, question, SCHEMA)
        print(f"Generated SQL Query:\n{sql_query}")
        try:
            result = do_query(db, sql_query)
            print(f'Query result:\n{result}')
           # answer = interpret_query_results(model, tokenizer, question, SCHEMA, sql_query, result)
          #  print(f'Answer to the question:\n{str(answer)}')
        except Exception as e:
            print(e)
            print(f'Bad SQL query: {sql_query}\n')


    db.close()

main()