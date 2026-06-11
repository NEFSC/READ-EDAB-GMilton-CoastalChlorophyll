# -*- coding: utf-8 -*-
"""
Created on Thu Feb 19 10:57:11 2026
gloria_qc_rrs, organizing and cleaning rrs data from GLORIA
@author: gianna.milton
"""
import pandas
import pandas as pd
import geopandas as gpd


#read in rrs data and metadata
gloria_22 = pd.read_csv(r'C:\Users\gianna.milton\Documents\Python\one off cruises\GLORIA-2022\GLORIA_2022\GLORIA_meta_and_lab.csv') #metadata
excel_file = pd.read_csv(r'C:\Users\gianna.milton\Documents\Python\one off cruises\GLORIA-2022\GLORIA_2022\GLORIA_Rrs.csv') #rrs data
excel_file = excel_file.drop('GLORIA_ID', axis=1) #remove duplicate id column to ensure consistannt columns when concatinating 

#since gloria_22 has the metadata that matches row wise, just concat
gloria_22 = pd.concat([gloria_22, excel_file],axis=1)
gloria_22 = gloria_22.dropna(axis=1, how='all')

#list of irrelevant columns we don't need to keep
columns_no=['GLORIA_ID', 'LIMNADES_ID', 'Data_collection_purpose','Sample_ID', 'Special_event_flag', 'Site_name', 'Country', 
             'Country_code', 'Platform','Water_body_type', 'Water_type', 'Elevation_asl', 'Wave_height', 'Wind_speed', 'Cloud_fraction', 'Distance_from_platform',
             'Platform_length', 'Platform_height', 'Distance_to_shore', 'Landcover', 'Topography','Distance_to_river_discharge', 
             'Optical_stability_of_water', 'Instrument_manufacturer', 'Instrument_model', 'Last_calibration', 'Measurement_method', 'Lt_nadir', 
             'Lt_relative_azimuth', 'Lsky_zenith','Lsky_relative_azimuth', 'Spectral_resolution', 'Number_of_radiometers','Field_of_view_Lt_radiometer',
             'Field_of_view_Lu_radiometer', 'Skyglint_removal', 'Bias_removal_in_NIR', 'Self_shading_correction','Viewing_angle_correction',
             'Availability_of_IOPs', 'Sample_depth', 'Water_collection_equipment', 'Chl_method', 'Phaeophytin_correction', 'TSS_method', 
             'aCDOM_method', 'Chla', 'Chla_plus_phaeo', 'TSS','aCDOM440', 'Turbidity', 'Secchi_depth', 'Comments']
gloria_22 = gloria_22.drop(columns_no, axis=1)

#rename columns to standard column names
gloria_22 = gloria_22.rename(columns={'Organization_ID':'affiliations','Dataset_ID':'experiment','Latitude':'lat','Longitude':'lon','Date_Time_UTC':'datetime',
                                  'Depth':'depth','SeaBASS_ID':'DOI_url'})

#turn rrs into same format as seabass (i.e long format)
rrs_cols = [col for col in gloria_22.columns if col.startswith('Rrs_')] #grab all columns with name rrs

#transform dataset
df_long = gloria_22.melt(id_vars=['affiliations', 'experiment', 'lat', 'lon', 'datetime', 'depth','DOI_url'], value_vars=rrs_cols,var_name='raw_wavelength',  value_name='rrs')
#remove the 'Rrs_' string from the column
df_long['raw_wavelength'] = df_long['raw_wavelength'].str.replace('Rrs_', '') #just retain wavelength value
df_long['wavelength'] = pd.to_numeric(df_long['raw_wavelength']) #ensure values are numeric
df_long = df_long.drop(columns=['raw_wavelength']) #drop unneeded column
df_long = df_long.dropna(subset=['rrs']) #drop any empty columns
df_long['source']='GLORIA'

#if DOI_url is empty, refer to the doi of paper 'https://doi.pangaea.de/10.1594/PANGAEA.948492
df_long['DOI_url'] = df_long['DOI_url'].fillna('https://doi.pangaea.de/10.1594/PANGAEA.948492')

#remove any inland data by subsetting to shapefile 
shp = gpd.read_file(r'C:\Users\gianna.milton\Documents\Python\Shapefiles\combined_coastline.shp')
gdf = gpd.GeoDataFrame(df_long, geometry=gpd.points_from_xy(df_long.lon, df_long.lat), crs="EPSG:4269")
gdf = gdf.to_crs(shp.crs)
df_long = gpd.sjoin(gdf, shp, how="inner", predicate="within")
columns_to_drop = ['geometry', 'index_right', 'merge_id']
df_long = df_long.drop(columns=columns_to_drop)
df_long= df_long.reset_index(drop=True)

df_long = df_long[df_long['datetime'] >= '2000-01-01'] #only keep data since 2000

df_long.to_excel('GLORIA_rrs_na.xlsx', index = False)

