from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from ..query_translator import translate_to_sql
app = FastAPI()

class QueryRequest(BaseModel):
    query: str
    schema: str


@app.post("/query_to_sql")
async def translate_query(request: QueryRequest):
    if not request.query:
        raise HTTPException(status_code=400, detail="El campo 'query' no puede estar vacío")
    translated_query = translate_to_sql(request.query, request.schema)
    return {"sql_query": translated_query}

