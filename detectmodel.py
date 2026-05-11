import os
import cv2
import numpy as np

base = os.getcwd()
mask_folder = os.path.join(base, "outputs", "preprocessed_analysis")
output_label_folder = os.path.join(base, "outputs", "yolo_labels")

# Create label output folder 
os.makedirs(output_label_folder, exist_ok=True)

#  YOLO Label Generator Function 
def generate_yolo_labels(mask_path, output_path, image_index):
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    if mask is None:
        print(f"[!] Could not read: {mask_path}")
        return

    # Binarize the mask
    _, binary = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    h, w = mask.shape
    lines = []

    for contour in contours:
        x, y, box_w, box_h = cv2.boundingRect(contour)

        x_center = (x + box_w / 2) / w
        y_center = (y + box_h / 2) / h
        norm_w = box_w / w
        norm_h = box_h / h

        # YOLO format
        lines.append(f"0 {x_center:.6f} {y_center:.6f} {norm_w:.6f} {norm_h:.6f}")

    # Write label file
    label_file = os.path.join(output_path, f"hotspot_{image_index}.txt")
    with open(label_file, "w") as f:
        f.write("\n".join(lines))

    print(f"Saved {len(lines)} labels to {label_file}")


# Process all 10 masks 
for i in range(1, 11):
    mask_path = os.path.join(mask_folder, f"hotspot_mask_{i}.png")
    if os.path.exists(mask_path):
        generate_yolo_labels(mask_path, output_label_folder, i)
    else:
        print(f" Not found: {mask_path}")
