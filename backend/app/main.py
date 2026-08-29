from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import initalrouter
from app.core.exception import register_exception_handlers
from app.core.logger import logger

from app.schemas.response import APIResponse
from app.db.session import  get_db,Base,engine
from sqlalchemy import text

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    # Application Startup
    
    logger.info("Application starting...")
    logger.info("Configuration loading.")
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connected.")

    except Exception as e:
        logger.exception(f"Database connection failed:{e}")
        raise
    logger.info("Application startup complete.")
    
    yield

    logger.info("Application shutting down...")

    

    
    # Application Shutdown
     
    logger.info("Application shutting down...")


app = FastAPI(
    title="AI Debugger API",
    version="1.0.0",
    lifespan=lifespan
)


register_exception_handlers(app)

app.include_router(initalrouter.router)