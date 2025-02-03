import uvicorn
from fastapi import  FastAPI
from .routes.query import router as user_question_router
import logging

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

app = FastAPI()
app.include_router(user_question_router, prefix="/query", tags=["Query Translator"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level='debug')