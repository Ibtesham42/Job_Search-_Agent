# ============================================
# COMPLETE JOB AGENT SYSTEM - SINGLE FILE
# ============================================
# Run this file: python job_agent.py
# It will automatically create all necessary folders and files
# ============================================

import os
import sys
import json
import csv
import time
import requests
from typing import List, Optional
from datetime import datetime
from urllib.parse import urlparse

# ============================================
# CREATE PROJECT STRUCTURE
# ============================================

def create_project_structure():
    """Create all necessary folders and files for the project"""
    
    structure = {
        "backend": ["main.py", "pipeline.py", "extractor.py", "parser.py", "models.py", "storage.py"],
        "frontend": ["app.py"],
        "data": ["jobs.csv"]
    }
    
    # Create directories
    for folder in structure.keys():
        os.makedirs(folder, exist_ok=True)
    
    # Create empty jobs.csv if not exists
    if not os.path.exists("data/jobs.csv"):
        with open("data/jobs.csv", "w", encoding="utf-8") as f:
            f.write("Company,Job Title,Description,Location,Posted Date,Apply By,Apply Link,Source\n")
    
    print("[OK] Project structure created")
    print("    Created folders: backend/, frontend/, data/")
    print("    Created file: data/jobs.csv")
    
    return True

# ============================================
# MODELS (models.py content)
# ============================================

MODELS_PY = '''from pydantic import BaseModel
from typing import Optional

class Job(BaseModel):
    company: Optional[str] = None
    job_title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    posted_date: Optional[str] = None
    apply_by: Optional[str] = None
    apply_link: Optional[str] = None
    source: Optional[str] = None
'''

# ============================================
# PARSER (parser.py content)
# ============================================

PARSER_PY = '''import requests
from bs4 import BeautifulSoup
from langchain_community.document_loaders import PyPDFLoader
import tempfile

def fetch_html(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        res = requests.get(url, timeout=15, headers=headers)
        res.raise_for_status()
        return res.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_html(html):
    try:
        soup = BeautifulSoup(html, "html.parser")
        
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
            
        text = soup.get_text(separator="\\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\\n".join(lines)
    except Exception as e:
        print(f"Error parsing HTML: {e}")
        return None

def parse_pdf(url):
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name
        
        loader = PyPDFLoader(tmp_path)
        docs = loader.load()
        
        os.unlink(tmp_path)
        
        return "\\n".join([d.page_content for d in docs])
    except Exception as e:
        print(f"Error parsing PDF {url}: {e}")
        return None
'''

# ============================================
# EXTRACTOR (extractor.py content)
# ============================================

EXTRACTOR_PY = '''from langchain_groq import ChatGroq
import json
import os

# Initialize LLM - You need to set GROQ_API_KEY in .env
def get_llm():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("[WARNING] GROQ_API_KEY not set. Using mock extractor.")
        return None
    return ChatGroq(model="mixtral-8x7b-32768", temperature=0, api_key=api_key)

PROMPT = """Extract job listings from the text below.

Return ONLY valid JSON array. Example:
[
  {
    "company": "Google",
    "job_title": "Software Engineer",
    "description": "Looking for Python developer...",
    "location": "Bangalore",
    "posted_date": "2024-01-15",
    "apply_by": "2024-02-15",
    "apply_link": null
  }
]

Rules:
- If field not found, use null
- No extra text before or after JSON
- Only extract REAL job postings
- Keep description concise (max 500 chars)

TEXT:
"""

def extract_jobs_with_llm(text, llm):
    try:
        response = llm.invoke(PROMPT + text[:10000])
        content = response.content
        
        # Clean response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        data = json.loads(content.strip())
        
        if isinstance(data, dict) and "jobs" in data:
            data = data["jobs"]
        
        if not isinstance(data, list):
            data = [data]
            
        return data
    except Exception as e:
        print(f"LLM extraction error: {e}")
        return []

def extract_jobs_regex(text):
    """Fallback regex-based extraction when LLM not available"""
    import re
    
    jobs = []
    
    # Pattern for job listings
    patterns = {
        "job_title": r"(?:Job Title|Position|Role)[:\s]+([^\n]+)",
        "company": r"(?:Company|Organization)[:\s]+([^\n]+)",
        "location": r"(?:Location)[:\s]+([^\n]+)",
        "posted_date": r"(?:Posted|Date Posted)[:\s]+([^\n]+)"
    }
    
    job = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            job[key] = match.group(1).strip()
    
    if job.get("job_title"):
        job["description"] = text[:500]
        jobs.append(job)
    
    return jobs

def extract_jobs(text):
    llm = get_llm()
    
    if llm:
        jobs = extract_jobs_with_llm(text, llm)
        if jobs:
            return jobs
    
    print("[INFO] Using fallback regex extractor")
    return extract_jobs_regex(text)
'''

# ============================================
# PIPELINE (pipeline.py content)
# ============================================

PIPELINE_PY = '''from parser import fetch_html, parse_html, parse_pdf
from extractor import extract_jobs
import hashlib

def get_content_hash(text):
    return hashlib.md5(text.encode()).hexdigest()

def run_pipeline(urls):
    all_jobs = []
    seen_hashes = set()
    
    print(f"\\n[PIPELINE] Processing {len(urls)} URLs")
    
    for idx, url in enumerate(urls, 1):
        print(f"  [{idx}/{len(urls)}] Processing: {url[:60]}...")
        
        if url.lower().endswith(".pdf"):
            text = parse_pdf(url)
            source = "pdf"
        else:
            html = fetch_html(url)
            if not html:
                print(f"    [FAIL] Could not fetch URL")
                continue
            text = parse_html(html)
            source = "website"
        
        if not text:
            print(f"    [FAIL] Could not extract text")
            continue
        
        print(f"    [OK] Extracted {len(text)} chars")
        
        jobs = extract_jobs(text)
        print(f"    [OK] Found {len(jobs)} jobs")
        
        for job in jobs:
            # Create unique key for deduplication
            unique_str = f"{job.get('company', '')}|{job.get('job_title', '')}|{job.get('location', '')}"
            unique_hash = hashlib.md5(unique_str.encode()).hexdigest()
            
            if unique_hash not in seen_hashes:
                seen_hashes.add(unique_hash)
                job["source"] = source
                job["apply_link"] = url
                all_jobs.append(job)
    
    print(f"\\n[PIPELINE] Total unique jobs: {len(all_jobs)}")
    return all_jobs
'''

# ============================================
# STORAGE (storage.py content)
# ============================================

STORAGE_PY = '''import csv
import json
from datetime import datetime

def save_jobs_csv(jobs, path="data/jobs.csv"):
    try:
        with open(path, "w", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            writer.writerow([
                "Company", "Job Title", "Description", "Location",
                "Posted Date", "Apply By", "Apply Link", "Source", "Extracted At"
            ])
            
            for job in jobs:
                writer.writerow([
                    job.get("company", ""),
                    job.get("job_title", ""),
                    job.get("description", "")[:200],
                    job.get("location", ""),
                    job.get("posted_date", ""),
                    job.get("apply_by", ""),
                    job.get("apply_link", ""),
                    job.get("source", ""),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ])
        
        print(f"[STORAGE] Saved {len(jobs)} jobs to {path}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save CSV: {e}")
        return False

def save_jobs_json(jobs, path="data/jobs.json"):
    try:
        with open(path, "w", encoding='utf-8') as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)
        print(f"[STORAGE] Saved {len(jobs)} jobs to {path}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save JSON: {e}")
        return False

def load_jobs_csv(path="data/jobs.csv"):
    jobs = []
    try:
        with open(path, "r", encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                jobs.append(row)
    except FileNotFoundError:
        pass
    return jobs
'''

# ============================================
# FASTAPI BACKEND (backend/main.py)
# ============================================

BACKEND_MAIN_PY = '''import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
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
    return {"message": "Job Extraction API is running", "endpoints": ["POST /extract-jobs/", "GET /health"]}

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": __import__("datetime").datetime.now().isoformat()}

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
'''

# ============================================
# STREAMLIT FRONTEND (frontend/app.py)
# ============================================

FRONTEND_APP_PY = '''import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime

st.set_page_config(page_title="Job Extraction System", page_icon="", layout="wide")

st.title(" Job Extraction System")
st.markdown("Extract job listings from URLs automatically using AI")

with st.sidebar:
    st.header("Configuration")
    
    api_url = st.text_input("API URL", value="http://localhost:8000")
    
    st.header("About")
    st.info("""
    **How it works:**
    1. Enter job board URLs
    2. System crawls and parses content
    3. AI extracts job details
    4. Results saved to CSV/JSON
    
    **Supported sources:**
    - Job boards (Indeed, LinkedIn, Naukri)
    - Company career pages
    - PDF job descriptions
    """)
    
    st.header("Quick Examples")
    st.code("""
    https://www.naukri.com/
    https://www.linkedin.com/jobs/
    https://example.com/jobs.pdf
    """)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("URLs to Extract")
    
    urls_text = st.text_area(
        "Enter one URL per line",
        height=200,
        placeholder="https://example.com/jobs\\nhttps://company.com/careers.pdf"
    )
    
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        extract_btn = st.button(" Extract Jobs", type="primary", use_container_width=True)
    
    with col_btn2:
        if st.button(" Clear All", use_container_width=True):
            st.rerun()

with col2:
    st.subheader("Status")
    status_placeholder = st.empty()

if extract_btn:
    url_list = [u.strip() for u in urls_text.split("\\n") if u.strip()]
    
    if not url_list:
        st.error("Please enter at least one URL")
    else:
        with st.spinner(f"Processing {len(url_list)} URLs..."):
            try:
                response = requests.post(
                    f"{api_url}/extract-jobs/",
                    json={"urls": url_list},
                    timeout=120
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    status_placeholder.success(f" Found {data['total_jobs']} jobs")
                    
                    st.subheader(f"Extracted Jobs ({data['total_jobs']})")
                    
                    for idx, job in enumerate(data['jobs'], 1):
                        with st.expander(f"{idx}. {job.get('job_title', 'Unknown Position')} @ {job.get('company', 'Unknown Company')}"):
                            col_a, col_b = st.columns(2)
                            
                            with col_a:
                                st.markdown(f"**Company:** {job.get('company', 'N/A')}")
                                st.markdown(f"**Location:** {job.get('location', 'N/A')}")
                                st.markdown(f"**Posted Date:** {job.get('posted_date', 'N/A')}")
                            
                            with col_b:
                                st.markdown(f"**Apply By:** {job.get('apply_by', 'N/A')}")
                                st.markdown(f"**Source:** {job.get('source', 'N/A')}")
                                if job.get('apply_link'):
                                    st.markdown(f"**Apply Link:** [Click Here]({job['apply_link']})")
                            
                            if job.get('description'):
                                st.markdown("**Description:**")
                                st.write(job['description'][:500])
                    
                    # Download section
                    st.subheader("Download Results")
                    
                    col_d1, col_d2 = st.columns(2)
                    
                    with col_d1:
                        try:
                            df = pd.DataFrame(data['jobs'])
                            csv = df.to_csv(index=False)
                            st.download_button(
                                label=" Download CSV",
                                data=csv,
                                file_name=f"jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                        except:
                            pass
                    
                    with col_d2:
                        json_str = json.dumps(data['jobs'], indent=2)
                        st.download_button(
                            label=" Download JSON",
                            data=json_str,
                            file_name=f"jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                
                else:
                    st.error(f"API Error: {response.status_code}")
                    
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to backend. Make sure FastAPI is running: python backend/main.py")
            except Exception as e:
                st.error(f"Error: {e}")

# Show recent jobs from CSV
st.markdown("---")
st.subheader("Recent Extractions")

try:
    df_existing = pd.read_csv("data/jobs.csv")
    if len(df_existing) > 0:
        st.dataframe(df_existing.tail(10), use_container_width=True)
    else:
        st.info("No jobs extracted yet. Run extraction to see results here.")
except:
    st.info("No data file found. Run extraction first.")
'''

# ============================================
# REQUIREMENTS.TXT
# ============================================

REQUIREMENTS_TXT = '''fastapi==0.104.1
uvicorn==0.24.0
streamlit==1.28.1
requests==2.31.0
beautifulsoup4==4.12.2
pydantic==2.4.2
pandas==2.1.3
langchain-groq==0.1.0
langchain-community==0.1.0
pypdf==3.17.0
python-dotenv==1.0.0
'''

# ============================================
# .ENV FILE
# ============================================

ENV_CONTENT = '''# Groq API Key (get from https://console.groq.com)
GROQ_API_KEY=your_groq_api_key_here

# Optional: Other API keys if needed
# OPENAI_API_KEY=
# SERPAPI_API_KEY=
'''

# ============================================
# MAIN FUNCTION TO GENERATE ALL FILES
# ============================================

def generate_all_files():
    """Generate all project files"""
    
    files_to_create = [
        ("backend/models.py", MODELS_PY),
        ("backend/parser.py", PARSER_PY),
        ("backend/extractor.py", EXTRACTOR_PY),
        ("backend/pipeline.py", PIPELINE_PY),
        ("backend/storage.py", STORAGE_PY),
        ("backend/main.py", BACKEND_MAIN_PY),
        ("frontend/app.py", FRONTEND_APP_PY),
        ("requirements.txt", REQUIREMENTS_TXT),
        (".env", ENV_CONTENT),
    ]
    
    for filepath, content in files_to_create:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[CREATED] {filepath}")
    
    # Also create __init__.py files
    with open("backend/__init__.py", "w") as f:
        f.write("# Backend package")
    with open("frontend/__init__.py", "w") as f:
        f.write("# Frontend package")
    
    print("\n[OK] All files created successfully!")

# ============================================
# INSTALL DEPENDENCIES
# ============================================

def install_dependencies():
    """Install required packages"""
    print("\n[INFO] Installing dependencies...")
    print("Run: pip install -r requirements.txt")
    print("Or manually install:")
    print("  pip install fastapi uvicorn streamlit requests beautifulsoup4")
    print("  pip install pydantic pandas langchain-groq langchain-community pypdf python-dotenv")

# ============================================
# RUN INSTRUCTIONS
# ============================================

def print_run_instructions():
    instructions = """

========================================
    JOB AGENT SYSTEM - READY TO RUN
========================================

To run the complete system:

1. INSTALL DEPENDENCIES:
   pip install -r requirements.txt

2. SETUP GROQ API KEY:
   - Get API key from: https://console.groq.com
   - Edit .env file and add your key:
     GROQ_API_KEY=your_actual_key_here

3. START BACKEND SERVER (Terminal 1):
   cd backend
   python main.py
   
   OR
   
   uvicorn backend.main:app --reload --port 8000

4. START FRONTEND UI (Terminal 2):
   streamlit run frontend/app.py

5. OPEN IN BROWSER:
   Frontend: http://localhost:8501
   API Docs: http://localhost:8000/docs

========================================
    QUICK TEST URLs
========================================

Try these sample URLs:
- https://www.naukri.com/software-engineer-jobs
- https://www.linkedin.com/jobs/view/123456
- Any company careers page

========================================
    PROJECT STRUCTURE CREATED
========================================

job-agent/
├── backend/
│   ├── __init__.py
│   ├── main.py (FastAPI server)
│   ├── pipeline.py (Main pipeline)
│   ├── extractor.py (LLM extraction)
│   ├── parser.py (HTML/PDF parser)
│   ├── models.py (Data models)
│   └── storage.py (CSV/JSON storage)
├── frontend/
│   ├── __init__.py
│   └── app.py (Streamlit UI)
├── data/
│   └── jobs.csv (Extracted jobs)
├── .env (API keys)
└── requirements.txt (Dependencies)

========================================
    FEATURES
========================================

- Crawl job URLs (HTML + PDF)
- AI-powered extraction (Groq LLM)
- Automatic deduplication
- Save to CSV and JSON
- Web UI with Streamlit
- REST API with FastAPI
- Fallback regex extractor (no API key needed)

========================================
"""

    print(instructions)

# ============================================
# MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    print("""
    ========================================
    JOB AGENT SYSTEM - AUTO SETUP
    ========================================
    """)
    
    # Create project structure
    create_project_structure()
    
    # Generate all files
    print("\n[INFO] Generating project files...")
    generate_all_files()
    
    # Print run instructions
    print_run_instructions()
    
    # Check for API key
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            if "your_groq_api_key_here" in f.read():
                print("\n[WARNING] Please edit .env file and add your Groq API key!")
                print("         Get free API key from: https://console.groq.com")
    
    print("\n[SUCCESS] Setup complete! Follow instructions above to run the system.")