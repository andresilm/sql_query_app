import sqlite3
import torch
from transformers import AutoTokenizer, T5Tokenizer, AutoModelForCausalLM, T5ForConditionalGeneration
import sqlparse
import pandas as pd
import sqlite3
import sqlparse
import logging

logger = logging.getLogger(__name__)

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

def get_t5_small():
    tokenizer = T5Tokenizer.from_pretrained('t5-small')
    # Load the model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = T5ForConditionalGeneration.from_pretrained('cssupport/t5-small-awesome-text-to-sql')
    model = model.to(device)
    model.eval()
    return "t5", model, tokenizer, device


def get_sqlcoder():
    tokenizer = AutoTokenizer.from_pretrained("defog/sqlcoder-7b-2")

    # load in 4 bits – this is way slower
    model = AutoModelForCausalLM.from_pretrained(
        "defog/sqlcoder-7b-2",
        trust_remote_code=True,
        load_in_4bit=True,
        device_map="auto",
        use_cache=True,
    )

    return "sqlcoder", model, tokenizer, None

def get_model():
    if torch.cuda.is_available():
        logger.debug('Will load LLM model %s', "defog/sqlcoder-7b-2")
        model = get_sqlcoder()
    else:
        logger.debug('Will load LLM model %s', "cssupport/t5-small-awesome-text-to-sql")
        model = get_t5_small()

    return model


model_type, model, tokenizer, device = get_model()


def generate_query_sqlcoder(model, tokenizer, question, schema):
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

    return sqlparse.format(outputs[0].split("[SQL]")[-1], reindent=True)

def generate_query_t5(device, model, tokenizer, question, schema):
    # Combine the schema and the user's question
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
    inputs = tokenizer(prompt, padding=True, truncation=True, return_tensors="pt").to(device)
    
    # Forward pass
    with torch.no_grad():
        outputs = model.generate(**inputs, max_length=512)
    
    # Decode the output IDs to a string (SQL query in this case)
    generated_sql = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    return generated_sql

def translate_to_sql(query: str, schema: str):
    logger.debug('Predicting...')
    result = None
    if model_type == "sqlcoder":
        result = generate_query_sqlcoder(model, tokenizer, query, schema)
    elif  model_type == "t5":
        logger.info('Loaded LLM model %s', model_type)
        result = generate_query_t5(device, model, tokenizer, query, schema)
    else:
        raise ValueError('Invalid model type %s', model_type)
    logger.debug('Finished predicting')
    return result
  


def do_query(db, query):
    cursor = db.cursor()
    # Execute the schema to create the table
    cursor.execute(query)
    results = cursor.fetchall()
    return results


def main():
    create_table_query = get_table_create_query(CSV_FILE, DB_NAME, TABLE_NAME)
   # print(f'Loading {CSV_FILE} into {DB_NAME}')
   # load_csv_to_sqlite(CSV_FILE, DB_NAME, TABLE_NAME)
    db = sqlite3.connect(DB_NAME)

    
    print(f'CUDA: {torch.cuda.is_available()}')

    available_memory = torch.cuda.get_device_properties(0).total_memory
    print(f'CUDA Memory: {int(available_memory / 1024 / 1024)} MB')

    # Example natural language questions
    questions = [
        "What is the most bought product on Fridays?",
         "What is the least bought product on Mondays?"
    ]

    # Generate SQL queries for each question
    for question in questions:
        print(f"Question:\n{question}")
        sql_query = translate_to_sql(question, SCHEMA)
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