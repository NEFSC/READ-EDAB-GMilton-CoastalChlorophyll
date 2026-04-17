# -*- coding: utf-8 -*-
"""
Created on Thu Feb  5 14:45:44 2026
ioos_chl
load in IOOS data by region and orgainize it, including HPLC and triplicate flags 
@author: gianna.milton
"""
import numpy as np
import pandas as pd
from erddapy import ERDDAP
import time
import warnings
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)
warnings.filterwarnings('ignore', category=FutureWarning)


#Seperate datasets into regions for easier manegment 

kwest  = {"min_lon": -131, #boundries for west coast
    "max_lon": -111,
    "min_lat": 19,
    "max_lat": 53,
    "min_time": "2000-01-01T00:00:00Z",
    "max_time": "2025-04-28T00:00:00Z"}

keast  = {"min_lon": -82, #boundries for east coast
    "max_lon": -47,
    "min_lat": 19,
    "max_lat": 50,
    "min_time": "2000-01-01T00:00:00Z",
    "max_time": "2025-04-28T00:00:00Z"}

kgulf  = {"min_lon": -103, #boundries for gulf of mexico
    "max_lon": -82,
    "min_lat": 17,
    "max_lat": 34,
    "min_time": "2000-01-01T00:00:00Z",
    "max_time": "2025-04-28T00:00:00Z"}


kalas  = {"min_lon": -168, #boundries for alaska
    "max_lon": -135,
    "min_lat": 51,
    "max_lat": 77,
    "min_time": "2000-01-01T00:00:00Z",
    "max_time": "2025-04-28T00:00:00Z"}

khaw  = {"min_lon": -162, #boundries for hawaii
    "max_lon": -150,
    "min_lat": 15,
    "max_lat": 23,
    "min_time": "2000-01-01T00:00:00Z",
    "max_time": "2025-04-28T00:00:00Z"}

#load in chl for each region
server = "http://erddap.sensors.ioos.us/erddap" #ioos erddap server
e = ERDDAP(server=server, protocol="tabledap")
url_west = e.get_search_url(search_for="mass_concentration_of_chlorophyll_in_sea_water", response="csv",**kwest) #only pull chlorophyll data from within the boundries
url_east = e.get_search_url(search_for="mass_concentration_of_chlorophyll_in_sea_water", response="csv",**keast) 
url_gulf = e.get_search_url(search_for="mass_concentration_of_chlorophyll_in_sea_water", response="csv",**kgulf) 
url_alas = e.get_search_url(search_for="mass_concentration_of_chlorophyll_in_sea_water", response="csv",**kalas) 
url_haw = e.get_search_url(search_for="mass_concentration_of_chlorophyll_in_sea_water", response="csv",**khaw) 

#read each url in
dfs_east = pd.read_csv(url_east)
dfs_west = pd.read_csv(url_west)
dfs_gulf = pd.read_csv(url_gulf)
dfs_alas = pd.read_csv(url_alas)
dfs_haw = pd.read_csv(url_haw)
#dfs includes the projects/ buoys that are recorded in the regional boundries
#title = title of project
#includes institution and dataset ID number 

dataframes_east = {}
dataframes_west = {}
dataframes_gulf = {}
dataframes_ak = {}
dataframes_haw = {}

reg_names = ['dataframes_east','dataframes_west','dataframes_gulf','dataframes_ak','dataframes_haw'] #create a dataframe for each region 
df_names = ['dfs_east','dfs_west','dfs_gulf','dfs_alas','dfs_haw']

for idx2 in range(len(reg_names)): #for each reg_name
    print('region '+reg_names[idx2]) 
    for idx, row in globals()[df_names[idx2]].iterrows(): #for every project in the df_names
        dataset_id = row['Dataset ID'] #identify the id
        e.dataset_id = dataset_id #match the id with the e dictionary
        e.variables = ['time', 'latitude', 'longitude', 'mass_concentration_of_chlorophyll_in_sea_water',
                       'z','mass_concentration_of_chlorophyll_in_sea_water_qc_agg']  #only append these variables
        try:
            print(f"Loading {dataset_id}...")
            df_data = e.to_pandas(index_col="time (UTC)") #create dataframe from e indexing the time
            globals()[reg_names[idx2]][dataset_id] = df_data #add the dataframe to the reg_name by id
            #add these to dataframe to ensure metadata is recorded
            globals()[reg_names[idx2]][dataset_id]['Dataset ID'] = dataset_id #add a column for dataset id
            globals()[reg_names[idx2]][dataset_id]['source'] = 'IOOS' #add source column
            globals()[reg_names[idx2]][dataset_id]['Institution'] = row['Institution'] #add institude column
            globals()[reg_names[idx2]][dataset_id]['url'] = row['Background Info'] #add link to sensor website
            globals()[reg_names[idx2]][dataset_id]['experiment'] = row['Title'] #add project to dataset

            time.sleep(1)  # small delay to avoid hammering the server
        except Exception as ex:
            print(f"Failed to load {dataset_id}: {ex}") #if no chlorophyll in the dataset, this allows it to skip those

#rename the columns in all reg_names and remove bad flags
for idx2 in range(len(reg_names)):    
    for dsid, df in globals()[reg_names[idx2]].items():
        df = df.reset_index()
        df = df.rename(columns={'latitude (degrees_north)': 'lat','longitude (degrees_east)': 'lon',
            'mass_concentration_of_chlorophyll_in_sea_water (microg.L-1)': 'chl', #micro gram/L == mg/m^3, so same units as seabass
            'mass_concentration_of_chlorophyll_in_sea_water_qc_agg': 'chl_qc_t','z (m)': 'depth', 'time (UTC)':'datetime'})
        df.datetime=pd.to_datetime(df.datetime.astype(str),format='mixed')
        #remove bad flags
        df = df[df['chl_qc_t'] != 3] #remove all 3s from dataframe i.e suspect points
        df = df[df['chl_qc_t'] != 4] #remove all 4s from dataframe i.e. failed points 

        globals()[reg_names[idx2]][dsid] = df  #update the dict

#create time and depth flags
for idx2 in range(len(reg_names)): #for every region's dataframe
    for dsid, df in globals()[reg_names[idx2]].items(): #for every dataframe in the region   
        df = df.sort_values(by='datetime')
        df['t_flag']=0 #initialize temporal resolution flag, 0=good, 1= bad (less than 1hour),2=flag (time is 0 i.e repeated)
        df['diff_time'] = 0 #column to populate with datatypes as values for organization
        df['d_flag'] = 0 #initialize depth flag, 0=good, 1=bad (less than 5m), 2=flag
        df['decision'] = 2 #ultimate decision flag inidcating whether to keep or toss data point (0=good, 1=bad,2=flag)
        
        df['diff_time']= df['datetime'].diff()      
        df.t_flag=np.where(df['diff_time']< pd.to_timedelta('10 minutes'), 1, df.t_flag) #if delta t is less than 1 hour, flag as bad
        df.t_flag=np.where(df['diff_time']== pd.to_timedelta(0), 2, df.t_flag) #if 0, then just a repeat so not necessarily bad       
        if 'depth' in df.columns: #find average change in depth
            depth_diff =abs(df.depth.diff())#calculate absolute change in depth
            df.loc[df[depth_diff<1].index,'d_flag']=1 #if the change in depth is not large enough
            df.loc[df[depth_diff==0].index,'d_flag']=2 #if the change in depth doesn't move, set as 2, diff_time 
        else:
            avg_z_res = None
            
        df.decision[(df['t_flag'] ==0) & (df['d_flag']==0)] = 0 #if both good, then good
        df.decision[(df['t_flag'] ==0) & (df['d_flag']==1)] = 1 #if everything else is good but the depth is too short, flag as nad
        df.decision[(df['t_flag'] ==0) & (df['d_flag']==2)] = 0 #if everything else is good and depth repeats, good
        df.decision[(df['t_flag'] ==1) & (df['d_flag']==0)] = 1 #IF TIME IS EVER BAD then the whole thing is bad
        df.decision[(df['t_flag'] ==1) & (df['d_flag']==1)] = 1
        df.decision[(df['t_flag'] ==1) & (df['d_flag']==2)] = 1
        df.decision[(df['t_flag'] ==2) & (df['d_flag']==0)] = 0
        df.decision[(df['t_flag'] ==2) & (df['d_flag']==1)] = 1
        df.decision[(df['t_flag'] ==2) & (df['d_flag']==2)] = 1
            
        globals()[reg_names[idx2]][dsid] = df  #update the dict



#reduced to 1 day average withing top 10 meters 
for idx2 in range(len(reg_names)):    
    for dsid, df in globals()[reg_names[idx2]].items(): 
        df=df[(df['depth']>=-10) & (df['depth']<=10)] #only within top 10 meters
        df['date'] = df['datetime'].dt.date
        df = df.drop(columns='datetime')
        df=df.groupby(['date','Dataset ID','source','Institution','url','experiment']).mean() #groupby date and take average
        globals()[reg_names[idx2]][dsid] = df.reset_index()

#turn the dictionary of dataframes into 1 single dataframe with all values concatinated 
dataframes_east2 = pd.concat(dataframes_east.values(), ignore_index=True)
dataframes_west2 = pd.concat(dataframes_west.values(), ignore_index=True)
dataframes_gulf2 = pd.concat(dataframes_gulf.values(), ignore_index=True)
dataframes_haw2 = pd.concat(dataframes_haw.values(), ignore_index=True)
dataframes_ak2 = pd.concat(dataframes_ak.values(), ignore_index=True)

dfs=[dataframes_east2,dataframes_west2,dataframes_gulf2,dataframes_haw2,dataframes_ak2]
ioos_chl = pd.concat(dfs).reset_index(drop=True) #concatinate them all together 

ioos_chl=ioos_chl[['date', 'lat', 'lon', 'chl', 'depth','source','Dataset ID','Institution','url', 'experiment','t_flag', 'diff_time','d_flag', 'decision']]
ioos_chl.loc[ioos_chl['decision'] != 0, 'decision'] = 1 #because we took the average, as long as the decision != 0, make 1 

ioos_chl['date'] = pd.to_datetime(ioos_chl['date'])
ioos_chl = ioos_chl.loc[ioos_chl['date'] > '2000-01-01'] #only want dates post 2000 for this algorithm 
#remove any negative chl values
ioos_chl=ioos_chl[(ioos_chl['chl']>0)]

#QA/QC, remove upper 95% quartiles of chlorophyll to remove outliers 
Q1 = ioos_chl['chl'].quantile(0.05) 
Q3 = ioos_chl['chl'].quantile(0.95)
IQR = Q3 - Q1
upper_bound = Q3 + 1.5 * IQR
ioos_chl2 = ioos_chl[ioos_chl['chl'] <= upper_bound] #only keep chl data below the upper bound
ioos_chl2['HPLC'] = 1 #there's no definitive way of distinguishing between hplc, so assume no
ioos_chl2['triplicate'] = 1 #since i'm reducing to shallow, 1 day average, triplicate flag = 1 (no triplicate)

#pivers-island-coastal-observa and mlml_monterey have no lat and lon, so go into errdap and populate manually
ioos_chl2.loc[ioos_chl2['Dataset ID'] == 'pivers-island-coastal-observa', ['lat', 'lon']] = [34.7181, -76.6707]
ioos_chl2.loc[ioos_chl2['Dataset ID'] == 'mlml_monterey', ['lat', 'lon']] = [36.60513, -121.88935]


ioos_chl2.to_excel('ioos_chl_qc2.xlsx', index = False)
































