# app.py
from fastapi import FastAPI, Request, HTTPException
from pipeline import pipeline
import uvicorn
from haystack.dataclasses import ChatMessage

app = FastAPI()


@app.post("/run")
async def run_pipeline(request: Request):
    data = await request.json()
    id = data.get("id")
    result = pipeline.run({"fetcher": {"id": id}})
    print(result)
    return {"response": result["validator"]["valid_replies"][0].text}


# Entry for running with uvicorn in Docker
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
