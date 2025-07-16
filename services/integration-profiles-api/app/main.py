from fastapi import FastAPI
from app.routers.routes import router

app = FastAPI(title="Integration Profiles API")
app.include_router(router)
