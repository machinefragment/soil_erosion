# Pulling Prism Stuff
library(prism)
library(raster)
library(terra)
wd= 'C:/soil_erosion/tutorial_data'
setwd(wd)
prism_set_dl_dir('C:/soil_erosion/tutorial_data')

# get_prism_normals("ppt", "800m", annual = TRUE, keepZip = FALSE)

bil_raster <- "C:/soil_erosion/tutorial_data/PRISM_ppt_30yr_normal_800mM4_annual_bil/PRISM_ppt_30yr_normal_800mM4_annual_bil.bil"
rainfall_raster <-rast(bil_raster)
# Basic plot with handling for NA values
plot(rainfall_raster)
