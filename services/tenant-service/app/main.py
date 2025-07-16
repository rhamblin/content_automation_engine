from fastapi import FastAPI
from app.routers.routes import router

app = FastAPI(title="Org Service")
app.include_router(router)
