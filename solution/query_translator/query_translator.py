import torch
from transformers import AutoTokenizer, T5Tokenizer, AutoModelForCausalLM, T5ForConditionalGeneration
import sqlparse


def get_model():
    if torch.cuda.is_available():
        model = get_sqlcoder()
    else:
        model = get_t5_small()

    return model


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
    inputs = tokenizer(prompt, padding=True, truncation=True, return_tensors="pt").to(device)
    
    # Forward pass
    with torch.no_grad():
        outputs = model.generate(**inputs, max_length=512)
    
    # Decode the output IDs to a string (SQL query in this case)
    generated_sql = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    return generated_sql

def translate_to_sql(query: str, schema: str):
    if model_type == "sqlcoder":
        return generate_query_sqlcoder(model, tokenizer, query, schema)
    elif  model_type == "t5":
        return generate_query_t5(device, model, tokenizer, query, schema)
    else:
        raise ValueError('Invalid model type %s', model_type)
