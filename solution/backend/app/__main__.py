from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from ..database import get_db
from . import DB_SCHEMA

app = FastAPI()

query_translator_url = os.getenv('QUERY_TRANSLATOR_URL', 'http://query_translator:5000')


class QuestionRequest(BaseModel):
    question: str


@app.post("/ask")
async def ask_question(request: QuestionRequest, db: AsyncSession = Depends(get_db)):
    try:
        
        response = requests.post(f"{query_translator_url}/query_to_sql", json={"query": request.question, "schema": DB_SCHEMA})
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Could not connect to query_translator")

        sql_query = response.json().get("translated_query", "Could not get SQL query")
        result = await db.execute(text(sql_query))  
        results = result.fetchall()  
        
        return {"original_question": request.question, "results": str(results)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
