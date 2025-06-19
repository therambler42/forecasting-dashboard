
from fastapi import FastAPI
from forecasting_service import run_forecast

app = FastAPI()

@app.get("/run")
def run():
    return run_forecast()

@app.get("/health")
def health():
    return {"status": "ok"}
