# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 11:10:48 2026
gloria_qc_chl, Organizing and cleaning chlorophyll data from GLORIA
@author: gianna.milton
"""
# -*- coding: utf-8 -*-
import pandas
import pandas as pd
import geopandas as gpd

gloria_22 = pd.read_csv(r'GLORIA-2022\GLORIA_2022\GLORIA_meta_and_lab.csv') #load in metadata

#list of columns to remove and are irrelevant
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
gloria_22 = gloria_22.dropna(subset=[ 'Chla']) #remove any empty chlorophyll rows

#standardize and rename columns 
gloria_22 = gloria_22.rename(columns={'Organization_ID':'affiliations','Dataset_ID':'experiment','Latitude':'lat','Longitude':'lon','Date_Time_UTC':'datetime',
                                  'Depth':'depth','Chla':'chl','SeaBASS_ID':'DOI_url'})

#remove any inland data by subsetting to shapefile
shp = gpd.read_file(r'C:\Users\gianna.milton\Documents\Python\Shapefiles\combined_coastline.shp')
gdf = gpd.GeoDataFrame(gloria_22, geometry=gpd.points_from_xy(gloria_22.lon, gloria_22.lat), crs="EPSG:4269")
gdf = gdf.to_crs(shp.crs)
gloria_22 = gpd.sjoin(gdf, shp, how="inner", predicate="within")
columns_to_drop = ['geometry', 'index_right', 'merge_id']
gloria_22 = gloria_22.drop(columns=columns_to_drop)
gloria_22= gloria_22.reset_index(drop=True)

gloria_22 = gloria_22.dropna(subset=[ 'depth']) #if any rows do not have depth values, remove
gloria_22=gloria_22.dropna(how='all', axis=1) #any empty columns, remove 

#triplicate
counts_series = gloria_22[['depth','datetime','lat','lon']].value_counts() #count how many unique cast,depth, datetime, lat, and lons there are
gloria_22['triplicate'] = 1 #based on inpsecting counts_series, no triplicates

gloria_22['HPLC'] = 1 #all remaining rows do not have a recorded chla_methods, so assume HPLC is not used
gloria_22['source']='GLORIA'
gloria_22 = gloria_22[gloria_22['datetime'] >= '2000-01-01'] #subset to data post 1999
gloria_22['DOI_url'] = gloria_22['DOI_url'].fillna('https://doi.pangaea.de/10.1594/PANGAEA.948492')


gloria_22.to_excel('GLORIA_chl_na.xlsx', index = False)

