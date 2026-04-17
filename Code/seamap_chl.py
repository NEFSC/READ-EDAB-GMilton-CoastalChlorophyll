# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 16:16:01 2026
Organize chlorophyll data from seamap
@author: gianna.milton
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cartopy
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import geopandas as gpd
import cmocean.cm as cmo

seamap_df = pd.read_csv(r'C:\Users\gianna.milton\Documents\Python\one off cruises\SeaMAP\SEAMAPDATAV3CSV\envrec.csv')
stations_df = pd.read_csv(r'C:\Users\gianna.milton\Documents\Python\one off cruises\SeaMAP\SEAMAPDATAV3CSV\starec.csv')
#match seamap_df to stations_df.START_DATE #seems like start and end date are withing a couple mins of each other, so fairly negligible which to choose. same w lat and lon
stations_df['START_DATE'] = pd.to_datetime(stations_df['START_DATE'], errors='coerce')
stations_df=stations_df[['STATIONID', 'CRUISEID', 'VESSEL', 'CRUISE_NO', 'P_STA_NO','START_DATE','DECSLAT','DECSLON']]
seamap_df2 = pd.merge(seamap_df, stations_df, on=['STATIONID', 'CRUISEID', 'VESSEL', 'CRUISE_NO', 'P_STA_NO'], how='left').reset_index(drop=True)
#need to make it such that if lat or lon in seamap are 0 or empty, replace with decslat and decslon
seamap_df2['LATITUDE'] = seamap_df2['LATITUDE'].fillna(seamap_df2['DECSLAT'])
seamap_df2.loc[seamap_df2['LATITUDE'] == 0, 'LATITUDE'] = seamap_df2['DECSLAT']
seamap_df2['LONGITUDE'] = seamap_df2['LONGITUDE'].fillna(seamap_df2['DECSLON'])
seamap_df2.loc[seamap_df2['LONGITUDE'] == 0, 'LONGITUDE'] = seamap_df2['DECSLON']

seamap_df2=seamap_df2[['CRUISEID', 'START_DATE','LATITUDE','LONGITUDE', 'STATIONID','P_STA_NO','SECCHI_DSK','DEPTH_ESRF', 'DEPTH_EMID', 'DEPTH_EMAX', 'DEPTH_EWTR', 
                       'CHLORSURF','CHLORMID', 'CHLORMAX']]
seamap_df2 = seamap_df2.rename(columns={"DEPTH_ESRF": "depth_min", "DEPTH_EMID": "depth_mid","DEPTH_EMAX":"depth_max",'DEPTH_EWTR':'water_depth',
                                         "CHLORSURF": "chl_min", "CHLORMID": "chl_mid","CHLORMAX":"chl_max",
                                         "START_DATE": "datetime",'SECCHI_DSK':'secchi_depth','LATITUDE':'lat','LONGITUDE':'lon'}).reset_index(drop=True)
seamap_df2['row_id'] = seamap_df2.index
stubs = ['depth', 'chl']
#turn into dataframe with 1 depth, 1 temp, ect, with i = the columns that stay constant
seamap_df3 = pd.wide_to_long(seamap_df2,stubnames=stubs, i=['row_id','CRUISEID', 'datetime', 'lat', 'lon', 'P_STA_NO','STATIONID','secchi_depth','water_depth'], 
    j='level', sep='_',   suffix='\w+')
seamap_df3 = seamap_df3.reset_index()
seamap_df3 = seamap_df3.drop(columns=['row_id'])
seamap_df3 = seamap_df3.dropna(subset=['chl'], how='all')

seamap_df3.rename(columns={"CRUISEID": "cruise", "P_STA_NO": "station", "date": "datetime", "Chl-a_µg/L": "chl_a"}, inplace=True)

seamap_df3['source'] = 'SEAMAP'
seamap_df3['DOI_url'] = 'https://seamapdata.gsmfc.org/seamap.download.php'
seamap_df3['experiment'] = 'SEAMAP'
seamap_df3['investigators'] = 'Jeff Rester'
seamap_df3['affiliations'] = 'GSMFC'

seamap_df3['HPLC'] = 1
counts_series = seamap_df3[['depth','datetime','lat','lon']].value_counts() #count how many unique cast,depth, datetime, lat, and lons there are
seamap_df3['triplicate'] = 1 #based on inpsecting counts_series, no triplicates


shp = gpd.read_file(r'C:\Users\gianna.milton\Documents\Python\Shapefiles\combined_coastline.shp')
gdf = gpd.GeoDataFrame(seamap_df3, geometry=gpd.points_from_xy(seamap_df3.lon, seamap_df3.lat), crs="EPSG:4269")
gdf = gdf.to_crs(shp.crs)
seamap_df3 = gpd.sjoin(gdf, shp, how="inner", predicate="within")
columns_to_drop = ['geometry', 'index_right', 'merge_id', 'STATIONID', 'level','water_depth','secchi_depth']
seamap_df3 = seamap_df3.drop(columns=columns_to_drop)
seamap_df3= seamap_df3.reset_index(drop=True)
seamap_df3 = seamap_df3[seamap_df3['datetime'] > '2000-01-01']

seamap_df3.to_excel('seamap_chl.xlsx')


fig=plt.figure(figsize=(7, 7))
axs1=fig.add_subplot(1,1,1,projection= cartopy.crs.PlateCarree())
axs1.add_feature(cfeature.LAND)
axs1.add_feature(cfeature.OCEAN)
im=axs1.scatter(seamap_df3.lon,seamap_df3.lat,c=seamap_df3['chl'],cmap=cmo.algae)
gl=axs1.gridlines(linewidth=0.2,color='grey',alpha=0.7,linestyle='-', draw_labels=True, x_inline= False,y_inline=False)
gl.xformatter=LONGITUDE_FORMATTER
gl.yformatter=LATITUDE_FORMATTER
cb=fig.colorbar(im,ax=axs1,orientation='horizontal')
cb.set_label('station',fontsize=12)