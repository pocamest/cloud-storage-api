from fastapi import FastAPI
from sqlalchemy import text

from app.core.dependencies import SessionDep
from app.core.logging import setup_logging

setup_logging()

app = FastAPI(title="Cloud storage API")


@app.get("/")
async def root(session: SessionDep) -> dict[str, str]:
    try:
        await session.execute(text("SELECT 1"))
        return {"message": "Cloud storage API"}

    except Exception as e:
        return {"error_message": str(e)}
