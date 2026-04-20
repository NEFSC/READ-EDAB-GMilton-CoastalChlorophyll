# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 11:10:48 2026
gloria_qc_chl
@author: gianna.milton
"""
# -*- coding: utf-8 -*-
import pandas
import pandas as pd
import warnings
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)
warnings.filterwarnings('ignore', category=FutureWarning)
import matplotlib.pyplot as plt
import cartopy
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import geopandas as gpd

gloria_22 = pd.read_csv(r'C:\Users\gianna.milton\Documents\Python\one off cruises\GLORIA-2022\GLORIA_2022\GLORIA_meta_and_lab.csv') #metadata

#columns to not keep
columns_no=['GLORIA_ID', 'LIMNADES_ID','LIMNADES_UID', 'Data_collection_purpose','Sample_ID', 'Special_event_flag', 'Site_name', 'Country', 
             'Country_code', 'Platform','Water_body_type', 'Water_type', 'Elevation_asl', 'Wave_height', 'Wind_speed', 'Cloud_fraction', 'Distance_from_platform',
             'Platform_length', 'Platform_height', 'Distance_to_shore', 'Landcover', 'Topography','Distance_to_river_discharge', 
             'Optical_stability_of_water', 'Instrument_manufacturer', 'Instrument_model', 'Last_calibration', 'Measurement_method', 'Lt_nadir', 
             'Lt_relative_azimuth', 'Lsky_zenith','Lsky_relative_azimuth', 'Spectral_resolution', 'Number_of_radiometers','Field_of_view_Lt_radiometer',
             'Field_of_view_Lu_radiometer', 'Skyglint_removal', 'Bias_removal_in_NIR', 'Self_shading_correction','Viewing_angle_correction',
             'Availability_of_IOPs', 'Water_collection_equipment', 'Turbidity', 'Phaeophytin_correction', 'TSS_method', 
              'Chla_plus_phaeo', 'TSS', 'Secchi_depth','aCDOM_method','aCDOM440', 'Comments','Rain_event_hour',
              'Additional_data_corrections', 'AOT'] 
gloria_22 = gloria_22.drop(columns_no, axis=1)
gloria_22 = gloria_22.dropna(subset=[ 'Chla'])

#rename columns 
gloria_22 = gloria_22.rename(columns={'Organization_ID':'affiliations','Dataset_ID':'experiment','Latitude':'lat','Longitude':'lon','Date_Time_UTC':'datetime',
                                  'Depth':'depth','Chla':'chl','SeaBASS_ID':'DOI_url'})

#remove any inland data
shp = gpd.read_file(r'C:\Users\gianna.milton\Documents\Python\Shapefiles\combined_coastline.shp')
gdf = gpd.GeoDataFrame(gloria_22, geometry=gpd.points_from_xy(gloria_22.lon, gloria_22.lat), crs="EPSG:4269")
gdf = gdf.to_crs(shp.crs)
gloria_22 = gpd.sjoin(gdf, shp, how="inner", predicate="within")
columns_to_drop = ['geometry', 'index_right', 'merge_id']
gloria_22 = gloria_22.drop(columns=columns_to_drop)
gloria_22= gloria_22.reset_index(drop=True)

gloria_22 = gloria_22.dropna(subset=[ 'depth'])
gloria_22=gloria_22.dropna(how='all', axis=1)

counts_series = gloria_22[['depth','datetime','lat','lon']].value_counts() #count how many unique cast,depth, datetime, lat, and lons there are
gloria_22['triplicate'] = 1 #based on inpsecting counts_series, no triplicates

gloria_22['HPLC'] = 1 #all remaining rows do not have a recorded chla_methods, so assume HPLC is not used
gloria_22['source']='GLORIA'
gloria_22 = gloria_22[gloria_22['datetime'] >= '2000-01-01']
gloria_22['DOI_url'] = gloria_22['DOI_url'].fillna('https://doi.pangaea.de/10.1594/PANGAEA.948492')


fig=plt.figure(figsize=(12, 12))
axs1=fig.add_subplot(1,1,1,projection= cartopy.crs.PlateCarree())
axs1.add_feature(cfeature.LAND)
axs1.add_feature(cfeature.OCEAN)
axs1.add_feature(cfeature.BORDERS)
im=axs1.scatter(gloria_22.lon,gloria_22.lat,s=10)
gl=axs1.gridlines(linewidth=0.2,color='grey',alpha=0.5,linestyle='-',
                draw_labels=True, x_inline= False,y_inline=False)
gl.xformatter=LONGITUDE_FORMATTER
gl.yformatter=LATITUDE_FORMATTER
gl.top_labels = False    # Disable top labels
gl.right_labels = False  # Disable right labels

gloria_22.to_excel('GLORIA_chl_na.xlsx', index = False)













