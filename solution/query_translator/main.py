import uvicorn
from fastapi import HTTPException, FastAPI
from pydantic import BaseModel
from .query_translator import translate_to_sql
import logging

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

app = FastAPI()

class QueryRequest(BaseModel):
    query: str
    table_def: str


@app.post("/query_to_sql")
async def translate_query(request: QueryRequest):
    if not request.query:
        raise HTTPException(status_code=400, detail="El campo 'query' no puede estar vacío")
    logger.debug('Received question %s and table definition %s', request.query, request.table_def)
    translated_query = translate_to_sql(request.query, request.table_def)
    return {"sql_query": translated_query}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level='debug')
