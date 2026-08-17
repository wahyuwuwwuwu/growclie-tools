from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.job_queue.queue_manager import job_queue

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

class JobRequest(BaseModel):
    module_type: str
    data: dict

@router.post("/")
def create_job(req: JobRequest):
    """Menerima request dari UI dan memasukkannya ke antrean."""
    job_id = job_queue.add_job(req.module_type, req.data)
    return {"message": "Job berhasil ditambahkan ke antrean", "job_id": job_id}

@router.get("/{job_id}")
def get_job(job_id: str):
    """Mengecek status pekerjaan saat ini berdasarkan ID."""
    job_data = job_queue.get_job_status(job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan")
    return job_data