from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Import router yang sudah kita buat
from app.web.routes import settings, jobs

app = FastAPI(title="GrowClie Tools")

# Inisialisasi Jinja2
templates = Jinja2Templates(directory="app/web/templates")

# Daftarkan seluruh router API ke aplikasi utama
app.include_router(settings.router)
app.include_router(jobs.router)  # <-- Tambahan baru untuk sistem antrean

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # Memuat UI Shell utama
    return templates.TemplateResponse(request=request, name="index.html", context={})