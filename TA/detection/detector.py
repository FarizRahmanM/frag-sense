import os
import cv2
import numpy as np
from datetime import datetime
from utils import resource_path
from ultralytics import YOLO
import time
import tempfile


model_cache = {}


label_colors = {
    0: (128, 0, 0),    # fragment_inside → merah tua
    1: (0, 0, 139),    # fragment_outside → biru tua
}

def get_model(model_name="best.pt"):
    if model_name not in model_cache:
        model_path = resource_path(os.path.join("models", model_name))
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model tidak ditemukan: {model_path}")
        model_cache[model_name] = YOLO(model_path)
    return model_cache[model_name]

def get_output_folder():
    user_data_dir = os.path.join(os.getenv('APPDATA'), "FragSense")  # Atau Documents
    output_folder = os.path.join(user_data_dir, "assets")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    return output_folder

def run_detection(img_path, model_name="best.pt", edge_colors=None, centroid_colors=None, alpha=0.5):
    img_original = cv2.imread(img_path)
    if img_original is None:
        raise ValueError(f"Gagal membaca gambar: {img_path}")

    img = cv2.resize(img_original, (640, 640))
    model = get_model(model_name)

    start_time = time.time()
    results = model(img)
    inference_time = time.time() - start_time   

    result = results[0]
    img_dots_only = img.copy()
    img_numbered = img.copy()
    masks = result.masks
    labels = result.boxes.cls.cpu().numpy()

    centroids = []

    if masks is not None:
        mask_array = masks.data.cpu().numpy()

        for idx, m in enumerate(mask_array):
            m_bool = m.astype(bool)
            label = int(labels[idx])

            mask_color = label_colors.get(label, (255, 255, 255))

            # Buat masker untuk kedua gambar
            mask_img = np.zeros_like(img, dtype=np.uint8)
            mask_img[m_bool] = mask_color
            img_dots_only = cv2.addWeighted(img_dots_only, 1, mask_img, alpha, 0)
            img_numbered = cv2.addWeighted(img_numbered, 1, mask_img, alpha, 0)

            m_uint8 = (m * 255).astype(np.uint8)
            contours, _ = cv2.findContours(m_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            edge_color = edge_colors.get(label, (0, 0, 0)) if edge_colors else (0, 0, 0)
            cv2.drawContours(img_dots_only, contours, -1, edge_color, 2)
            cv2.drawContours(img_numbered, contours, -1, edge_color, 2)

            M = cv2.moments(m_uint8)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                centroids.append((cy, cx, label))  # simpan dengan format (y, x, label)

        centroids.sort()  # urutkan dari atas ke bawah (y kecil ke besar)

        for cy, cx, label in centroids:
            dot_color = (0, 0, 0)  # hitam
            cv2.circle(img_dots_only, (cx, cy), 3, dot_color, -1)

        # 2. Tambahkan angka hanya ke img_numbered
        for i, (cy, cx, label) in enumerate(centroids):
            text = str(i + 1)
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            thickness = 2
            text_color = label_colors.get(label, (255, 255, 255))  # putih agar kontras
            cv2.putText(img_numbered, text, (cx - 10, cy + 5), font, font_scale, text_color, thickness, cv2.LINE_AA)

    # Simpan ke folder temp
    temp_dir = tempfile.gettempdir()
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

    dot_filename = f"detected_dots_only_{timestamp}.jpg"
    numbered_filename = f"detected_numbered_{timestamp}.jpg"

    dot_path = os.path.join(temp_dir, dot_filename)
    numbered_path = os.path.join(temp_dir, numbered_filename)

    cv2.imwrite(dot_path, img_dots_only)
    cv2.imwrite(numbered_path, img_numbered)

    fragment_inside = int(np.sum(labels == 0))
    fragment_outside = int(np.sum(labels == 1))

    # Kembalikan hanya path gambar dengan titik (dot_path), tapi hasil numbered juga bisa digunakan nanti
    return dot_path, numbered_path, fragment_inside, fragment_outside, inference_time