import cv2
import mediapipe as mp
import subprocess
import os
import statistics

def analyze_video_zones(video_path):
    """
    Mode 1: Smart Hybrid Zonasi.
    Melakukan downscale ke 320x240 di RAM dan mendeteksi titik wajah.
    """
    mp_face_detection = mp.solutions.face_detection
    face_detection = mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Tidak dapat membuka video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    iw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    ih = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    frame_interval = int(fps) 
    current_frame = 0

    left_cxs = []
    right_cxs = []
    all_cxs = []

    while cap.isOpened():
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
        success, image = cap.read()
        if not success:
            break

        # ATURAN MUTLAK: Downscale ke 320x240 di memori RAM
        image_small = cv2.resize(image, (320, 240))
        image_rgb = cv2.cvtColor(image_small, cv2.COLOR_BGR2RGB)
        
        results = face_detection.process(image_rgb)

        if results.detections:
            for detection in results.detections:
                bboxC = detection.location_data.relative_bounding_box
                cx = bboxC.xmin + bboxC.width / 2
                
                # Memastikan pemisahan Kiri dan Kanan tegas
                if cx < 0.45:
                    left_cxs.append(cx)
                elif cx > 0.55:
                    right_cxs.append(cx)
                all_cxs.append(cx)

        current_frame += frame_interval
        if current_frame >= total_frames:
            break

    cap.release()
    
    left_med = statistics.median(left_cxs) if left_cxs else 0.25
    right_med = statistics.median(right_cxs) if right_cxs else 0.75
    center_med = statistics.median(all_cxs) if all_cxs else 0.5

    # Penentuan Zonasi
    if len(left_cxs) > 0 and len(right_cxs) > 0:
        zone_type = "dual"
    elif len(left_cxs) > 0:
        zone_type = "left_only"
    elif len(right_cxs) > 0:
        zone_type = "right_only"
    else:
        zone_type = "center"

    return zone_type, left_med, right_med, center_med, iw, ih

def process_mode_1(input_path, output_path):
    print(f"[Mode 1] Menganalisis zonasi wajah di {input_path}...")
    zone_type, left_med, right_med, center_med, iw, ih = analyze_video_zones(input_path)
    print(f"[Mode 1] Hasil Deteksi AI: Zonasi {zone_type.upper()}")
    
    if zone_type == "dual":
        # RUMUS PRESISI: Potongan mutlak 1080x960 per orang
        # Saat ditumpuk 960 + 960 = 1920. Hasil akhir tepat 1080x1920 (9:16)
        crop_w = int(ih)
        crop_h = int(ih * 8 / 9)
        
        if crop_w % 2 != 0: crop_w -= 1
        if crop_h % 2 != 0: crop_h -= 1

        y_pos = int((ih - crop_h) / 2) # Pemusatan vertikal

        # Menghitung titik kordinat Kiri (Top) murni di Python
        left_cx = int(left_med * iw)
        x_top = int(left_cx - crop_w / 2)
        x_top = max(0, min(x_top, iw - crop_w))

        # Menghitung titik kordinat Kanan (Bottom) murni di Python
        right_cx = int(right_med * iw)
        x_bot = int(right_cx - crop_w / 2)
        x_bot = max(0, min(x_bot, iw - crop_w))

        # Split=2 memastikan FFmpeg membelah stream dengan benar sebelum memotong
        vf_filter = (
            "[0:v]split=2[v1][v2];"
            f"[v1]crop={crop_w}:{crop_h}:{x_top}:{y_pos}[top];"
            f"[v2]crop={crop_w}:{crop_h}:{x_bot}:{y_pos}[bottom];"
            "[top][bottom]vstack[v]"
        )
        map_arg = ["-map", "[v]", "-map", "0:a?"]
        
    else:
        # LOGIKA SINGLE PORTRAIT 9:16
        crop_h = int(ih)
        crop_w = int(ih * 9 / 16)
        
        if crop_w % 2 != 0: crop_w -= 1
        if crop_h % 2 != 0: crop_h -= 1
        
        y_pos = 0

        if zone_type == "left_only":
            med = left_med
        elif zone_type == "right_only":
            med = right_med
        else:
            med = center_med

        center_x = int(med * iw)
        x_val = int(center_x - crop_w / 2)
        x_val = max(0, min(x_val, iw - crop_w))

        vf_filter = f"crop={crop_w}:{crop_h}:{x_val}:{y_pos}"
        map_arg = []
        
    command = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-filter_complex" if zone_type == "dual" else "-vf", vf_filter,
        "-threads", "3", 
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-c:a", "copy",
    ]
    
    if zone_type == "dual":
        command.extend(map_arg)
        
    command.append(output_path)
    
    print("[Mode 1] Memulai rendering cerdas FFmpeg...")
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if result.returncode != 0:
        print(f"[FFmpeg ERROR]\n{result.stderr}")
        raise RuntimeError("Gagal memproses video Mode 1.")
        
    print(f"[Mode 1] ✅ Selesai! Output tersimpan di {output_path}")
    return output_path

# ==========================================
# BLOK PENGUJIAN MANDIRI (THE GITHUB METHOD)
# ==========================================
if __name__ == "__main__":
    print("=== UJI COBA MODE 1: SMART HYBRID ZONASI (FIXED RATIO 1080x1920) ===")
    
    input_file = "output/hasil_potong_hasil_potong_testing1.mp4"
    output_file = "output/mode1_hasil_testing1.mp4"
    
    if not os.path.exists(input_file):
        print(f"❌ File input tidak ditemukan: {input_file}")
    else:
        try:
            process_mode_1(input_file, output_file)
        except Exception as e:
            print(f"❌ Error: {e}")