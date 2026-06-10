# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 09:42:57 2026
Consolidate Arctic Pigments into QA/QC formatted dataset with flags 
@author: gianna.milton
"""
import numpy as np
import pandas as pd
import geopandas as gpd


df = pd.read_excel(r'Consolidated Arctic Pigments\29445104\Consolidated_pigments.xlsx') #load in the dataset
df=df[df['environment '] != 'Ice'] #remove any ice measurments

df = df[[ 'Dataset', 'DOI', 'date', 'lat', 'lon', 'depth','Chl-a_µg/L']] #remove any unneeded variables and only retain chlorophyll
df.loc[2299, 'depth'] = 3 #at row 2299, in column depth, replace 03.maj with 3 to fix error in raw dataset
df.replace('na', np.nan, inplace=True) #standardize empty entries to np.nan
df['depth'] = df['depth'].astype(float) #ensure depth is in regular formatting
df['date'] = pd.to_datetime(df['date'], format='%Y%m%d', errors='coerce')#ensure date is in regular formatting

#triplicates flag
counts_series = df[['depth','date','lat','lon']].value_counts() #count how many unique cast,depth, datetime, lat, and lons there are
counts_df = counts_series.reset_index(name='freq_uniq')
df = pd.merge(df, counts_df, on=['depth','date','lat','lon'], how='left') #add frequency column to original dataframe4

#sometimes, triplicate specific times are recorded (ex: 3:00, 3:05, 3:10 ), so also check for unique datehour entries
df['date_hour'] = df['date'].dt.strftime('%Y-%m-%d %H')
counts_series = df[['depth','date_hour','lat','lon']].value_counts() #count how many unique datehour, lat, and lons there are
counts_df = counts_series.reset_index(name='freq_hour')
df = pd.merge(df, counts_df, on=['depth','date_hour','lat','lon'], how='left') #add frequency column to original dataframe
df['triplicate'] = 1 #assume bad unless otherwise said
df.loc[df['freq_uniq'] == 3, 'triplicate'] = 0 #if there was a unique datetime, lat, and lon that happened 3 times, triplicate
df.loc[(df['freq_uniq'] == 1) &(df['freq_hour'] == 3), 'triplicate'] = 0 #if 1 unique datetime but 3 unique date hours, assume triplicate

#according to the paper, all points are HPLC
df['HPLC'] = 0

#subset all data to the shapefile 
shp = gpd.read_file(r'Shapefiles\combined_coastline.shp')
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs="EPSG:4269")
gdf = gdf.to_crs(shp.crs)
df2 = gpd.sjoin(gdf, shp, how="inner", predicate="within")
columns_to_drop = ['geometry', 'index_right', 'merge_id']
df2 = df2.drop(columns=columns_to_drop)
df2= df2.reset_index(drop=True)

df.rename(columns={"Dataset": "experiment", "DOI": "url", "date": "datetime", "Chl-a_µg/L": "chl_a"}, inplace=True) #rename columns to match
#add metadata information 
df['source'] = 'arctic_pigment'
df['url'] = 'https://doi.org/10.11583/DTU.29445104'
df['contact'] = 'Asta Heidemann'
df['affiliation'] = 'Technical University of Denmark'

df = df.drop(columns=['freq_uniq', 'date_hour', 'freq_hour']) #drop any unneeded columns
df.to_excel('arctic_pigment_chl.xlsx')


