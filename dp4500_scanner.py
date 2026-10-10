import time
import struct
import random
import usb.core
import usb.util
from PIL import Image

VID = 0x05ba
PID = 0x000a

# Register
REG_HWSTAT = 0x07
REG_SCRAMBLE_DATA_INDEX = 0x33
REG_SCRAMBLE_DATA_KEY = 0x34
REG_MODE = 0x4e
REG_DEVICE_INFO = 0xf0

# Mode
MODE_INIT = 0x00
MODE_AWAIT_FINGER_ON = 0x10
MODE_AWAIT_FINGER_OFF = 0x12
MODE_CAPTURE = 0x20
MODE_OFF = 0x70

# IRQ Types
IRQ_SCANPWR_ON = 0x56aa
IRQ_FINGER_ON = 0x0101
IRQ_FINGER_OFF = 0x0200

# Image geometry
IMAGE_WIDTH = 384
IMAGE_HEIGHT = 290
HEADER_SIZE = 64
TOTAL_IMAGE_SIZE = HEADER_SIZE + (IMAGE_WIDTH * IMAGE_HEIGHT)

# Block flags
BLOCKF_CHANGE_KEY    = 0x80
BLOCKF_NO_KEY_UPDATE = 0x04
BLOCKF_ENCRYPTED     = 0x02
BLOCKF_NOT_PRESENT   = 0x01

def update_key(key: int) -> int:
    bit = key & 0x9248144d
    bit ^= bit << 16
    bit ^= bit << 8
    bit ^= bit << 4
    bit ^= bit << 2
    bit ^= bit << 1
    return ((bit & 0x80000000) | (key >> 1)) & 0xffffffff

def do_decode(data: bytearray, key: int) -> int:
    num_bytes = len(data)
    for i in range(num_bytes - 1):
        xorbyte = (((key >>  4) & 1) << 0) | \
                  (((key >>  8) & 1) << 1) | \
                  (((key >> 11) & 1) << 2) | \
                  (((key >> 14) & 1) << 3) | \
                  (((key >> 18) & 1) << 4) | \
                  (((key >> 21) & 1) << 5) | \
                  (((key >> 24) & 1) << 6) | \
                  (((key >> 29) & 1) << 7)
        key = update_key(key)
        data[i] = (data[i + 1] ^ xorbyte) & 0xff
    data[-1] = 0
    return update_key(key)

class DigitalPersona4500:
    def __init__(self):
        self.dev = None

    def connect(self):
        self.dev = usb.core.find(idVendor=VID, idProduct=PID)
        if self.dev is None:
            raise RuntimeError("Perangkat DigitalPersona 4500 tidak ditemukan!")

        try:
            if self.dev.is_kernel_driver_active(0):
                self.dev.detach_kernel_driver(0)
        except Exception:
            pass

        self.dev.set_configuration()
        usb.util.claim_interface(self.dev, 0)
        self._init_hardware()

    def write_reg(self, reg: int, val: int):
        self.dev.ctrl_transfer(0x40, 0x04, reg, 0, bytes([val]))

    def write_regs(self, reg: int, data: bytes):
        self.dev.ctrl_transfer(0x40, 0x04, reg, 0, data)

    def read_regs(self, reg: int, length: int = 1) -> bytes:
        return bytes(self.dev.ctrl_transfer(0xc0, 0x04, reg, 0, length))

    def _init_hardware(self):
        hwstat = self.read_regs(REG_HWSTAT, 1)[0]
        if (hwstat & 0x84) == 0x84:
            for _ in range(100):
                self.write_reg(REG_HWSTAT, hwstat & 0x0f)
                hwstat = self.read_regs(REG_HWSTAT, 1)[0]
                if hwstat & 0x01:
                    break
                time.sleep(0.01)

        if (hwstat & 0x80) == 0:
            self.write_reg(REG_HWSTAT, hwstat | 0x80)
            time.sleep(0.01)

        for _ in range(100):
            self.write_reg(REG_HWSTAT, hwstat & 0x0f)
            hwstat = self.read_regs(REG_HWSTAT, 1)[0]
            if (hwstat & 0x80) == 0:
                break
            time.sleep(0.01)

        # Flush interrupt
        try:
            self.dev.read(0x81, 64, timeout=300)
        except usb.core.USBTimeoutError:
            pass

    def set_mode(self, mode: int):
        self.write_reg(REG_MODE, mode)

    def wait_for_finger(self, timeout_sec=15):
        """Menyalakan lampu sensor dan menunggu jari disentuhkan"""
        self.set_mode(MODE_AWAIT_FINGER_ON)
        start_time = time.time()
        while time.time() - start_time < timeout_sec:
            try:
                irq = self.dev.read(0x81, 64, timeout=200)
                irq_type = (irq[0] << 8) | irq[1]
                if irq_type == IRQ_FINGER_ON:
                    return True
            except usb.core.USBTimeoutError:
                pass
        return False

    def capture_image(self) -> Image.Image:
        """Mengambil citra sidik jari dari sensor"""
        # Aktifkan mode capture
        self.set_mode(MODE_CAPTURE)

        # Baca bulk data dari EP 0x82
        raw_buffer = bytearray()
        chunk_size = 4096
        start_time = time.time()
        
        while len(raw_buffer) < TOTAL_IMAGE_SIZE and (time.time() - start_time < 3.0):
            try:
                data = self.dev.read(0x82, chunk_size, timeout=1000)
                raw_buffer.extend(data)
            except usb.core.USBTimeoutError:
                break

        if len(raw_buffer) < HEADER_SIZE:
            self.set_mode(MODE_OFF)
            raise RuntimeError(f"Gagal capture: data terlalu sedikit ({len(raw_buffer)} bytes)")

        # Parsing header
        num_lines = struct.unpack_from("<H", raw_buffer, 4)[0]
        key_number = raw_buffer[6]
        
        block_info = []
        for b in range(15):
            offset = 16 + (b * 2)
            flags = raw_buffer[offset]
            n_lines = raw_buffer[offset + 1]
            block_info.append((flags, n_lines))

        raw_img_data = raw_buffer[HEADER_SIZE:HEADER_SIZE + (IMAGE_WIDTH * IMAGE_HEIGHT)]
        if len(raw_img_data) < (IMAGE_WIDTH * min(num_lines, IMAGE_HEIGHT)):
            raw_img_data.extend(b'\x00' * (IMAGE_WIDTH * IMAGE_HEIGHT - len(raw_img_data)))

        # Cek enkripsi menggunakan variansi sederhana
        # Jika rata-rata derau tinggi, lakukan de-scramble
        dev2 = 0
        if len(raw_img_data) >= IMAGE_WIDTH * 2:
            row0 = raw_img_data[0:IMAGE_WIDTH]
            row1 = raw_img_data[IMAGE_WIDTH:IMAGE_WIDTH*2]
            mean = (sum(row0) + sum(row1)) / (IMAGE_WIDTH * 2)
            dev2 = sum((x - mean) ** 2 for x in row0) / IMAGE_WIDTH

        if dev2 >= 5000:
            # Lakukan dekripsi
            seed = random.randint(0, 0x7fffffff)
            buf = bytearray([
                key_number,
                seed & 0xff,
                (seed >> 8) & 0xff,
                (seed >> 16) & 0xff,
                (seed >> 24) & 0xff
            ])
            self.write_regs(REG_SCRAMBLE_DATA_INDEX, buf)
            key_bytes = self.read_regs(REG_SCRAMBLE_DATA_KEY, 4)
            key = struct.unpack("<I", key_bytes)[0] ^ seed

            img_bytes = bytearray(raw_img_data)
            lines_done = 0
            for flags, n_lines in block_info:
                if n_lines == 0 or lines_done >= num_lines:
                    break
                if flags & BLOCKF_CHANGE_KEY:
                    key_number = (key_number + 1) & 0xff
                    seed = random.randint(0, 0x7fffffff)
                    buf = bytearray([
                        key_number,
                        seed & 0xff,
                        (seed >> 8) & 0xff,
                        (seed >> 16) & 0xff,
                        (seed >> 24) & 0xff
                    ])
                    self.write_regs(REG_SCRAMBLE_DATA_INDEX, buf)
                    key_bytes = self.read_regs(REG_SCRAMBLE_DATA_KEY, 4)
                    key = struct.unpack("<I", key_bytes)[0] ^ seed

                block_len = IMAGE_WIDTH * n_lines
                if flags & BLOCKF_ENCRYPTED:
                    chunk = img_bytes[lines_done * IMAGE_WIDTH : (lines_done + n_lines) * IMAGE_WIDTH]
                    key = do_decode(chunk, key)
                    img_bytes[lines_done * IMAGE_WIDTH : (lines_done + n_lines) * IMAGE_WIDTH] = chunk
                elif (flags & (BLOCKF_NO_KEY_UPDATE | BLOCKF_ENCRYPTED)) == 0:
                    for _ in range(block_len):
                        key = update_key(key)

                if (flags & BLOCKF_NOT_PRESENT) == 0:
                    lines_done += n_lines
            raw_img_data = bytes(img_bytes)

        # Kembalikan mode ke OFF
        self.set_mode(MODE_OFF)

        # Buat image Pillow Grayscale (Mode L)
        img = Image.frombytes("L", (IMAGE_WIDTH, IMAGE_HEIGHT), raw_img_data[:IMAGE_WIDTH * IMAGE_HEIGHT])
        return img

    def close(self):
        try:
            self.set_mode(MODE_OFF)
            usb.util.dispose_resources(self.dev)
        except Exception:
            pass
