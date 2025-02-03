import torch
from transformers import T5Tokenizer, T5ForConditionalGeneration
from .query_translation_model import IQuerySqlTranslationModel
import logging


logger = logging.getLogger(__name__)


class T5SmallSqlWrapper(IQuerySqlTranslationModel):
    def __init__(self):
        self._tokenizer = T5Tokenizer.from_pretrained('t5-small')
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._model = T5ForConditionalGeneration.from_pretrained('cssupport/t5-small-awesome-text-to-sql')
        self._model = self._model.to(self._device)
        self._model.eval()

    def question_to_sql(self, question: str, schema: str) -> str:
        # Combine the schema and the user's question
        prompt = f""" Task:
        Generate a SQL query to answer the question: {question}[/QUESTION]
    Context:
    This query will run on a database whose schema is represented in this string:
    {schema}
    """
        
        prompt = """
    " Generate a SQL query to answer the question: {question} 
      given that database has the following tables: {schema}"

"""
        inputs = self._tokenizer(prompt, padding=True, truncation=True, return_tensors="pt").to(self._device)
        
        # Forward pass
        with torch.no_grad():
            outputs = self._model.generate(**inputs, max_length=512)
        
        # Decode the output IDs to a string (SQL query in this case)
        generated_sql = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return generated_sql
