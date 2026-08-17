import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Membuat router khusus untuk pengaturan
router = APIRouter(prefix="/api/settings", tags=["Settings"])

CONFIG_PATH = Path("app/config/hardware_profiles.json")

# Model validasi untuk request POST
class ProfileUpdate(BaseModel):
    active_profile: str

@router.get("/profile")
def get_hardware_profile():
    """Mengambil konfigurasi profil hardware saat ini."""
    if not CONFIG_PATH.exists():
        raise HTTPException(status_code=404, detail="Fail konfigurasi tidak ditemukan.")
    
    with open(CONFIG_PATH, "r") as f:
        data = json.load(f)
    return data

@router.post("/profile")
def update_hardware_profile(update_data: ProfileUpdate):
    """Mengubah profil hardware yang aktif."""
    if not CONFIG_PATH.exists():
        raise HTTPException(status_code=404, detail="Fail konfigurasi tidak ditemukan.")
    
    # Baca data lama
    with open(CONFIG_PATH, "r") as f:
        data = json.load(f)
    
    # Validasi apakah profil yang diminta ada di dalam konfigurasi
    if update_data.active_profile not in data.get("profiles", {}):
        raise HTTPException(status_code=400, detail="Profil tidak valid atau tidak tersedia.")
    
    # Perbarui profil aktif
    data["active_profile"] = update_data.active_profile
    
    # Simpan kembali ke fail JSON
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=4)
        
    return {
        "message": "Profil berhasil diperbarui.", 
        "active_profile": update_data.active_profile
    } 