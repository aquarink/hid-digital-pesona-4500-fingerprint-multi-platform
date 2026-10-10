import os
import json
import base64
import zlib
import cv2
import numpy as np
from PIL import Image

DB_FILE = "users_db.json"
MATCH_THRESHOLD_MATCHES = 30  # Minimum good matches to declare a positive match

class FingerprintMatcher:
    def __init__(self):
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        self.sift = cv2.SIFT_create()
        self.index_params = dict(algorithm=1, trees=5)  # FLANN KDTree
        self.search_params = dict(checks=50)
        self.flann = cv2.FlannBasedMatcher(self.index_params, self.search_params)

    def preprocess(self, img_input):
        """Menerima PIL Image, file path, atau numpy array, lalu mengubahnya ke format grayscale enhanced"""
        if isinstance(img_input, str):
            gray = cv2.imread(img_input, cv2.IMREAD_GRAYSCALE)
        elif isinstance(img_input, Image.Image):
            gray = np.array(img_input.convert("L"))
        elif isinstance(img_input, np.ndarray):
            gray = img_input if len(img_input.shape) == 2 else cv2.cvtColor(img_input, cv2.COLOR_BGR2GRAY)
        else:
            raise ValueError("Tipe citra tidak didukung")

        # Tingkatkan kontras alur garis sidik jari
        enhanced = self.clahe.apply(gray)
        return enhanced

    def extract_descriptor(self, img_input):
        """Mengekstrak deskriptor fitur biometrik (SIFT) dari citra sidik jari"""
        enhanced = self.preprocess(img_input)
        keypoints, descriptors = self.sift.detectAndCompute(enhanced, None)
        return keypoints, descriptors

    def descriptor_to_template(self, descriptors) -> str:
        """Mengubah array numpy deskriptor menjadi string template base64 terkompresi"""
        if descriptors is None or len(descriptors) == 0:
            return ""
        raw_bytes = descriptors.astype(np.float32).tobytes()
        compressed = zlib.compress(raw_bytes)
        b64 = base64.b64encode(compressed).decode("utf-8")
        # Sertakan bentuk array agar bisa di-reconstruct
        shape_str = f"{descriptors.shape[0]}x{descriptors.shape[1]}"
        return f"{shape_str}:{b64}"

    def template_to_descriptor(self, template_str: str):
        """Mengembalikan string template ke numpy array descriptor"""
        if not template_str or ":" not in template_str:
            return None
        shape_part, b64_part = template_str.split(":", 1)
        rows, cols = map(int, shape_part.split("x"))
        raw_bytes = zlib.decompress(base64.b64decode(b64_part))
        descriptors = np.frombuffer(raw_bytes, dtype=np.float32).reshape((rows, cols))
        return descriptors

    def compare(self, des1, des2):
        """Membandingkan 2 deskriptor. Mengembalikan (score_persen, jumlah_titik_cocok)"""
        if des1 is None or des2 is None or len(des1) < 5 or len(des2) < 5:
            return 0.0, 0

        try:
            matches = self.flann.knnMatch(des1, des2, k=2)
            # Lowe's ratio test
            good = []
            for match_pair in matches:
                if len(match_pair) == 2:
                    m, n = match_pair
                    if m.distance < 0.75 * n.distance:
                        good.append(m)

            good_count = len(good)
            # Hitung skor relatif terhadap jumlah fitur minimum kedua gambar
            min_features = min(len(des1), len(des2))
            score = (good_count / min_features) * 100.0 if min_features > 0 else 0.0
            return min(score, 100.0), good_count
        except Exception:
            return 0.0, 0

class FingerprintDatabase:
    def __init__(self, db_path=DB_FILE):
        self.db_path = db_path
        self.matcher = FingerprintMatcher()
        self.users = self._load()

    def _load(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save(self):
        with open(self.db_path, "w") as f:
            json.dump(self.users, f, indent=2)

    def enroll(self, user_id: str, name: str, img_input):
        """Mendaftarkan sidik jari untuk user ID tertentu"""
        kp, des = self.matcher.extract_descriptor(img_input)
        if des is None or len(des) < 50:
            raise ValueError("Kualitas sidik jari kurang jelas untuk didaftarkan. Coba ulangi dengan tekanan pas.")

        template_str = self.matcher.descriptor_to_template(des)
        self.users[user_id] = {
            "id": user_id,
            "name": name,
            "feature_count": len(kp),
            "template": template_str
        }
        self._save()
        return len(kp)

    def identify(self, img_input, threshold_matches=MATCH_THRESHOLD_MATCHES):
        """
        Pencocokan 1:N (Identify).
        Mencari pemilik sidik jari di database.
        Mengembalikan (user_info, score, good_matches) jika cocok, atau None jika tidak cocok.
        """
        _, query_des = self.matcher.extract_descriptor(img_input)
        if query_des is None or len(query_des) < 10:
            return None, 0.0, 0

        best_user = None
        best_score = 0.0
        best_matches = 0

        for user_id, user_data in self.users.items():
            db_des = self.matcher.template_to_descriptor(user_data.get("template", ""))
            if db_des is None:
                continue

            score, good_matches = self.matcher.compare(query_des, db_des)
            if good_matches > best_matches:
                best_matches = good_matches
                best_score = score
                best_user = user_data

        if best_matches >= threshold_matches:
            return best_user, best_score, best_matches
        return None, best_score, best_matches

    def list_users(self):
        return list(self.users.values())

    def delete_user(self, user_id: str):
        if user_id in self.users:
            del self.users[user_id]
            self._save()
            return True
        return False
