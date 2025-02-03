from fastapi import  APIRouter
from pydantic import BaseModel
from ..models import translation_model
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    table_def: str

@router.post("/to_sql")
async def question_to_sql_query(request: QueryRequest):
    """
    Translate a natural language question into a SQL query and execute it.

    Args:
        request (QueryRequest): A request object containing the user's question in natural language.

    Returns:
        dict: A dictionary containing the translated SQL query.
    """
   
    logger.debug('Received question %s and table definition %s', request.query, request.table_def)
    translated_query = translation_model.question_to_sql(request.query, request.table_def)
    return {"sql_query": translated_query}
