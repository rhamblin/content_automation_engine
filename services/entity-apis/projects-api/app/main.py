from fastapi import FastAPI
from app.routers.routes import router

app = FastAPI(title="Projects API")
app.include_router(router)
