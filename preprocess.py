import os
import numpy as np
import rasterio
from rasterio.enums import Resampling
from skimage.transform import resize
from scipy.ndimage import gaussian_filter, sobel
import matplotlib.pyplot as plt

# Paths 
base = os.getcwd()

sar_folder = os.path.join(base, "SAR_images")
landsat_folder = os.path.join(base, "Landsat_images")

output_sar = os.path.join(base, "preprocessed_SAR")
output_landsat = os.path.join(base, "preprocessed_Landsat")
output_combined = os.path.join(base, "preprocessed_combined")
output_analysis = os.path.join(base, "preprocessed_analysis")

# Create output folders
os.makedirs(output_sar, exist_ok=True)
os.makedirs(output_landsat, exist_ok=True)
os.makedirs(output_combined, exist_ok=True)
os.makedirs(output_analysis, exist_ok=True)

# === Helpers ===
def normalize(img):
    img = np.clip(img, a_min=0, a_max=None)
    return (img - img.min()) / (img.max() - img.min() + 1e-6)

def resize_image_to_shape(src, shape):
    return src.read(out_shape=(1, shape[0], shape[1]), resampling=Resampling.bilinear)[0]

def resize_array(img, shape):
    return resize(img, shape, preserve_range=True, anti_aliasing=True)

# === Loop for 10 images ===
for i in range(1, 11):
    try:
        # Load Landsat thermal
        landsat_path = os.path.join(landsat_folder, f"Landsat8_Thermal_{i}.tif")
        with rasterio.open(landsat_path) as src_land:
            band10 = normalize(src_land.read(1))
            band11 = normalize(src_land.read(2))
            target_shape = band10.shape

        # Load SAR and smooth
        sar_path = os.path.join(sar_folder, f"Sentinel1_SAR_{i}.tif")
        with rasterio.open(sar_path) as src_sar:
            sar_raw = src_sar.read(1)
            sar_norm = normalize(sar_raw)
            sar_resized = resize_image_to_shape(src_sar, target_shape)
            sar_smoothed = gaussian_filter(sar_resized, sigma=1.5)  # smoothing to remove speckle

        # SAR edge detection
        sar_edges = sobel(sar_smoothed)

        # Resize thermal B11 in case of mismatch
        band11_resized = resize_array(band11, target_shape)

        # Hotspot mask (thermal anomaly in both bands)
        hotspot_mask = ((band10 > 0.8) & (band11_resized > 0.8)).astype(np.uint8)

        # Save Preprocessed Arrays 
        np.save(os.path.join(output_sar, f"sar_{i}.npy"), sar_smoothed)
        np.save(os.path.join(output_landsat, f"landsat_b10_{i}.npy"), band10)
        np.save(os.path.join(output_landsat, f"landsat_b11_{i}.npy"), band11_resized)
        combined = np.stack([sar_smoothed, band10, band11_resized], axis=-1)
        np.save(os.path.join(output_combined, f"combined_{i}.npy"), combined)

        # =
        plt.imsave(os.path.join(output_sar, f"sar_{i}.png"), sar_smoothed, cmap='gray')
        plt.imsave(os.path.join(output_landsat, f"landsat_b10_{i}.png"), band10, cmap='inferno')
        plt.imsave(os.path.join(output_landsat, f"landsat_b11_{i}.png"), band11_resized, cmap='plasma')

        # Save analysis images
        plt.imsave(os.path.join(output_analysis, f"sar_edges_{i}.png"), sar_edges, cmap='gray')
        plt.imsave(os.path.join(output_analysis, f"hotspot_mask_{i}.png"), hotspot_mask * 255, cmap='hot')

        print(f"Completed full analysis for image {i}")

    except Exception as e:
        print(f"Error in image {i}: {e}")
