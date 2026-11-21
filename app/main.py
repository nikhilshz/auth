from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import admin, auth, password_reset, users
from app.db.session import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(password_reset.router)
