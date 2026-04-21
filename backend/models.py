from pydantic import BaseModel
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