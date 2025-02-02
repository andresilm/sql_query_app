import uvicorn
from fastapi import HTTPException, FastAPI, Depends
from pydantic import BaseModel
import os
import requests
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from .database import get_db
from .database import get_database_schema
import logging

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

db_schema = "table product (date,week_day,hour,ticket_number,waiter,product_name,quantity,unitary_price,total)"

app = FastAPI()


query_translator_url = os.getenv('QUERY_TRANSLATOR_URL')


class QuestionRequest(BaseModel):
    question: str


@app.post("/ask")
async def ask_question(request: QuestionRequest, db: AsyncSession = Depends(get_db)):
    try:
        logger.debug("Schema: %s", str(db_schema))
        response = requests.post(f"{query_translator_url}/query_to_sql", json={"query": request.question, "table_def": str(db_schema)})
        if response.status_code != 200:
            logger.debug(f'Received status code %d',  response.status_code)
            raise HTTPException(status_code=response.status_code, detail="Could not connect to query_translator")

        sql_query = response.json().get("translated_query", "Could not get SQL query")
        result = await db.execute(text(sql_query))  
        results = result.fetchall()  
        
        return {"original_question": request.question, "results": str(results)}

    except Exception as e:
        logger.error(e)
       
    

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
