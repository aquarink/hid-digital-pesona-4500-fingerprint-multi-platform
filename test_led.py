import time
import usb.core
import usb.util

VID = 0x05ba
PID = 0x000a

REG_HWSTAT = 0x07
REG_MODE = 0x4e
REG_DEVICE_INFO = 0xf0

MODE_OFF = 0x70
MODE_AWAIT_FINGER_ON = 0x10
MODE_CAPTURE = 0x20

def write_reg(dev, reg, val):
    dev.ctrl_transfer(0x40, 0x04, reg, 0, bytes([val]))

def write_regs(dev, reg, data):
    dev.ctrl_transfer(0x40, 0x04, reg, 0, data)

def read_regs(dev, reg, length=1):
    return dev.ctrl_transfer(0xc0, 0x04, reg, 0, length)

def main():
    print("Mencari perangkat DigitalPersona 4500...")
    dev = usb.core.find(idVendor=VID, idProduct=PID)
    if dev is None:
        print("Perangkat tidak ditemukan!")
        return

    # Detach kernel driver if needed (on Linux/Mac)
    try:
        if dev.is_kernel_driver_active(0):
            dev.detach_kernel_driver(0)
    except Exception:
        pass

    dev.set_configuration()
    usb.util.claim_interface(dev, 0)
    print("Berhasil claim interface USB!")

    # Baca HWSTAT awal
    hwstat = read_regs(dev, REG_HWSTAT, 1)[0]
    print(f"HWSTAT awal: 0x{hwstat:02x}")

    # Reboot power jika 0x84
    if (hwstat & 0x84) == 0x84:
        print("Rebooting device power...")
        for _ in range(100):
            write_reg(dev, REG_HWSTAT, hwstat & 0x0f)
            hwstat = read_regs(dev, REG_HWSTAT, 1)[0]
            if hwstat & 0x01:
                break
            time.sleep(0.01)

    # Power down jika belum down
    if (hwstat & 0x80) == 0:
        print("Power down...")
        write_reg(dev, REG_HWSTAT, hwstat | 0x80)
        time.sleep(0.01)

    # Power up loop
    print("Powering up sensor...")
    for _ in range(100):
        write_reg(dev, REG_HWSTAT, hwstat & 0x0f)
        hwstat = read_regs(dev, REG_HWSTAT, 1)[0]
        if (hwstat & 0x80) == 0:
            break
        time.sleep(0.01)

    print(f"HWSTAT setelah powerup: 0x{hwstat:02x}")

    # Cek interrupt 56aa pada EP 0x81 (timeout 500ms)
    try:
        irq = dev.read(0x81, 64, timeout=500)
        irq_type = (irq[0] << 8) | irq[1]
        print(f"Menerima IRQ: 0x{irq_type:04x}")
    except usb.core.USBTimeoutError:
        print("IRQ 56aa timeout (normal/lanjutkan)")

    # Baca device info
    try:
        info = read_regs(dev, REG_DEVICE_INFO, 16)
        print(f"Device Info: {bytes(info).hex()}")
    except Exception as e:
        print("Gagal baca info:", e)

    # NYALAKAN LAMPU SENSOR (AWAIT FINGER ON)
    print("\n>>> MENYALAKAN LAMPU MERAH SCANNER (MODE_AWAIT_FINGER_ON) SELAMA 5 DETIK! <<<")
    write_reg(dev, REG_MODE, MODE_AWAIT_FINGER_ON)
    
    # Tunggu 5 detik sambil monitor sentuhan jari
    t_end = time.time() + 5
    while time.time() < t_end:
        try:
            irq = dev.read(0x81, 64, timeout=200)
            irq_type = (irq[0] << 8) | irq[1]
            if irq_type == 0x0101:
                print(">>> JARI TERDETEKSI MENEMPEL! (FINGER ON) <<<")
            elif irq_type == 0x0200:
                print(">>> JARI DIANGKAT! (FINGER OFF) <<<")
        except usb.core.USBTimeoutError:
            pass

    # Matikan lampu
    print("Mematikan lampu scanner (MODE_OFF)...")
    write_reg(dev, REG_MODE, MODE_OFF)
    print("Selesai!")

if __name__ == "__main__":
    main()
