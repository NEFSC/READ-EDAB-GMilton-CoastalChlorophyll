# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 09:29:00 2026
HOTS_chl
Load in raw HOTS data from each station and turn into dataframe similar to seabass, with HPLC and triplicate flags
To load data, go to https://hahana.soest.hawaii.edu/hot/hot-dogs/bextraction.html and copy boundries below:
bottle: Jan 01 2000 -Dec 3 2023
            Depth = 0-200m
            variables: CTD salinity
                        CTD Temperature
                        Bottle Salinity
                        Fluorometric chlorophyll a
                        HPLC cholorophyll a
                        station: (hd871881.nc) Kahe point (1): 21 20.6'N, 158 16.4'W
                                 hd117751.nc) Aloha (2) 22 45.0'N, 158 00.0'W
                                 (hd106854.nc) Kaena (6) 21 50.8'N, 158 21.8'W
                                 (hd197174.nc) Hale-Aloha (8) 22 27.5'N, 158 7.9'W
                                 (hd258622.nc) WHOTS1 (ORS) (50) 22 45'N, 157 54.0'W
                                 (hd387759.nc) WHOTS2 22 (52) 22 40.208'N, 157 57.001'W

@author: gianna.milton
"""
import pandas
import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=RuntimeWarning)
from scipy.io import netcdf

#def to convert degree minutes to degrees for lat and lon 
def dm_to_decimal_degrees(degrees, decimal_minutes):
    """Converts degrees and decimal minutes to decimal degrees.
    args:
        degrees: The whole number of degrees.
        decimal_minutes: The fractional part of the degree, in minutes.
    returns: The equivalent decimal degree value.
    """
    decimal_degrees = degrees + (decimal_minutes / 60)
    return decimal_degrees

#def to input all .nc files from folder 
def get_files(dir):
    file_list = []
    for root, _, files in os.walk(dir): #here, dir would be the path to the files
        for file in files:
            if file.endswith(".nc"):
                file_list.append(os.path.join(root, file)) #if file ends in .nc, append to list 
    return file_list

f_list1 =  r'C:\Users\gianna.milton\Documents\Python\Hot dogs\bottle_data' #folder holding ONLY the bottle data downloaded from HOTS 
f_list = get_files(f_list1) #list of all .nc files from folder

for file in f_list:
    print(file)
    dfs=pd.DataFrame() #initiate empty dataframe
    file2read = netcdf.NetCDFFile(file,'r') #read in the netcdf file
    varrs = file2read.variables #variables in netcdf file
    #remove the dataDesc, which is just a description of the data. if not removed, concatination can't occur
    del varrs["dataDesc"]
    for vars in varrs: #for every variable in the file
    #convert the byte to match specific laptop, and appened the variable column (0) into the dataframe
        dfs[vars]=pd.DataFrame(varrs[vars][:].byteswap().newbyteorder(), columns =['0']) 
        
    dfs=dfs[dfs['mdate']!=-9] #take out any negative datetimes i.e unrecorded data 
    dfs=dfs[dfs['mtime']!=-9]
 #datetime is formatted as mmddyy, and hhmmss, but leading 0s are removed so need to pad with 0s until 6 numbers long
    dfs['mtime'] = [f"{int(t):06d}" for t in dfs['mtime']] 
    dfs['mdate'] = [f"{int(t):06d}" for t in dfs['mdate']] 
    
    dfs['month'] = [int(t[:2]) for t in dfs['mdate']]
    dfs['day'] = [int(t[2:4]) for t in dfs['mdate']]
    dfs['year'] = [int(t[4:])+2000 for t in dfs['mdate']]
    dfs['hour'] = [int(t[:2]) for t in dfs['mtime']]
    dfs['minute'] = [int(t[2:4]) for t in dfs['mtime']]
    dfs['second'] = [int(t[4:]) for t in dfs['mtime']]
    dfs['datetime']= pd.to_datetime(dfs[['year', 'month', 'day', 'hour', 'minute', 'second']]) #datetime variable
    #drop unneeded temporal columns now that datetime is created
    columns_to_drop = ['mtime','mdate','month','day','year','hour','minute','second']
    dfs = dfs.drop(columns=columns_to_drop)
    dfs = dfs.reset_index(drop=True)
    
    #seperate data from each station into it's own dataframe, where the name of the dataframe equals the station name
    #lat and lon are not included in the file, so manually add them
    #finally, roughly convert pressure to depth (Depth(m)=Pressure(db) *1.019716)
    if dfs.stn[0]==1: #station 1 = station Kahe
        kahe=dfs.copy()
        kahe['lat']=dm_to_decimal_degrees(21, 20.6)
        kahe['lon']=dm_to_decimal_degrees(158, 16.4)*-1
        kahe=kahe[kahe['chl']!=-9] #remove -9 i.e. bad chl values
        kahe['station']='kahe'
        kahe['depth'] = kahe['press'] * 1.02
        kahe=kahe[['crn', 'depth', 'chl','hplc', 'datetime', 'lat', 'lon', 'station']]
        
    elif dfs.stn[0]==2: #station 2 = station Aloha
        aloha=dfs.copy()
        aloha['lat']=dm_to_decimal_degrees(22, 45.0)
        aloha['lon']=dm_to_decimal_degrees(158, 00.0)*-1
        #don't remove -9 from chl for aloha station because some bad chl entries still have hplc values. 
        aloha['station']='aloha'
        aloha['depth'] = aloha['press'] * 1.02
        aloha=aloha[['crn', 'depth', 'chl','hplc', 'datetime', 'lat', 'lon', 'station']]

    elif dfs.stn[0]==6: #station 6 = station kaena
        kaena=dfs.copy()
        kaena['lat']=dm_to_decimal_degrees(21, 50.8)
        kaena['lon']=dm_to_decimal_degrees(158, 7.9)*-1
        kaena=kaena[kaena['chl']!=-9] #remove -9 i.e. bad chl values
        kaena['station']='kaena'
        kaena['depth'] = kaena['press'] * 1.02
        kaena=kaena[['crn', 'depth', 'chl','hplc', 'datetime', 'lat', 'lon', 'station']]

    elif dfs.stn[0]==8: #station 8 = station Hale
        hale=dfs.copy()
        hale['lat']=dm_to_decimal_degrees(22, 27.5)
        hale['lon']=dm_to_decimal_degrees(158, 21.8)*-1
        hale=hale[hale['chl']!=-9] #remove -9 i.e. bad chl values
        hale['station']='hale'
        hale['depth'] = hale['press'] * 1.02
        hale=hale[['crn', 'depth', 'chl','hplc', 'datetime', 'lat', 'lon', 'station']]

    elif dfs.stn[0]==50: #station 50 = station Ors
        ors=dfs.copy()
        ors['lat']=dm_to_decimal_degrees(22, 45)
        ors['lon']=dm_to_decimal_degrees(157, 54.0)*-1
        ors=ors[ors['chl']!=-9] #remove -9 i.e. bad chl values
        ors['station']='ors'
        ors['depth'] = ors['press'] * 1.02
        ors=ors[['crn', 'depth', 'chl','hplc', 'datetime', 'lat', 'lon', 'station']]

    elif dfs.stn[0]==52: #station 52 = station Whots
        whots=dfs.copy()
        whots['lat']=dm_to_decimal_degrees(22, 40.208)
        whots['lon']=dm_to_decimal_degrees(157, 57.001)*-1
        whots=whots[whots['chl']!=-9] #remove -9 i.e. bad chl values
        whots['station']='whots'
        whots['depth'] = whots['press'] * 1.02
        whots=whots[['crn', 'depth', 'chl','hplc', 'datetime', 'lat', 'lon', 'station']]

    else:
        print(file) #if noe of the above, print the file to inspect
    file2read.close()  #close file

#primary production, only recorded at station aloha.
#repeat above procedure
ppro=pd.DataFrame()
file2read = netcdf.NetCDFFile(r'C:\Users\gianna.milton\Documents\Python\Hot dogs\hd192096.nc','r')
varrs = file2read.variables #variables
del varrs["dataDesc"]
for vars in varrs:
    ppro[vars]=pd.DataFrame(varrs[vars][:].byteswap().newbyteorder(), columns =['0'])
ppro['stime'] = [f"{int(t):04d}" for t in ppro['stime']] #start time
ppro['etime'] = [f"{int(t):04d}" for t in ppro['etime']] #end time  
ppro['date'] = [f"{int(t):06d}" for t in ppro['date']]  #date

#arbitrarily deciding to use etime (end time) for datetime column
ppro['month'] = [int(t[2:4]) for t in ppro['date']]
ppro['day'] = [int(t[4:]) for t in ppro['date']]
ppro['year'] = [int(t[:2])+2000 for t in ppro['date']]
ppro['hour'] = [int(t[:2]) for t in ppro['etime']]
ppro['minute'] = [int(t[2:4]) for t in ppro['etime']]
ppro['datetime']= pd.to_datetime(ppro[['year', 'month', 'day', 'hour', 'minute']])
ppro=ppro[['crn', 'type', 'depth', 'chl', 'bsal','datetime']].reset_index(drop=True)  
ppro['station']='primary_prod'
ppro['hplc']=-9 #initiate empty hplc column so that when concatinated with stations it matches with other columns
#lat and lon to match station aloha 
ppro['lat']=dm_to_decimal_degrees(22, 45.0)
ppro['lon']=dm_to_decimal_degrees(158, 00.0)*-1

hots = pd.concat([kahe, aloha, kaena,hale,ors,whots,ppro]).reset_index(drop=True)

#HPLC flag: if column hplc = -9, flag as 1 (bad), if there is a value, value, then convert to mg/L and flag as hplc=0
hots['HPLC'] = 1 #assume no HPLC
hots=hots.rename(columns={'hplc':'chl_a'})
hots.loc[hots['chl_a'] != -9, 'HPLC'] = 0 #if hplc column does not equal -9 change to 0
#Based on this linke, https://www.bco-dmo.org/dataset/3773, hplc is in nanograms/L, so need to convert
hots.loc[hots['chl_a'] != -9, 'chl_a'] =hots['chl_a']*0.001

#triplicates
counts_series = hots[['depth','datetime','lat','lon']].value_counts() #count how many unique cast,depth, datetime, lat, and lons there are
counts_df = counts_series.reset_index(name='freq_uniq')
hots = pd.merge(hots, counts_df, on=['depth','datetime','lat','lon'], how='left') #add frequency column to original dataframe4

#sometimes, triplicate specific times are recorded (ex: 3:00, 3:05, 3:10 ), so also check for unique datehour entries
hots['date_hour'] = hots['datetime'].dt.strftime('%Y-%m-%d %H')
counts_series = hots[['depth','date_hour','lat','lon']].value_counts() #count how many unique datehour, lat, and lons there are
counts_df = counts_series.reset_index(name='freq_hour')
hots = pd.merge(hots, counts_df, on=['depth','date_hour','lat','lon'], how='left') #add frequency column to original dataframe
hots['triplicate'] = 1 #assume bad unless otherwise said
hots.loc[hots['freq_uniq'] == 3, 'triplicate'] = 0 #if there was a unique datetime, lat, and lon that happened 3 times, triplicate
hots.loc[(hots['freq_uniq'] == 1) &(hots['freq_hour'] == 3), 'triplicate'] = 0 #if 1 unique datetime but 3 unique date hours, assume triplicate
hots=hots.loc[hots['depth']<=150].reset_index(drop=True) #reduce to upper 150 meteres for algorithm development

hots=hots[['datetime', 'lat', 'lon','depth', 'chl', 'chl_a', 'station', 'HPLC', 'triplicate']]
hots['experiment']='HOTS'
hots['source']='HOTS'
hots['investigators']= 'Angelicque E. White'
hots['affiliations']="University of Hawai'i at Mānoa"
hots['url']='https://hahana.soest.hawaii.edu/hot/hot-dogs/interface.html'
hots.replace(-9, np.nan, inplace=True)
hots = hots.dropna(subset=['chl', 'chl_a'], how='all')

hots.to_excel('hots_chl_qc.xlsx', index = False)




    
    