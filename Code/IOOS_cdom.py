# -*- coding: utf-8 -*-
"""
Created on Thu Feb 19 15:09:42 2026
IOOS_cdom, code to load in and organize cdom data from ioos
@author: gianna.milton
"""
import pandas as pd
from erddapy import ERDDAP
import time


#IOOS cdom data, first subset to regions for data processing ease. only data on east and west coast, not USA or Alaska for cdom
kwest  = {"min_lon": -131,"max_lon": -111,"min_lat": 19,"max_lat": 53,"min_time": "2000-01-01T00:00:00Z", "max_time": "2025-12-12T00:00:00Z"}
keast  = {"min_lon": -82,"max_lon": -47,"min_lat": 19,"max_lat": 50,"min_time": "2000-01-01T00:00:00Z","max_time": "2025-12-12T00:00:00Z"}
server = "http://erddap.sensors.ioos.us/erddap" #name of ioos erddap server
e = ERDDAP(server=server, protocol="tabledap")
url_west = e.get_search_url(search_for="cdom", response="csv",**kwest) #only pull data from within the boundries, search for cdom variable
url_east = e.get_search_url(search_for="cdom", response="csv",**keast) 
#read in dataset and transform into dataframe
dfs_east = pd.read_csv(url_east)
dfs_west = pd.read_csv(url_west)

#initiate empty dataframe for appending
dataframes_east_cdom = {}
dataframes_west_cdom = {}

#dataframe names to cycle through 
reg_names_cdom = ['dataframes_east_cdom','dataframes_west_cdom'] #dataframes for full dataset
df_names = ['dfs_east','dfs_west'] #dataframes for just dataset ID information

for idx2 in range(len(reg_names_cdom)): #for each dataframe
    print('region '+reg_names_cdom[idx2])
    for idx, row in globals()[df_names[idx2]].iterrows(): #for each row in the dataframe i.e for each project
        dataset_id = row['Dataset ID'] #pull the dataset id
        e.dataset_id = dataset_id #use erddap to gather that specific dataset 
        e.variables = ['time', 'latitude', 'longitude', 'cdom ','cdom_qc_agg','z']  #only append these columns
        try:
            print(f"Loading {dataset_id}...") #load in dataset
            df_data = e.to_pandas(index_col="time (UTC)") #transform into pandas dataframe
            globals()[reg_names_cdom[idx2]][dataset_id] = df_data #add the data from that dataset into the dataframe
            #add these to dataframe to ensure metadata is recorded
            globals()[reg_names_cdom[idx2]][dataset_id]['Dataset ID'] = dataset_id #add a column for dataset id
            globals()[reg_names_cdom[idx2]][dataset_id]['source'] = 'IOOS' #add source column
            globals()[reg_names_cdom[idx2]][dataset_id]['Institution'] = row['Institution'] #add institude column
            globals()[reg_names_cdom[idx2]][dataset_id]['url'] = row['Background Info'] #add link to sensor website
            globals()[reg_names_cdom[idx2]][dataset_id]['experiment'] = row['Title'] #add project to dataset
            time.sleep(1)  # small delay to avoid hammering the server
        except Exception as ex:
            print(f"Failed to load {dataset_id}") #{ex}
            
#rename columns to standard names 
for idx2 in range(len(reg_names_cdom)):    
    for dsid, df in globals()[reg_names_cdom[idx2]].items(): #for every dataframe
        df = df.reset_index()
        df = df.rename(columns={'latitude (degrees_north)': 'lat', 'longitude (degrees_east)': 'lon', 'cdom (microg.L-1)': 'cdom',
            'cdom (1e-9)': 'cdom', 'z (m)': 'depth', 'time (UTC)':'datetime'}) #rename columns
        df.datetime=pd.to_datetime(df.datetime.astype(str),format='mixed') #format datetime column
        df = df[df['cdom_qc_agg'] != 3] #remove all 3s from dataframe i.e suspect points
        df = df[df['cdom_qc_agg'] != 4] #remove all 4s from dataframe i.e. failed points 
        
        globals()[reg_names_cdom[idx2]][dsid] = df  # update the dict

#reduced to 1 day average withing top 10 meters 
for idx2 in range(len(reg_names_cdom)):    
    for dsid, df in globals()[reg_names_cdom[idx2]].items(): 
        df=df[(df['depth']>=-10) & (df['depth']<=10)] #only within top 10 meters
        df['date'] = df['datetime'].dt.date #calculate the date from datetime and remove datetime since datetime can't be averaged 
        df = df.drop(columns='datetime')
        df=df.groupby(['date','Dataset ID','source','Institution','url','experiment']).mean() #groupby date and take average
        globals()[reg_names_cdom[idx2]][dsid] = df.reset_index()
        
#concatinate all individual datasets into a single dataframe 
dataframes_east = pd.concat(dataframes_east_cdom.values(), ignore_index=True)
dataframes_west = pd.concat(dataframes_west_cdom.values(), ignore_index=True)
dfs=[dataframes_east,dataframes_west]
ioos_cdom = pd.concat(dfs).reset_index(drop=True)

ioos_cdom=ioos_cdom[['date', 'lat', 'lon', 'cdom','depth','Dataset ID', 'source', 'Institution','url', 'experiment',]]
ioos_cdom['date'] = pd.to_datetime(ioos_cdom['date'])
ioos_cdom = ioos_cdom.loc[ioos_cdom['date'] > '2000-01-01']  #only retain dates after 2000
ioos_cdom = ioos_cdom.dropna(subset=['cdom']) #if cdom empty, remove 
ioos_cdom['depth'] = ioos_cdom['depth'].abs() #make sure depth is not positive
 
ioos_cdom.to_excel('ioos_cdom_na.xlsx', index = False)


