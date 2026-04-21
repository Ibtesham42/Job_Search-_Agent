import csv
import json
import os
from datetime import datetime

def _ensure_dir(path):
    """Create parent directory if it doesn't exist"""
    os.makedirs(os.path.dirname(path), exist_ok=True)

def save_jobs_csv(jobs, path="data/jobs.csv"):
    try:
        _ensure_dir(path)  # FIX: create data/ folder automatically
        with open(path, "w", newline="", encoding="utf-8") as f:
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
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ])
        print(f"[STORAGE] Saved {len(jobs)} jobs to {path}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save CSV: {e}")
        return False

def save_jobs_json(jobs, path="data/jobs.json"):
    try:
        _ensure_dir(path)  # FIX: create data/ folder automatically
        with open(path, "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)
        print(f"[STORAGE] Saved {len(jobs)} jobs to {path}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save JSON: {e}")
        return False

def load_jobs_csv(path="data/jobs.csv"):
    jobs = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                jobs.append(row)
    except FileNotFoundError:
        pass
    return jobs