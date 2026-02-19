# -*- coding: utf-8 -*-
"""
Created on Thu Feb 19 10:57:11 2026
gloria_qc_rrs
format gloria rrs cruise data to match seabass
@author: gianna.milton
"""
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


#read in all data with chl and metadata
gloria_22 = pd.read_csv(r'C:\Users\gianna.milton\Documents\Python\one off cruises\GLORIA-2022\GLORIA_2022\GLORIA_meta_and_lab.csv') #metadata
excel_file = pd.read_csv(r'C:\Users\gianna.milton\Documents\Python\one off cruises\GLORIA-2022\GLORIA_2022\GLORIA_Rrs.csv') #rrs data
excel_file = excel_file.drop('GLORIA_ID', axis=1) #remove duplicate id column to ensure consistannt columns

#since gloria_22 has the metadata for excel_file, and they match row wise, just concat
gloria_22 = pd.concat([gloria_22, excel_file],axis=1)

gloria_22=gloria_22.loc[gloria_22['Country']=='United States of America (the)'].reset_index(drop=True) 
#get rid of any rows with seabass ids since these we already have
gloria_22 = gloria_22[gloria_22['SeaBASS_ID'].isna()]
gloria_22 = gloria_22.dropna(axis=1, how='all')

#columns to not keep
columns_no=['GLORIA_ID', 'LIMNADES_ID', 'Data_collection_purpose','Sample_ID', 'Special_event_flag', 'Site_name', 'Country', 
             'Country_code', 'Platform','Water_body_type', 'Water_type', 'Elevation_asl', 'Wave_height', 'Wind_speed', 'Cloud_fraction', 'Distance_from_platform',
             'Platform_length', 'Platform_height', 'Distance_to_shore', 'Landcover', 'Topography','Distance_to_river_discharge', 
             'Optical_stability_of_water', 'Instrument_manufacturer', 'Instrument_model', 'Last_calibration', 'Measurement_method', 'Lt_nadir', 
             'Lt_relative_azimuth', 'Lsky_zenith','Lsky_relative_azimuth', 'Spectral_resolution', 'Number_of_radiometers','Field_of_view_Lt_radiometer',
             'Field_of_view_Lu_radiometer', 'Skyglint_removal', 'Bias_removal_in_NIR', 'Self_shading_correction','Viewing_angle_correction',
             'Availability_of_IOPs', 'Sample_depth', 'Water_collection_equipment', 'Chl_method', 'Phaeophytin_correction', 'TSS_method', 
             'aCDOM_method', 'Chla', 'Chla_plus_phaeo', 'TSS','aCDOM440', 'Turbidity', 'Secchi_depth', 'Comments']
gloria_22 = gloria_22.drop(columns_no, axis=1)

#rename columns 
gloria_22 = gloria_22.rename(columns={'Organization_ID':'affiliations','Dataset_ID':'experiment','Latitude':'lat','Longitude':'lon','Date_Time_UTC':'datetime',
                                  'Depth':'depth'})

#turn rrs into same format as seabass
rrs_cols = [col for col in gloria_22.columns if col.startswith('Rrs_')]

df_long = gloria_22.melt(id_vars=['affiliations', 'experiment', 'lat', 'lon', 'datetime', 'depth'], value_vars=rrs_cols,var_name='raw_wavelength',  value_name='rrs')
#remove the 'Rrs_' string from the column
df_long['raw_wavelength'] = df_long['raw_wavelength'].str.replace('Rrs_', '')
df_long['wavelength'] = pd.to_numeric(df_long['raw_wavelength'])
df_long = df_long.drop(columns=['raw_wavelength'])
df_long = df_long.dropna(subset=['rrs'])
df_long['source']='GLORIA'

#remove any inland data
shp = gpd.read_file(r'C:\Users\gianna.milton\Documents\Python\Shapefiles\combined_coastline.shp')
gdf = gpd.GeoDataFrame(df_long, geometry=gpd.points_from_xy(df_long.lon, df_long.lat), crs="EPSG:4269")
gdf = gdf.to_crs(shp.crs)
df_long = gpd.sjoin(gdf, shp, how="inner", predicate="within")
columns_to_drop = ['geometry', 'index_right', 'merge_id']
df_long = df_long.drop(columns=columns_to_drop)
df_long= df_long.reset_index(drop=True)

fig=plt.figure(figsize=(12, 12))
axs1=fig.add_subplot(1,1,1,projection= cartopy.crs.PlateCarree())
axs1.add_feature(cfeature.LAND)
axs1.add_feature(cfeature.OCEAN)
axs1.add_feature(cfeature.BORDERS)
im=axs1.scatter(df_long.lon,df_long.lat,s=10)
gl=axs1.gridlines(linewidth=0.2,color='grey',alpha=0.5,linestyle='-',
                draw_labels=True, x_inline= False,y_inline=False)
gl.xformatter=LONGITUDE_FORMATTER
gl.yformatter=LATITUDE_FORMATTER
gl.top_labels = False    # Disable top labels
gl.right_labels = False  # Disable right labels


df_long.to_excel('GLORIA_rrs_na.xlsx', index = False)















