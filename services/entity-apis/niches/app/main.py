# app/main.py

from fastapi import FastAPI
from app.routers.routes import router

app = FastAPI(
    title="Niches API",
    description="Manage niches and keywords",
)

# Register all routers
app.include_router(router)