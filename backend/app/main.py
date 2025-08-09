from fastapi import FastAPI
from .db import engine, Base
from .auth import router as auth_router
from .expenses import router as expenses_router

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(expenses_router)
