import json
import os
import re
from langchain_groq import ChatGroq

def get_llm():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("[WARNING] GROQ_API_KEY not set. Using regex extractor.")
        return None
    return ChatGroq(model="mixtral-8x7b-32768", temperature=0, api_key=api_key)

PROMPT = """Extract ALL job listings from the text below.

Return ONLY valid JSON array. Example:
[
  {
    "company": "Google",
    "job_title": "Software Engineer",
    "description": "Looking for Python developer with 3+ years experience...",
    "location": "Bangalore, India",
    "posted_date": "2024-01-15",
    "apply_by": "2024-02-15"
  }
]

Rules:
- Extract EVERY job posting you find
- If field not found, use null
- No extra text before or after JSON
- Keep description under 300 chars

TEXT:
"""

def extract_jobs_with_llm(text, llm):
    try:
        response = llm.invoke(PROMPT + text[:8000])
        content = response.content
        
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
    """Improved regex-based extraction"""
    jobs = []
    
    # Pattern 1: Job title followed by company and location
    patterns = [
        # Standard job posting pattern
        r'(?P<title>[A-Z][A-Za-z\s]+(?:Engineer|Developer|Manager|Analyst|Designer|Specialist|Consultant|Associate|Lead|Architect))[\s\S]{0,200}?(?P<company>[A-Z][a-z]+(?:Corp|Inc|Ltd|Technologies|Solutions|Systems)?)[\s\S]{0,200}?(?P<location>[A-Z][a-z]+\s*(?:,?\s*[A-Z]{2})?)',
        
        # Pattern 2: "Job Title: XXX" format
        r'Job\s+Title[:\s]+(?P<title>[^\n]+)',
        
        # Pattern 3: "Position: XXX" format  
        r'Position[:\s]+(?P<title>[^\n]+)',
        
        # Pattern 4: "Role: XXX" format
        r'Role[:\s]+(?P<title>[^\n]+)',
    ]
    
    all_matches = []
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            job = {}
            if 'title' in match.groupdict() and match.group('title'):
                job['job_title'] = match.group('title').strip()
            if 'company' in match.groupdict() and match.group('company'):
                job['company'] = match.group('company').strip()
            if 'location' in match.groupdict() and match.group('location'):
                job['location'] = match.group('location').strip()
            
            if job.get('job_title'):
                all_matches.append(job)
    
    # Pattern 5: Extract company names (common patterns)
    company_patterns = [
        r'(?:at|@|with)\s+([A-Z][a-zA-Z\s]+(?:Technologies|Solutions|Corp|Inc|Ltd|LLC|Systems|Software|Digital))',
        r'Company[:\s]+([^\n]+)',
        r'Organization[:\s]+([^\n]+)',
    ]
    
    for pattern in company_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if not all_matches or not all_matches[-1].get('company'):
                job = {'company': match.strip()}
                all_matches.append(job)
    
    # Pattern 6: Extract locations
    location_patterns = [
        r'Location[:\s]+([^\n]+)',
        r'(?:in|at)\s+([A-Z][a-z]+,\s*[A-Z]{2})',
        r'([A-Z][a-z]+\s*,\s*[A-Z][a-z]+)',
    ]
    
    for pattern in location_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if all_matches and not all_matches[-1].get('location'):
                all_matches[-1]['location'] = match.strip()
    
    # Pattern 7: Extract dates
    date_patterns = [
        r'Posted[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'Date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'Apply\s+by[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
    ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if all_matches and not all_matches[-1].get('posted_date'):
                all_matches[-1]['posted_date'] = match.strip()
    
    # Add description and deduplicate
    seen_titles = set()
    unique_jobs = []
    
    for job in all_matches:
        title = job.get('job_title', '')
        if title and title.lower() not in seen_titles:
            seen_titles.add(title.lower())
            job['description'] = text[:500] if text else ''
            job['apply_by'] = None
            unique_jobs.append(job)
    
    # If no jobs found, create a sample job from page title or first heading
    if not unique_jobs:
        # Try to find first heading
        heading_match = re.search(r'<h1[^>]*>([^<]+)</h1>', text, re.IGNORECASE)
        if heading_match:
            unique_jobs.append({
                'job_title': heading_match.group(1).strip(),
                'company': None,
                'location': None,
                'description': text[:500],
                'posted_date': None,
                'apply_by': None
            })
    
    return unique_jobs

def extract_jobs(text):
    llm = get_llm()
    
    if llm:
        jobs = extract_jobs_with_llm(text, llm)
        if jobs and len(jobs) > 0:
            return jobs
    
    print("[INFO] Using regex extractor")
    return extract_jobs_regex(text)