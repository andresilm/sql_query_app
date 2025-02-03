from fastapi import HTTPException, Depends, status, APIRouter
from pydantic import BaseModel
import os
import requests
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
import logging
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

query_translator_url = os.getenv('QUERY_TRANSLATOR_URL')

class QuestionRequest(BaseModel):
    question: str

router = APIRouter()

table_schema = None  # to be initialized by below method on startup

@router.on_event("startup")
async def startup_event():
    global table_schema
    async for db in get_db():
        try:
            query = f"""
SELECT COLUMN_NAME, DATA_TYPE 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'products'
"""
            result = await db.execute(text(query))
            table_schema = result.fetchall()
            cols_description = "\n".join([f"column_name:{col[0]}, column_type:{col[1]}" for col in table_schema])
            table_schema = f'Table products: {cols_description}'
        except ProgrammingError as e:
            logger.error(f"SQL syntax error: {e}")
        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
        except Exception as e:
            logger.error(e)
        finally:
            await db.close()
        break



@router.post("/query_sales", status_code=status.HTTP_200_OK)
async def query_sales(request: QuestionRequest, db: AsyncSession = Depends(get_db)):
    try:
        logger.debug("Table schema: %s", table_schema)
        response = requests.post(
            f"{query_translator_url}/query/to_sql",
            json={"query": request.question, "table_def": table_schema}
        )
        if response.status_code != status.HTTP_200_OK:
            logger.debug(f"Received status code %d", response.status_code)
            raise HTTPException(status_code=response.status_code, detail="Could not connect to query_translator")

        sql_query = response.json().get("translated_query", "Could not get SQL query")
        result = await db.execute(text(sql_query))
        results = result.fetchall()

        return {"original_question": request.question, "results": str(results)}

    except ProgrammingError as e:
        logger.error(f"SQL syntax error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="SQL syntax error")
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
    except Exception as e:  # any other exception
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

