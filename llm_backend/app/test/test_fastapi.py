from fastapi import FastAPI
from fastapi import APIRouter
from pydantic import BaseModel

app = FastAPI()

router = APIRouter()

class Item(BaseModel):
    name: str
    description: str = None

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.post("/items/")
async def create_item(item: Item):
    return item

@router.get("/")
async def read_router():
    return {"message": "This is from the router"}

@router.post("/items/")
async def create_router_item(item: Item):
    return item

app.include_router(router, prefix="/router")
