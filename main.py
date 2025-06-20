from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Forecasting dashboard minimal"}

@app.get("/forecast")
async def forecast():
    return {"forecast": [1, 2, 3]}