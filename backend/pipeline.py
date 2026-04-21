import sys
import os
import hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parser import fetch_html, parse_html, parse_pdf
from extractor import extract_jobs

def run_pipeline(urls):
    all_jobs = []
    seen_hashes = set()
    
    print(f"\n[PIPELINE] Processing {len(urls)} URLs")
    
    for idx, url in enumerate(urls, 1):
        print(f"  [{idx}/{len(urls)}] Processing: {url[:80]}...")
        
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
        
        if not text or len(text) < 100:
            print(f"    [FAIL] Could not extract text (got {len(text) if text else 0} chars)")
            continue
        
        print(f"    [OK] Extracted {len(text)} chars")
        
        jobs = extract_jobs(text)
        print(f"    [OK] Found {len(jobs)} jobs")
        
        for job in jobs:
            # Create unique key
            company = job.get('company', '') or ''
            title = job.get('job_title', '') or ''
            location = job.get('location', '') or ''
            unique_str = f"{company}|{title}|{location}"
            unique_hash = hashlib.md5(unique_str.encode()).hexdigest()
            
            if unique_hash not in seen_hashes and title:
                seen_hashes.add(unique_hash)
                job["source"] = source
                job["apply_link"] = url
                all_jobs.append(job)
                print(f"      Added: {title[:50]}")
    
    print(f"\n[PIPELINE] Total unique jobs: {len(all_jobs)}")
    return all_jobs