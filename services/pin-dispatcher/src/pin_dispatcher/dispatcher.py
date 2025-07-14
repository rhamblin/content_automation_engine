from fastapi import FastAPI

app = FastAPI()

@app.post("/dispatch")
def dispatch():
    return {"Hello": "World"}