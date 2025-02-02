import torch
from transformers import AutoTokenizer, T5Tokenizer, AutoModelForCausalLM, T5ForConditionalGeneration
import sqlparse
import logging

logger = logging.getLogger(__name__)

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
        logger.info('Will load LLM model %s', "defog/sqlcoder-7b-2")
        model = get_sqlcoder()
    else:
        logger.info('Will load LLM model %s', "cssupport/t5-small-awesome-text-to-sql")
        model = get_t5_small()

    return model


model_type, model, tokenizer, device = get_model()


def generate_query_sqlcoder(model, tokenizer, question, schema):
    prompt = f"""### Task
Generate a SQL query to answer [QUESTION]{question}[/QUESTION]

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
    prompt = f""" Task:
    Generate a SQL query to answer the question: {question}[/QUESTION]
Context:
This query will run on a database whose schema is represented in this string:
{schema}
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