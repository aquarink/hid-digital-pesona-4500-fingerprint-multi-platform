import sys
import os
import time
import base64
from io import BytesIO
from datetime import datetime
from dp4500_scanner import DigitalPersona4500

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
    print(" DIGITALPERSONA 4500 - CONTINUOUS FINGERPRINT SCANNER ")
    print("=" * 65)
    print("Scanner akan terus menyala & siaga membaca setiap kali jari ditempelkan.")
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
            
            # Tunggu sentuhan jari tanpa batas (looping per 60 detik agar tetap responsif)
            finger_detected = False
            while not finger_detected:
                finger_detected = scanner.wait_for_finger(timeout_sec=60)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            print(f"[*] Jari terdeteksi pada {datetime.now().strftime('%H:%M:%S')}! Mengambil gambar...")
            
            img = scanner.capture_image()
            
            # 1. Simpan ke fingerprint.png (dan arsip history di folder scans/)
            os.makedirs("scans", exist_ok=True)
            archive_path = f"scans/fingerprint_{timestamp}.png"
            img.save("fingerprint.png")
            img.save(archive_path)
            
            # 2. Simpan Base64 ke TXT
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            b64_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            with open("fingerprint_base64.txt", "w") as f:
                f.write(f"data:image/png;base64,{b64_str}")
            
            # 3. Simpan ASCII Art ke TXT
            ascii_art = image_to_ascii(img, width=80)
            with open("fingerprint_ascii.txt", "w") as f:
                f.write(f"=== HASIL SCAN #{scan_count} ({timestamp}) ===\n\n")
                f.write(ascii_art)
            
            print(f"[OK] Gambar disimpan: fingerprint.png (arsip: {archive_path})")
            print(f"[OK] Base64 disimpan: fingerprint_base64.txt")
            print(f"[OK] ASCII Art disimpan: fingerprint_ascii.txt")
            
            print("\nPreview Mini:")
            print(image_to_ascii(img, width=50))
            
            # Tunggu sampai jari diangkat agar tidak langsung scan dobel
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
