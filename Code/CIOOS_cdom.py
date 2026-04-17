# -*- coding: utf-8 -*-
"""
Created on Thu Apr 16 13:50:32 2026
CIOOS_cdom
@author: gianna.milton
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import xarray as xr
import cartopy
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from shapely import geometry
import geopandas as gpd
from datetime import datetime
import os
from os.path import join, getsize
from matplotlib import ticker
import datetime as dt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import cmocean as cm
import cmocean.cm as cmo
from shapely.ops import unary_union
import matplotlib.gridspec as gridspec
from pyproj import Transformer
from erddapy import ERDDAP
import time
import matplotlib.ticker as mticker

keast  = {"min_time": "2000-01-01T00:00:00Z","max_time": "2025-12-12T00:00:00Z"}

server = "http://data.cioospacific.ca/erddap"
e = ERDDAP(server=server, protocol="tabledap")
url = e.get_search_url(search_for="cdom", response="csv",**keast) 
#no cdom in gulf, alaska, or hawaii
dfs = pd.read_csv(url)

dataframes_east_cdom = {}
dataframes_west_cdom = {}

reg_names_cdom = ['dataframes_east_cdom','dataframes_west_cdom']
df_names = ['dfs_east','dfs_west']

for idx2 in range(len(reg_names_cdom)):
    print('region '+reg_names_cdom[idx2])
    for idx, row in globals()[df_names[idx2]].iterrows():
        dataset_id = row['Dataset ID']
        e.dataset_id = dataset_id
        e.variables = ['time', 'latitude', 'longitude', 'cdom ','cdom_qc_agg','z']  #only append these columns
        try:
            print(f"Loading {dataset_id}...")
            df_data = e.to_pandas(index_col="time (UTC)")
            globals()[reg_names_cdom[idx2]][dataset_id] = df_data
            #add these to dataframe to ensure metadata is recorded
            globals()[reg_names_cdom[idx2]][dataset_id]['Dataset ID'] = dataset_id #add a column for dataset id
            globals()[reg_names_cdom[idx2]][dataset_id]['source'] = 'IOOS' #add source column
            globals()[reg_names_cdom[idx2]][dataset_id]['Institution'] = row['Institution'] #add institude column
            globals()[reg_names_cdom[idx2]][dataset_id]['url'] = row['Background Info'] #add link to sensor website
            globals()[reg_names_cdom[idx2]][dataset_id]['experiment'] = row['Title'] #add project to dataset
            time.sleep(1)  # small delay to avoid hammering the server
        except Exception as ex:
            print(f"Failed to load {dataset_id}") #{ex}
            
#rename for easier concatination
for idx2 in range(len(reg_names_cdom)):    
    for dsid, df in globals()[reg_names_cdom[idx2]].items():
        df = df.reset_index()
        df = df.rename(columns={'latitude (degrees_north)': 'lat', 'longitude (degrees_east)': 'lon', 'cdom (microg.L-1)': 'cdom',
            'cdom (1e-9)': 'cdom', 'z (m)': 'depth', 'time (UTC)':'datetime'})
        df.datetime=pd.to_datetime(df.datetime.astype(str),format='mixed')
        df = df[df['cdom_qc_agg'] != 3] #remove all 3s from dataframe i.e suspect points
        df = df[df['cdom_qc_agg'] != 4] #remove all 4s from dataframe i.e. failed points 
        
        globals()[reg_names_cdom[idx2]][dsid] = df  # update the dict

#reduced to 1 day average withing top 10 meters 
for idx2 in range(len(reg_names_cdom)):    
    for dsid, df in globals()[reg_names_cdom[idx2]].items(): 
        df=df[(df['depth']>=-10) & (df['depth']<=10)] #only within top 10 meters
        df['date'] = df['datetime'].dt.date
        df = df.drop(columns='datetime')
        df=df.groupby(['date','Dataset ID','source','Institution','url','experiment']).mean() #groupby date and take average
        globals()[reg_names_cdom[idx2]][dsid] = df.reset_index()
        

dataframes_east = pd.concat(dataframes_east_cdom.values(), ignore_index=True)
dataframes_west = pd.concat(dataframes_west_cdom.values(), ignore_index=True)

dfs=[dataframes_east,dataframes_west]
ioos_cdom = pd.concat(dfs).reset_index(drop=True)
ioos_cdom=ioos_cdom[['date', 'lat', 'lon', 'cdom','depth','Dataset ID', 'source', 'Institution','url', 'experiment',]]
ioos_cdom['date'] = pd.to_datetime(ioos_cdom['date'])
ioos_cdom = ioos_cdom.loc[ioos_cdom['date'] > '2000-01-01'] 
ioos_cdom = ioos_cdom.dropna(subset=['cdom'])
ioos_cdom['depth'] = ioos_cdom['depth'].abs() #make sure depth is not positive
 
ioos_cdom.to_excel('ioos_cdom_na.xlsx', index = False)

















