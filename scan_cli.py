import sys
import os
import time
import base64
from io import BytesIO
from datetime import datetime
from dp4500_scanner import DigitalPersona4500
from fingerprint_matcher import FingerprintDatabase

def image_to_ascii(img, width=60):
    """Mengubah gambar sidik jari menjadi teks ASCII agar bisa dilihat di text editor"""
    w, h = img.size
    aspect_ratio = h / w
    new_height = int(aspect_ratio * width * 0.55)
    img_small = img.resize((width, new_height))
    
    chars = [" ", "░", "▒", "▓", "█"]
    pixels = img_small.getdata()
    ascii_str = ""
    for idx, p in enumerate(pixels):
        char_idx = int(p / 256 * len(chars))
        ascii_str += chars[min(char_idx, len(chars) - 1)]
        if (idx + 1) % width == 0:
            ascii_str += "\n"
    return ascii_str

def main():
    print("=" * 65)
    print(" DIGITALPERSONA 4500 - FINGERPRINT IDENTIFICATION SYSTEM ")
    print("=" * 65)
    
    db = FingerprintDatabase()
    total_users = len(db.users)
    print(f"[*] Database: {total_users} user terdaftar.")
    if total_users == 0:
        print("[!] Tips: Database masih kosong. Anda bisa mendaftarkan user")
        print("    dengan menjalankan: python3 enroll.py")
    else:
        for u in db.list_users():
            print(f"    - ID: {u['id']:<10} | Nama: {u['name']}")

    print("\nScanner akan terus menyala & siaga mengenali sidik jari.")
    print("Tekan Ctrl + C di terminal untuk keluar.\n")
    
    scanner = DigitalPersona4500()
    scan_count = 0

    try:
        print("[*] Menghubungkan ke hardware DigitalPersona 4500...")
        scanner.connect()
        print("[*] Perangkat terhubung & siap digunakan!\n")
        
        while True:
            scan_count += 1
            print("-" * 65)
            print(f"[IDLE #{scan_count}] LAMPU MENYALA: Silakan tempelkan jari ke scanner...")
            
            finger_detected = False
            while not finger_detected:
                finger_detected = scanner.wait_for_finger(timeout_sec=60)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            time_str = datetime.now().strftime("%H:%M:%S")
            print(f"[*] Jari terdeteksi pada {time_str}! Mengambil citra...")
            
            img = scanner.capture_image()
            
            # 1. Simpan gambar dan Base64
            os.makedirs("scans", exist_ok=True)
            archive_path = f"scans/fingerprint_{timestamp}.png"
            img.save("fingerprint.png")
            img.save(archive_path)
            
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            b64_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            with open("fingerprint_base64.txt", "w") as f:
                f.write(f"data:image/png;base64,{b64_str}")
            
            ascii_art = image_to_ascii(img, width=80)
            with open("fingerprint_ascii.txt", "w") as f:
                f.write(f"=== HASIL SCAN #{scan_count} ({timestamp}) ===\n\n")
                f.write(ascii_art)

            # 2. PROSES PENCOCOKAN KE DATABASE (IDENTIFIKASI BIOMETRIK)
            print("[*] Memeriksa kecocokan biometrik ke database...")
            user, score, good_matches = db.identify(img)

            if user:
                print("\n" + "=" * 65)
                print("🎯 IDENTIFIKASI BERHASIL! (MATCH FOUND)")
                print("=" * 65)
                print(f"  ID User      : {user['id']}")
                print(f"  Nama Lengkap : {user['name']}")
                print(f"  Skor Cocok   : {score:.1f}% ({good_matches} titik biometrik identik)")
                print(f"  Waktu Absen  : {time_str}")
                print("=" * 65)
            else:
                print("\n" + "=" * 65)
                print("⚠️  SIDIK JARI TIDAK DIKENALI! (UNKNOWN USER)")
                print("=" * 65)
                if good_matches > 0:
                    print(f"  Kemiripan tertinggi hanya {good_matches} titik (belum mencapai ambang batas).")
                print("  Jari ini belum terdaftar di database.")
                print("  Gunakan 'python3 enroll.py' untuk mendaftarkan user ini.")
                print("=" * 65)

            # Tunggu sampai jari diangkat dari sensor
            print("[*] Menunggu jari diangkat dari sensor...")
            scanner.wait_for_finger_off(timeout_sec=5)
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n[!] Program dihentikan oleh pengguna (Ctrl+C).")
    except Exception as e:
        print(f"\n[ERROR]: {e}")
    finally:
        print("[*] Mematikan sensor...")
        scanner.close()
        print("[*] Selesai. Sensor dalam mode standby.")

if __name__ == "__main__":
    main()
