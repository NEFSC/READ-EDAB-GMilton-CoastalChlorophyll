# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 16:16:01 2026
Organize chlorophyll data from seamap. All data gathered from: https://seamapdata.gsmfc.org/seamap.download.php
@author: gianna.milton
"""
import pandas as pd
import geopandas as gpd

seamap_df = pd.read_csv(r'SeaMAP\SEAMAPDATAV3CSV\envrec.csv') #load in dataset
stations_df = pd.read_csv(r'SeaMAP\SEAMAPDATAV3CSV\starec.csv') #load in metadata

#match seamap_df to stations_df.START_DATE 
#seems like start and end date are withing a couple mins of each other, so fairly negligible which to choose as these are the start and end of a cast. same with lat and lon
stations_df['START_DATE'] = pd.to_datetime(stations_df['START_DATE'], errors='coerce') #chose START_DATE as datetime as sample 
stations_df=stations_df[['STATIONID', 'CRUISEID', 'VESSEL', 'CRUISE_NO', 'P_STA_NO','START_DATE','DECSLAT','DECSLON']] #subset metadata columns
seamap_df2 = pd.merge(seamap_df, stations_df, on=['STATIONID', 'CRUISEID', 'VESSEL', 'CRUISE_NO', 'P_STA_NO'], how='left').reset_index(drop=True) #merge two datasets based on similar metadata 
#need to make it such that if lat or lon in seamap are 0 or empty, replace with decslat and decslon from metadata 
seamap_df2['LATITUDE'] = seamap_df2['LATITUDE'].fillna(seamap_df2['DECSLAT'])
seamap_df2.loc[seamap_df2['LATITUDE'] == 0, 'LATITUDE'] = seamap_df2['DECSLAT']
seamap_df2['LONGITUDE'] = seamap_df2['LONGITUDE'].fillna(seamap_df2['DECSLON'])
seamap_df2.loc[seamap_df2['LONGITUDE'] == 0, 'LONGITUDE'] = seamap_df2['DECSLON']

#subbset dataset to relevant columns and rename to standard column names
seamap_df2=seamap_df2[['CRUISEID', 'START_DATE','LATITUDE','LONGITUDE', 'STATIONID','P_STA_NO','SECCHI_DSK','DEPTH_ESRF', 'DEPTH_EMID', 'DEPTH_EMAX', 'DEPTH_EWTR', 
                       'CHLORSURF','CHLORMID', 'CHLORMAX']]
seamap_df2 = seamap_df2.rename(columns={"DEPTH_ESRF": "depth_min", "DEPTH_EMID": "depth_mid","DEPTH_EMAX":"depth_max",'DEPTH_EWTR':'water_depth',
                                         "CHLORSURF": "chl_min", "CHLORMID": "chl_mid","CHLORMAX":"chl_max",
                                         "START_DATE": "datetime",'SECCHI_DSK':'secchi_depth','LATITUDE':'lat','LONGITUDE':'lon'}).reset_index(drop=True)
seamap_df2['row_id'] = seamap_df2.index #set row_id as the index
#Seamap data saves chlorophyll into 3 seperate columns: CHLORSURF, CHLORMID, CHLORMAX. so we need to create a single depth and chl column from these 3 distinct columns 
stubs = ['depth', 'chl']
seamap_df3 = pd.wide_to_long(seamap_df2,stubnames=stubs, i=['row_id','CRUISEID', 'datetime', 'lat', 'lon', 'P_STA_NO','STATIONID','secchi_depth','water_depth'], 
    j='level', sep='_',   suffix='\w+') #pivot a data table into more rows than more columns. stub names are the data that's getting pivoted, and i are the id variables that are remaining the same 
seamap_df3 = seamap_df3.reset_index()
seamap_df3 = seamap_df3.drop(columns=['row_id']) #drop column
seamap_df3 = seamap_df3.dropna(subset=['chl'], how='all') #if  chl empty, remove the row

#further standardize column names 
seamap_df3.rename(columns={"CRUISEID": "cruise", "P_STA_NO": "station", "date": "datetime", "Chl-a_µg/L": "chl_a"}, inplace=True)

#add metadata 
seamap_df3['source'] = 'SEAMAP'
seamap_df3['DOI_url'] = 'https://seamapdata.gsmfc.org/seamap.download.php'
seamap_df3['experiment'] = 'SEAMAP'
seamap_df3['investigators'] = 'Jeff Rester'
seamap_df3['affiliations'] = 'GSMFC'

seamap_df3['HPLC'] = 1 #no hplc used in methods 
#triplicates flag
counts_series = seamap_df3[['depth','datetime','lat','lon']].value_counts() #count how many unique cast,depth, datetime, lat, and lons there are
seamap_df3['triplicate'] = 1 #based on inpsecting counts_series, no triplicates

#subset data to shapefile 
shp = gpd.read_file(r'C:\Users\gianna.milton\Documents\Python\Shapefiles\combined_coastline.shp')
gdf = gpd.GeoDataFrame(seamap_df3, geometry=gpd.points_from_xy(seamap_df3.lon, seamap_df3.lat), crs="EPSG:4269")
gdf = gdf.to_crs(shp.crs)
seamap_df3 = gpd.sjoin(gdf, shp, how="inner", predicate="within")
columns_to_drop = ['geometry', 'index_right', 'merge_id', 'STATIONID', 'level','water_depth','secchi_depth']
seamap_df3 = seamap_df3.drop(columns=columns_to_drop)
seamap_df3= seamap_df3.reset_index(drop=True)
seamap_df3 = seamap_df3[seamap_df3['datetime'] > '2000-01-01'] #subset data to post 1999

seamap_df3.to_excel('seamap_chl.xlsx')

