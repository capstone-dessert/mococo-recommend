from fastapi import FastAPI
from api.endpoints import recommend

app = FastAPI()

app.include_router(recommend.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}