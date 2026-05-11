
import ee

ee.Authenticate()


ee.Initialize(project='ee-elafaljohar11')

# Area of interest (Deer Park) and time range
aoi = ee.Geometry.Rectangle([-95.1600, 29.6800, -95.1000, 29.7300])
start = '2014-04-01'
end = '2024-12-31'

# Load Sentinel-1 SAR (VV) and Landsat 8 thermal bands (B10, B11)
sentinel1 = ee.ImageCollection("COPERNICUS/S1_GRD") \
    .filterBounds(aoi) \
    .filterDate(start, end) \
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')) \
    .select('VV')

landsat8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_TOA") \
    .filterBounds(aoi) \
    .filterDate(start, end) \
    .select(['B10', 'B11'])

print("Loading dataset is done.")

# Get available image timestamps
sar_dates = sentinel1.aggregate_array('system:time_start').getInfo()
landsat_dates = landsat8.aggregate_array('system:time_start').getInfo()

if len(sar_dates) == 0 or len(landsat_dates) == 0:
    print("No images found in one or both datasets.")
else:
    # Match closest Landsat date to each SAR date
    def find_closest_landsat(sar_date):
        differences = [abs(l - sar_date) for l in landsat_dates]
        if not differences:
            return None
        return landsat_dates[differences.index(min(differences))]

    matched_pairs = [(s, find_closest_landsat(s)) for s in sar_dates]
    matched_pairs = [(s, l) for s, l in matched_pairs if l is not None][:10]

    if not matched_pairs:
        print("No matching image pairs found.")
    else:
        print(f"Found {len(matched_pairs)} matching SAR + Landsat pairs!\n")
        print("Selected image dates:")

        for i, (sar_date, landsat_date) in enumerate(matched_pairs):
            sar_str = ee.Date(sar_date).format('YYYY-MM-dd').getInfo()
            land_str = ee.Date(landsat_date).format('YYYY-MM-dd').getInfo()
            print(f"Pair {i+1}: SAR → {sar_str} | Landsat → {land_str}")

            sar_image = sentinel1.filter(ee.Filter.eq('system:time_start', sar_date)).first()
            landsat_image = landsat8.filter(ee.Filter.eq('system:time_start', landsat_date)).first()

            # Export SAR image to "SAR images"
            sar_export = ee.batch.Export.image.toDrive(
                image=sar_image,
                description=f'Sentinel1_SAR_{i+1}',
                folder='SAR images',
                scale=10,
                region=aoi,
                fileFormat='GeoTIFF'
            )

            # Export Landsat thermal image to "Landsat images"
            landsat_export = ee.batch.Export.image.toDrive(
                image=landsat_image,
                description=f'Landsat8_Thermal_{i+1}',
                folder='Landsat images',
                scale=30,
                region=aoi,
                fileFormat='GeoTIFF'
            )

            sar_export.start()
            landsat_export.start()

        print("\n Export started for:")
        print("- SAR images → MyDrive > SAR images")
        print("- Landsat images → MyDrive > Landsat images")
