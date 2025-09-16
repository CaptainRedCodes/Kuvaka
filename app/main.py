import uvicorn
from fastapi import FastAPI

from .models import Base, engine
from .models import Csv_input, Offer, Result
from .router import router
Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def root():
    return {"message": "FastAPI running on Render/Railway"}

app.include_router(router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
