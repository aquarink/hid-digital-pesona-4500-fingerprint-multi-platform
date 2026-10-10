# HID DigitalPersona 4500 Multi-Platform Fingerprint Driver & Bridge

Driver dan bridge mandiri (user-space USB) berbasis Python untuk perangkat pembaca sidik jari **HID DigitalPersona 4500 (U.are.U 4500)** dengan dukungan lintas sistem operasi (**macOS**, **Linux**, dan **Windows**).

## Fitur Utama

- **Multi-Platform:** Berjalan di macOS (Intel & Apple Silicon), Linux, dan Windows tanpa ketergantungan driver kernel resmi vendor.
- **Direct USB Communication:** Mengakses hardware secara langsung melalui `libusb` & `pyusb` menggunakan protokol `uru4000`.
- **Hardware Control:** Kontrol inisialisasi chip, pengaturan gain/exposure, toggle LED merah sensor (*armed / standby*), dan deteksi event jari (*finger on / finger off*).
- **Image Capture & Decoding:** Menangkap citra mentah sidik jari (384x290 piksel), dekripsi stream data LFSR, dan konversi ke citra Grayscale PNG.
- **Multiple Output Formats:**
  - File citra PNG (`fingerprint.png`)
  - Format teks ASCII Art (`fingerprint_ascii.txt`) untuk pengujian di text editor/notepad
  - Base64 data URI (`fingerprint_base64.txt`) untuk konsumsi aplikasi Web frontend
  - HTML viewer sederhana (`viewer.html`)

## Persyaratan Sistem

- Python 3.8+
- Library sistem `libusb`:
  - **macOS:** `brew install libusb`
  - **Linux:** `sudo apt install libusb-1.0-0`
  - **Windows:** Pasang driver generic WinUSB / libusb-win32 pada perangkat menggunakan [Zadig](https://zadig.akeo.ie/)

## Instalasi

1. Clone repositori ini:
   ```bash
   git clone git@github.com:aquarink/hid-digital-pesona-4500-fingerprint-multi-platform.git
   cd hid-digital-pesona-4500-fingerprint-multi-platform
   ```

2. Pasang dependensi Python:
   ```bash
   pip install -r requirements.txt
   ```

## Penggunaan

### 1. Uji Coba LED Sensor
Menyalakan lampu sensor merah selama 5 detik untuk memastikan komunikasi USB berjalan:
```bash
python3 test_led.py
```

### 2. Pendaftaran User & ID Baru (Enrollment)
Mendaftarkan sidik jari dengan ID dan Nama ke database lokal:
```bash
python3 enroll.py
```
Ikuti instruksi di terminal:
1. Masukkan ID User (misal: `EMP-001` atau `001`)
2. Masukkan Nama Lengkap
3. Tempelkan jari ke scanner saat lampu merah menyala. Template biometrik akan tersimpan di `users_db.json`.

### 3. Pengenalan & Identifikasi Otomatis (Continuous Recognition)
Scanner siaga terus menerus. Setiap kali ada jari yang ditempelkan, sistem akan otomatis mencocokkan ke database dan mengeluarkan nama & ID pemiliknya:
```bash
python3 scan_cli.py
```

Jika sidik jari cocok:
```text
🎯 IDENTIFIKASI BERHASIL! (MATCH FOUND)
ID User      : EMP-001
Nama Lengkap : Budi
Skor Cocok   : 94.2% (142 titik biometrik identik)
```

Jika belum terdaftar:
```text
⚠️  SIDIK JARI TIDAK DIKENAL! (UNKNOWN USER)
Gunakan 'python3 enroll.py' untuk mendaftarkan user ini.
```

### 4. Melihat Hasil di Browser
Buka file `viewer.html` di browser (Chrome/Edge/Safari/Firefox) untuk melihat gambar hasil scan.

## Lisensi

MIT License
