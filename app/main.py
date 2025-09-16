import uvicorn
from fastapi import FastAPI

from .models import Base, engine
from .models import Csv_input, Offer, Result

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def root():
    return {"message": "FastAPI running on Render/Railway"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
