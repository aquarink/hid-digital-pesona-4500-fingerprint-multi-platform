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

### 2. Pengambilan Sidik Jari (CLI Scanner)
Menyalakan sensor, mendeteksi sentuhan jari, mengambil gambar sidik jari, dan mengekspor hasilnya:
```bash
python3 scan_cli.py
```

Hasil scan akan tersimpan otomatis:
- `fingerprint.png`
- `fingerprint_ascii.txt`
- `fingerprint_base64.txt`

### 3. Melihat Hasil di Browser
Buka file `viewer.html` di browser (Chrome/Edge/Safari/Firefox) untuk melihat gambar hasil scan.

## Lisensi

MIT License
