import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import sqlparse
import logging
from .query_translation_model import IQuerySqlTranslationModel

logger = logging.getLogger(__name__)


class SqlCoder2Wrapper(IQuerySqlTranslationModel):
    def __init__(self):
        logger.info("Loading SQLCoder2 model")
        self._tokenizer = AutoTokenizer.from_pretrained("defog/sqlcoder-7b-2")
        # load in 4 bits – this is way slower
        self._model = AutoModelForCausalLM.from_pretrained(
            "defog/sqlcoder-7b-2",
            trust_remote_code=True,
            load_in_4bit=True,
            device_map="auto",
            use_cache=True,
        )
        logger.info("[DONE] Loading SQLCoder2 model")


    def question_to_sql(self, question: str, schema: str) -> str:
        prompt = f"""### Task
Generate a SQL query to answer [QUESTION]{question}[/QUESTION]

### Instructions
- If you cannot answer the question with the available database schema, return 'I do not know'

### Database Schema
This query will run on a database whose schema is represented in this string:
{schema}
- When using the name of the table or columns, respect the singular or plural as it appears in the schema 
- Do not confuse "date" which has format %m-%d-%Y with "week_day" which ranges from Monday to Friday

### Answer
Given the database schema, here is the SQL query that answers [QUESTION]{question}[/QUESTION]
[SQL]
"""
        inputs = self._tokenizer(prompt, return_tensors="pt").to("cuda")
        generated_ids = self._model.generate(
            **inputs,
            num_return_sequences=1,
            eos_token_id=self._tokenizer.eos_token_id,
            pad_token_id=self._tokenizer.eos_token_id,
            max_new_tokens=400,
            do_sample=False,
            num_beams=1,
        )
        outputs = self._tokenizer.batch_decode(generated_ids, skip_special_tokens=True)

        torch.cuda.empty_cache()
        torch.cuda.synchronize()

        return sqlparse.format(outputs[0].split("[SQL]")[-1], reindent=True)

