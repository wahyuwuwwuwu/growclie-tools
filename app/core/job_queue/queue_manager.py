import queue
import threading
import time
import uuid

class JobQueueManager:
    def __init__(self):
        # Membuat antrean FIFO (First In, First Out)
        self.queue = queue.Queue()
        self.jobs = {}  # Menyimpan status setiap job
        
        # Lock untuk mengamankan dictionary self.jobs dari tabrakan data (race condition)
        self.lock = threading.Lock()
        
        # Memulai worker di latar belakang (daemon thread)
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

    def add_job(self, module_type: str, data: dict):
        """Menambahkan pekerjaan baru ke dalam antrean."""
        job_id = str(uuid.uuid4())
        job = {
            "id": job_id,
            "module_type": module_type,
            "data": data,
            "status": "queued",  # Status awal: queued
            "result": None
        }
        
        # Amankan proses penulisan ke dictionary
        with self.lock:
            self.jobs[job_id] = job
            
        self.queue.put(job_id)
        print(f"[Queue] Job {job_id} ditambahkan ke antrean.")
        return job_id

    def get_job_status(self, job_id: str):
        """Mengambil status pekerjaan saat ini secara aman."""
        with self.lock:
            return self.jobs.get(job_id)

    def _worker(self):
        """Fungsi pekerja yang berjalan di latar belakang secara sekuensial."""
        while True:
            # Akan menunggu (block) sampai ada pekerjaan di antrean
            job_id = self.queue.get()
            
            with self.lock:
                job = self.jobs.get(job_id)
            
            if not job:
                self.queue.task_done()
                continue
            
            try:
                with self.lock:
                    job["status"] = "processing"
                    
                print(f"\n[Worker] 🔄 MEMULAI proses Job ID: {job_id} (Modul: {job['module_type']})")
                
                # SIMULASI PEKERJAAN BERAT (Phase 1)
                # Di sini nanti kita akan memanggil FFmpeg atau Whisper
                for i in range(3):
                    print(f"         > Memproses... {i+1}/3 detik")
                    time.sleep(1)
                
                with self.lock:
                    job["status"] = "done"
                    job["result"] = "Sukses simulasi render"
                print(f"[Worker] ✅ SELESAI Job ID: {job_id}")
                
            except Exception as e:
                with self.lock:
                    job["status"] = "error"
                    job["result"] = str(e)
                print(f"[Worker] ❌ ERROR Job ID: {job_id} - {e}")
                
            finally:
                # Memberi tahu bahwa pekerjaan ini sudah selesai sebelum lanjut ke antrean berikutnya
                self.queue.task_done()

# Instansiasi global agar bisa dipanggil dari seluruh aplikasi
job_queue = JobQueueManager()


# ==========================================
# BLOK PENGUJIAN MANDIRI (THE GITHUB METHOD)
# ==========================================
if __name__ == "__main__":
    print("=== UJI COBA JOB QUEUE ENGINE (SEQUENTIAL) ===")
    
    # 1. Menambahkan 3 pekerjaan sekaligus
    job1 = job_queue.add_job("podcast", {"video": "eps1.mp4"})
    job2 = job_queue.add_job("sruput", {"video": "reaksi.mp4"})
    job3 = job_queue.add_job("podcast", {"video": "eps2.mp4"})
    
    # 2. Menjaga skrip utama tetap hidup agar worker bisa menyelesaikan pekerjaannya
    # Pekerjaan harus diproses satu per satu (sekuensial)
    job_queue.queue.join()
    
    print("\n=== SEMUA PEKERJAAN SELESAI ===")
    print("Status Akhir Job 1:", job_queue.get_job_status(job1)['status'])
    print("Status Akhir Job 2:", job_queue.get_job_status(job2)['status'])
    print("Status Akhir Job 3:", job_queue.get_job_status(job3)['status'])
