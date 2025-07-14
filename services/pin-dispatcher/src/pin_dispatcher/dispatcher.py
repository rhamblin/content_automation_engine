from fastapi import FastAPI

app = FastAPI()

@app.post("/v1/dispatch")
def dispatch():
    return {"Hello": "World"}