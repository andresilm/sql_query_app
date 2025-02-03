import uvicorn
from fastapi import FastAPI
from .routes.user_query import router as user_question_router
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


app = FastAPI()
app.include_router(user_question_router, prefix="/db_users", tags=["Database users"])


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
