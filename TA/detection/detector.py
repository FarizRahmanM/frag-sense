import os
import cv2
import numpy as np
from datetime import datetime
from utils import resource_path
from ultralytics import YOLO


model = None


label_colors = {
    0: (128, 0, 0),    # fragment_inside → merah tua
    1: (0, 0, 139),    # fragment_outside → biru tua
}

def get_model():
    global model
    if model is None:
        model_path = resource_path("best.pt")
        model = YOLO(model_path)
    return model

def get_output_folder():
    output_folder = os.path.join(os.getcwd(), "assets")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    return output_folder

def run_detection(img_path, edge_colors=None, centroid_colors=None, alpha=0.5):
    img = cv2.imread(img_path)
    if img is None:
        raise ValueError(f"Gagal membaca gambar: {img_path}")

    original_h, original_w = img.shape[:2]
    model = get_model()

    results = model(img)
    result = results[0]

    img_mask_only = img.copy()
    masks = result.masks
    labels = result.boxes.cls.cpu().numpy()

    if masks is not None:
        mask_array = masks.data.cpu().numpy()

        for idx, m in enumerate(mask_array):
            m_bool = m.astype(bool)
            label = int(labels[idx])

            # --- Resize m_bool agar cocok dengan ukuran gambar asli ---
            m_bool_resized = cv2.resize(m_bool.astype(np.uint8), (original_w, original_h), interpolation=cv2.INTER_NEAREST)
            m_bool_resized = m_bool_resized.astype(bool)

            mask_color = label_colors.get(label, (255, 255, 255))  # Default putih
            mask_img = np.zeros_like(img_mask_only, dtype=np.uint8)

            mask_img[m_bool_resized] = mask_color
            img_mask_only = cv2.addWeighted(img_mask_only, 1, mask_img, alpha, 0)

            # Buat kontur dari m_bool_resized
            m_uint8 = (m_bool_resized * 255).astype(np.uint8)
            contours, _ = cv2.findContours(m_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            edge_color = edge_colors.get(label, (0, 0, 0)) if edge_colors else (0, 0, 0)
            cv2.drawContours(img_mask_only, contours, -1, edge_color, 2)

            # Centroid
            M = cv2.moments(m_uint8)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                centroid_color = centroid_colors.get(label, (0, 0, 0)) if centroid_colors else (0, 0, 0)
                cv2.circle(img_mask_only, (cx, cy), 4, centroid_color, -1)

    output_folder = get_output_folder()
    filename = f"detected_mask_only_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
    output_path = os.path.join(output_folder, filename)
    cv2.imwrite(output_path, img_mask_only)

    fragment_inside = int(np.sum(labels == 0))
    fragment_outside = int(np.sum(labels == 1))

    return output_path, fragment_inside, fragment_outside

