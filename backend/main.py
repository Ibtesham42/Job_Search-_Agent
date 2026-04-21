import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from pipeline import run_pipeline
from storage import save_jobs_csv, save_jobs_json

app = FastAPI(title="Job Extraction API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExtractRequest(BaseModel):
    urls: List[str]

class ExtractResponse(BaseModel):
    success: bool
    total_jobs: int
    jobs: List[dict]
    message: str

@app.get("/")
def root():
    return {
        "message": "Job Extraction API is running",
        "endpoints": ["POST /extract-jobs/", "GET /health"]
    }

@app.get("/health")
def health():
    from datetime import datetime
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/extract-jobs/", response_model=ExtractResponse)
def extract_jobs_endpoint(request: ExtractRequest):
    if not request.urls:
        raise HTTPException(status_code=400, detail="No URLs provided")

    try:
        jobs = run_pipeline(request.urls)
        save_jobs_csv(jobs)
        save_jobs_json(jobs)

        return ExtractResponse(
            success=True,
            total_jobs=len(jobs),
            jobs=jobs,
            message=f"Successfully extracted {len(jobs)} jobs"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)