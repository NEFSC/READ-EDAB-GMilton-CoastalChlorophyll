# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 09:42:57 2026
Consolidated Arctic Pigments
@author: gianna.milton
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cartopy
import cartopy.feature as cfeature
import cmocean.cm as cmo
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import geopandas as gpd


df = pd.read_excel(r'C:\Users\gianna.milton\Documents\Python\one off cruises\Consolidated Arctic Pigments\29445104\Consolidated_pigments.xlsx')
df=df[df['environment '] != 'Ice'] #remove any ice measurments, only keep water 

df = df[[ 'Dataset', 'DOI', 'date', 'lat', 'lon', 'depth','Chl-a_µg/L']]
df.loc[2299, 'depth'] = 3 #at row 2299, in column depth, replace 03.maj with 3 
df.replace('na', np.nan, inplace=True)
df['depth'] = df['depth'].astype(float)
df['date'] = pd.to_datetime(df['date'], format='%Y%m%d', errors='coerce')

#triplicates
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

#subset to the shapefile 
shp = gpd.read_file(r'C:\Users\gianna.milton\Documents\Python\Shapefiles\combined_coastline.shp')
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs="EPSG:4269")
gdf = gdf.to_crs(shp.crs)
df2 = gpd.sjoin(gdf, shp, how="inner", predicate="within")
columns_to_drop = ['geometry', 'index_right', 'merge_id']
df2 = df2.drop(columns=columns_to_drop)
df2= df2.reset_index(drop=True)

df.rename(columns={"Dataset": "experiment", "DOI": "url", "date": "datetime", "Chl-a_µg/L": "chl_a"}, inplace=True)
df['source'] = 'arctic_pigment'
df['url'] = 'https://doi.org/10.11583/DTU.29445104'
df['contact'] = 'Asta Heidemann'
df['affiliation'] = 'Technical University of Denmark'

df = df.drop(columns=['freq_uniq', 'date_hour', 'freq_hour']) # Multiple columns
df.to_excel('arctic_pigment_chl.xlsx')


fig=plt.figure(figsize=(7, 7))
axs1=fig.add_subplot(1,1,1,projection= cartopy.crs.PlateCarree())
axs1.add_feature(cfeature.LAND)
axs1.add_feature(cfeature.OCEAN)
im=axs1.scatter(df2.lon,df2.lat,c=df2['Chl-a_µg/L'],cmap=cmo.algae)
axs1.set_title('Chlorophyll')
gl=axs1.gridlines(linewidth=0.2,color='grey',alpha=0.7,linestyle='-', draw_labels=True, x_inline= False,y_inline=False)
gl.xformatter=LONGITUDE_FORMATTER
gl.yformatter=LATITUDE_FORMATTER
cb=fig.colorbar(im,ax=axs1,orientation='horizontal')
cb.set_label('chlorophyll (mg/L)',fontsize=12)





