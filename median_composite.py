'''
 Write a function that takes a list of satellite images and returns their median composite.
 Note: make sure you take into consideration that satellite images do not always completely overlap spatially.
 Apply the function to the images you downloaded previously.

Reference:
http://xarray.pydata.org/
https://rasterio.readthedocs.io/en/latest/topics/writing.html
'''
import os
import sys
import xarray as xr
import rasterio as rio
import yaml

def main():

    # load configuration file config.yaml
    cfg = None
    try:
        with open("../config.yaml", "r") as ymlfile:
            cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
    except Exception as e:
        print('Configuration file not found: %s',e)
        sys.exit()

    # Assign parameters from config.yaml
    output=cfg["output_median"]
    driver = cfg["driver"]
    num_of_bands=cfg["number_of_bands"]
    input_path=cfg["input_folder"]

    #calculate raster profile as xarray data arrays
    imgs, imgs_profile = calc_raster_profile(input_path)

    # calculate median composite depending on no. of bands specified in config.yaml
    median_img = median_comp(imgs, num_of_bands)

    # write median composite to output raster as mentioned in config.yaml using rasterio
    write_median_composite_output(imgs_profile, median_img, output, driver)

# calculate median composite
def calc_raster_profile(imgs_path):
    print('Calculating raster profile')
    images = []
    profile = None
    for root, dirs, files in os.walk(imgs_path, topdown=True):
        for file in files:
            if profile is None:
                with rio.open(os.path.join(root, file)) as img:
                    profile = img.profile
            images.append(xr.open_rasterio(os.path.join(root, file),
                                           chunks={'x': 1024, 'y': 1024}))
    return (images, profile)

# calculate median composite
def median_comp(imgs, no_of_bands):
    bands_medians = []
    for b in range(no_of_bands):
        #extract each slice of a multi-dimensional array of x-y-band
        bands = [img.sel(band=b+1) for img in imgs]
        #creating band composite
        bands_comp = xr.concat(bands, dim='band')
        #creating median of all the band composites while skipping pixel with no data in each band composite
        median = bands_comp.median(dim='band', skipna=True)
        bands_medians.append(median)
    #3D array of band X-Y-Band dimensions
    dataset = xr.concat(bands_medians, dim='band')
    print('Completed median composite!')
    return dataset

# write median composite to output raster as mentioned in config.yaml using rasterio
def write_median_composite_output(imgs_profile, median_comp, save_path, driver):
    print('Saving median composite. Default setting is GeoTiff in config.yaml')
    imgs_profile.update(driver='GTiff')
    with rio.open(save_path, 'w', **imgs_profile) as dst:
        dst.write(median_comp.astype(rio.uint8))

if __name__ == '__main__':
    main()


