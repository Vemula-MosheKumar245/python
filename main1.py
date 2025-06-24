from fastapi import HTTPException
from fastapi import FastAPI
app = FastAPI()
data_store = {}
@app.post("/")
async def moshe(name : str,number :int):
    data_store[name] = number
    return {"message":f"saved number {number} for the name {name}"}
@app.get("/")
async def moshekumar(name : str):
   if name in data_store:
       return{"name":name,"number":data_store[name]}
   else:
       raise HTTPException(status_code=404,detail="name not found")