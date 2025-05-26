from ultralytics import YOLO
import cv2
import numpy as np
from datetime import datetime

model = YOLO('best.pt')

label_colors = {
    0: (128, 0, 0),    # fragment_inside → hijau
    1: (0, 0, 139),    # fragment_outside → merah
}

def run_detection(img_path, edge_colors=None, centroid_colors=None, alpha=0.5):
    """
    edge_colors: dict {label: (B, G, R)}
    centroid_colors: dict {label: (B, G, R)}
    alpha: float, opacity mask overlay [0..1]
    """
    img = cv2.imread(img_path)
    
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

            default_mask_color = (255, 255, 255)
            mask_color = label_colors.get(label, default_mask_color)

            mask_img = np.zeros_like(img_mask_only, dtype=np.uint8)
            mask_img[m_bool] = mask_color
            
            # Gunakan parameter alpha untuk opacity overlay
            img_mask_only = cv2.addWeighted(img_mask_only, 1, mask_img, alpha, 0)

            m_uint8 = (m * 255).astype(np.uint8)
            contours, _ = cv2.findContours(m_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            edge_color = edge_colors.get(label, (0, 0, 0)) if edge_colors else (0, 0, 0)
            cv2.drawContours(img_mask_only, contours, -1, edge_color, 2)

            M = cv2.moments(m_uint8)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])

                centroid_color = centroid_colors.get(label, (0, 0, 0)) if centroid_colors else (0, 0, 0)
                cv2.circle(img_mask_only, (cx, cy), 4, centroid_color, -1)

    output_path = f"assets/detected_mask_only_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
    cv2.imwrite(output_path, img_mask_only)

    fragment_inside = int(np.sum(labels == 0))
    fragment_outside = int(np.sum(labels == 1))

    return output_path, fragment_inside, fragment_outside