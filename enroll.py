import sys
import os
import time
from dp4500_scanner import DigitalPersona4500
from fingerprint_matcher import FingerprintDatabase

def main():
    print("=" * 60)
    print(" DAFTAR USER BARU (ENROLLMENT SIDIK JARI) ")
    print("=" * 60)

    user_id = input("Masukkan ID User (contoh: 001 atau EMP-101): ").strip()
    if not user_id:
        print("[!] ID User tidak boleh kosong.")
        return

    name = input("Masukkan Nama Lengkap: ").strip()
    if not name:
        print("[!] Nama tidak boleh kosong.")
        return

    db = FingerprintDatabase()
    if user_id in db.users:
        confirm = input(f"[?] ID '{user_id}' sudah ada ({db.users[user_id]['name']}). Timpa? (y/n): ")
        if confirm.lower() != 'y':
            print("Pendaftaran dibatalkan.")
            return

    scanner = DigitalPersona4500()
    try:
        print("\n[*] Menghubungkan ke scanner DigitalPersona 4500...")
        scanner.connect()
        print("[*] Terhubung!")
        
        print("\n🔴 LAMPU MERAH MENYALA!")
        print(f"👉 Silakan tempelkan jari milik [{name}] ke scanner (waktu 30 detik)...")
        
        detected = scanner.wait_for_finger(timeout_sec=30)
        if not detected:
            print("\n[!] Waktu habis: Jari tidak ditempelkan. Pendaftaran gagal.")
            return

        print("[*] Jari terdeteksi! Mengambil citra & mengekstrak ciri biometrik...")
        img = scanner.capture_image()
        
        # Simpan sampel gambar pendaftaran
        os.makedirs("enrolled_images", exist_ok=True)
        img_file = f"enrolled_images/user_{user_id}.png"
        img.save(img_file)

        # Daftarkan ke database
        feature_count = db.enroll(user_id, name, img)
        
        print("\n" + "=" * 60)
        print("🎉 PENDAFTARAN BERHASIL!")
        print("=" * 60)
        print(f"ID User       : {user_id}")
        print(f"Nama          : {name}")
        print(f"Jumlah Fitur  : {feature_count} titik biometrik unik")
        print(f"File Template : Tersimpan di users_db.json")
        print(f"File Sampel   : {img_file}")
        print("=" * 60)
        print("Sekarang Anda bisa menjalankan 'python3 scan_cli.py' untuk menguji identifikasi!")

        # Tunggu jari diangkat
        scanner.wait_for_finger_off(timeout_sec=5)

    except Exception as e:
        print(f"\n[ERROR]: {e}")
    finally:
        scanner.close()

if __name__ == "__main__":
    main()
