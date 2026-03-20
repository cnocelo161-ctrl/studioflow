from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel
from studioflow.processor import generate_project_output

app = FastAPI()

class IntakeRequest(BaseModel):
    client_name: Optional[str] = None
    project_type: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    budget: Optional[str] = None
    timeline: Optional[str] = None

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/generate")
def generate(data: IntakeRequest):
    result = generate_project_output(data)
    return result
