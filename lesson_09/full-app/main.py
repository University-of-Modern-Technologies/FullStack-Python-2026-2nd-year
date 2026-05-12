import logging

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.routes import auth
from src.routes import todos


app = FastAPI()
logger = logging.getLogger("uvicorn.error")

app.include_router(auth.router, prefix="/api")
app.include_router(todos.router, prefix="/api")


@app.get("/")
def read_root():
    return {"message": "TODO Application v1.0"}


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "message": "Application is running"}


@app.get("/readyz")
async def readyz(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT 1"))
        result = result.fetchone()
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database is not configured correctly",
            )
        return {"status": "ok", "message": "Application is ready"}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error connecting to the database")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error connecting to the database",
        )
