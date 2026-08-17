import subprocess
import json
import os
from pathlib import Path

CONFIG_PATH = Path("app/config/hardware_profiles.json")

def get_ffmpeg_threads():
    """Membaca batas thread FFmpeg dari profil perangkat keras yang aktif."""
    try:
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)
            active = data.get("active_profile", "classic_pc")
            return data.get("profiles", {}).get(active, {}).get("ffmpeg_threads", 3)
    except Exception:
        return 3 # Nilai default (fallback) jika file tidak terbaca

def cut_video(input_path: str, output_path: str, start_time: str, end_time: str):
    """
    Memotong video berdasarkan timestamp manual.
    Menerapkan batasan thread agar CPU tidak terbebani secara berlebihan.
    """
    threads = get_ffmpeg_threads()
    
    # Perintah FFmpeg: re-encoding cepat untuk memastikan potongan akurat per frame
    command = [
        "ffmpeg",
        "-y", # Timpa file jika sudah ada
        "-i", input_path,
        "-ss", start_time,
        "-to", end_time,
        "-threads", str(threads), # Batasan dari profil Classic PC
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-c:a", "aac",
        output_path
    ]
    
    print(f"[FFmpeg] Memotong video: {start_time} -> {end_time} (Memakai max {threads} Threads)")
    
    # Menjalankan proses FFmpeg
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if result.returncode != 0:
        print(f"[FFmpeg ERROR]\n{result.stderr}")
        raise RuntimeError(f"Gagal memotong video: {output_path}")
        
    print(f"[FFmpeg] ✅ Selesai: Output tersimpan di {output_path}")
    return output_path


# ==========================================
# BLOK PENGUJIAN MANDIRI (THE GITHUB METHOD)
# ==========================================
if __name__ == "__main__":
    print("=== UJI COBA MANUAL TIMESTAMP CUTTING ===")
    
    # Pastikan folder input dan output eksis
    os.makedirs("input", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    
# GANTI 'dummy.mp4' DENGAN NAMA FILE VIDEO ANDA DI FOLDER input/
    nama_file_input = "testing1.mp4" 
    
    input_file = f"input/{nama_file_input}"
    output_file = f"output/hasil_potong_{nama_file_input}"
        
    if not os.path.exists(input_file):
        print(f"❌ File {input_file} tidak ditemukan!")
        print("Silakan ubah variabel 'nama_file_input' di script ini sesuai dengan nama video Anda.")
    else:
        try:
            # Simulasi memotong dari detik ke-0 hingga detik ke-10
            cut_video(input_file, output_file, "00:00:00", "00:00:10")
            print("✅ Pengujian pemotongan video sukses!")
        except Exception as e:
            print(f"❌ Terjadi kesalahan: {e}")