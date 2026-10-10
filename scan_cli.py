import sys
import time
import base64
from io import BytesIO
from dp4500_scanner import DigitalPersona4500

def image_to_ascii(img, width=60):
    """Mengubah gambar sidik jari menjadi teks ASCII agar bisa dilihat di text editor"""
    # Resize menjaga aspect ratio
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
    print("=" * 60)
    print(" DIGITALPERSONA 4500 - FINGERPRINT SCANNER TEST ")
    print("=" * 60)
    
    scanner = DigitalPersona4500()
    try:
        print("[1/3] Menghubungkan ke pembaca sidik jari...")
        scanner.connect()
        print("      Berhasil terhubung!")
        
        print("\n[2/3] LAMPU MERAH MENYALA! Tempelkan jari Anda ke scanner sekarang (waktu 45 detik)...")
        finger_detected = scanner.wait_for_finger(timeout_sec=45)
        
        if not finger_detected:
            print("\n[!] Waktu habis (45 detik): Tidak ada jari yang ditempelkan.")
            scanner.set_mode(0x70)
            return

        print("\n[3/3] Jari terdeteksi! Mengambil gambar sidik jari...")
        img = scanner.capture_image()
        
        # 1. Simpan ke PNG
        img_path = "fingerprint.png"
        img.save(img_path)
        print(f"      [OK] Gambar sidik jari berhasil disimpan: {img_path}")
        
        # 2. Simpan Base64 ke TXT (bisa dibuka di browser / notepad)
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        b64_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        with open("fingerprint_base64.txt", "w") as f:
            f.write(f"data:image/png;base64,{b64_str}")
        print("      [OK] Data Base64 disimpan: fingerprint_base64.txt")

        # 3. Simpan ASCII Art ke TXT (bisa dibuka di Notepad / TextEdit)
        ascii_art = image_to_ascii(img, width=80)
        with open("fingerprint_ascii.txt", "w") as f:
            f.write("=== PREVIEW HASIL SCAN SIDIK JARI (BUKA DENGAN FONT MONOSPACE) ===\n\n")
            f.write(ascii_art)
        print("      [OK] Preview visual disimpan: fingerprint_ascii.txt")

        print("\n" + "=" * 60)
        print("HASIL PREVIEW DI TERMINAL:")
        print("=" * 60)
        print(image_to_ascii(img, width=60))
        print("=" * 60)
        print("SUKSES! Anda bisa membuka file berikut di Notepad / TextEdit:")
        print("1. fingerprint_ascii.txt  -> Gambar sidik jari dalam karakter teks")
        print("2. fingerprint_base64.txt -> Kode base64 untuk aplikasi web")
        print("3. fingerprint.png        -> File gambar asli hasil scan")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR]: {e}")
    finally:
        scanner.close()

if __name__ == "__main__":
    main()
