# -*- coding: utf-8 -*-
"""
Created on Mon Mar  2 10:56:27 2026
seabass data from 2025 unpublished as of March, 2026
@author: gianna.milton
"""
import pandas as pd
import geopandas as gpd
from datetime import datetime
import os
import datetime as dt
import SB_support as sb 
from SeaBass_flags2 import sb_flags #looser flags

#step 1.a, turn raw .sb files in 'requested files' into dataframes per affiliation folder in 'requested files'
def get_files(dir): #def to gather name of all .sb files in a folder 
    file_list = []
    for root, _, files in os.walk(dir): #here, dir would be the path to the requested_files
        for file in files:
            if file.endswith(".env"): #pull all files that end with .env
                file_list.append(os.path.join(root, file))
    return file_list

f_list = get_files(r'data\2025_PACE_val_data\ENV_BGC_files') #gather all .env files in f_list1
dfs = []  # list to collect all processed DataFrames
for file in f_list: #for each .env file
    data1 = sb.readSB(filename=file, no_warn=True)  #read it using readSB from the seabass website: https://seabass.gsfc.nasa.gov/wiki/Getting_Started -> Python reader (https://seabass.gsfc.nasa.gov/wiki/readsb_python)
    data2 = data1.data #append the data values
    df = pd.DataFrame.from_dict(data2, orient='index').T #turn data into dataframe with columns as variable names
    
    dt = None  # initialize datetime variable
    #Detect the datetime columns in the dataframe and create single datetime column from pulling datetime elements 
    if all(col in df.columns for col in ['year', 'month', 'day', 'hour', 'minute', 'second']):
        dt = pd.to_datetime(df[['year', 'month', 'day', 'hour', 'minute', 'second']]) #if all 6 time values, create datetime
    elif all(col in df.columns for col in ['year', 'month', 'day', 'hour', 'minute']):
        dt = pd.to_datetime(df[['year', 'month', 'day', 'hour', 'minute']])
    elif all(col in df.columns for col in ['year', 'month', 'day', 'time']):
        df['hour'] = df['time'].astype(str).str[:-6].astype(int) #if just time, seperate into hour, min, sec 
        df['minute'] = df['time'].astype(str).str[-5:-3].astype(int)
        df['second'] = df['time'].astype(str).str[-2:].astype(int)
        dt = pd.to_datetime(df[['year', 'month', 'day', 'hour', 'minute', 'second']])
    elif all(col in df.columns for col in ['date', 'time']):
        df['year'] = df['date'].astype(str).str[:4].astype(int)
        df['month'] = df['date'].astype(str).str[4:6].astype(int)
        df['day'] = df['date'].astype(str).str[6:8].astype(int)
        time_strs = df['time'].astype(str) #some files have time as HH:mm, some as HH:mm:ss, so this accounts for both
        if time_strs.str.contains(":").all() and time_strs.str.count(":").eq(2).all():  #determine format based on string length or presence of ":"
            df['hour'] = time_strs.str.split(":").str[0].astype(int)
            df['minute'] = time_strs.str.split(":").str[1].astype(int)
            df['second'] = time_strs.str.split(":").str[2].astype(float).astype(int)
            dt = pd.to_datetime(df[['year', 'month', 'day', 'hour', 'minute', 'second']])
        elif time_strs.str.contains(":").all() and time_strs.str.count(":").eq(1).all():
            df['hour'] = time_strs.str.split(":").str[0].astype(int)
            df['minute'] = time_strs.str.split(":").str[1].astype(int)
            df['second'] = 0
            dt = pd.to_datetime(df[['year', 'month', 'day', 'hour', 'minute', 'second']])
    else: #if none of the above is deteted, skip for now, we'll create it later
        dt = pd.NaT
    df.insert(0, 'datetime', dt) #insert datetime column into df
    header = pd.DataFrame.from_dict(data1.headers, orient='index').T #create metedata header from dictionary and repeat it to match lenth of dataset
    header_repeated = pd.concat([header] * len(df), ignore_index=True)
    # Combine data and metadata
    combined = pd.concat([df.reset_index(drop=True), header_repeated], axis=1)
    combined = combined.loc[:, ~combined.columns.duplicated()]
    dfs.append(combined)
#final concatenation
sb_2025 = pd.concat(dfs, ignore_index=True) #append all files in that specific affiliation file toether 

chl_columns =['chl','chl_a'] #for reducing rows without these in it (without ,'chl_experiment','chl_stimf')
chl_cols=[col for col in sb_2025.columns if col in chl_columns] #detect the chlorophyll columns present 
sb_2025.dropna(subset=chl_cols, how='all', inplace=True) #if rows in the chl columns empty, remove 

#for any remaining empty datetime, manually create it from the metadata date 
sb_2025['time_flag']='no' #create a flag stating if datetime populated from metadata, initiate as no 
if 'datetime' not in sb_2025.columns: #if the dataframe does not have datetime column, create one
    sb_2025['datetime']=pd.NaT
for idx in sb_2025.index: #loop through each row 
    try:
        if pd.isna(sb_2025.at[idx, 'datetime']) and sb_2025.at[idx, 'start_date'] == sb_2025.at[idx, 'end_date']: 
            #sometimes, start_date and end_date are concerning the start and end of the cruise/project, not that specific data recording. so only enter if loop if start_date = end_date
            #extract strings
            date_str = str(sb_2025.at[idx, 'end_date'])  # e.g. "20240520"
            time_str = str(sb_2025.at[idx, 'end_time'])  # e.g. "14:30:00.000"
            #parse date and time parts
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            hour = int(time_str[:-11])
            minute = int(time_str[-10:-8])
            second = int(float(time_str[-7:-5]))  # Handles "00.000"

            dt = datetime(year, month, day, hour, minute, second)
            sb_2025.at[idx, 'datetime'] = dt #populate that specific datetime row with dt
            sb_2025.at[idx, 'time_flag'] = 'yes' #turn the time_flag to yes
    except Exception as e:
        # If there's a parsing problem, skip gracefully
        print(f"Row {idx} failed — start_date: {date_str}, end_time: {time_str}")
        sb_2025.at[idx, 'time_flag'] = f'error: {e}'

#if lat or lon are empty, populate with the metadata      
sb_2025['coord_flag'] = 'no' #create a flag stating if coordinates populated from metadata, initiate as no 
if 'lat' not in sb_2025.columns: #if lat and lon not in columns, create an empty column
    sb_2025['lat']=pd.NA
    sb_2025['lon']=pd.NA
for idx in sb_2025.index: #for each row
    if pd.isna(sb_2025.at[idx, 'lat']) and sb_2025.at[idx, 'north_latitude'] ==sb_2025.at[idx, 'south_latitude']:
        #sometimes, north_lat and south_lat show the total boundry of the project rather than specific point. so only append if they equal each other
        sb_2025.at[idx, 'lat'] = float(sb_2025.north_latitude[idx][:-5]) #pull latitude value out of north_lat
        sb_2025.at[idx, 'coord_flag'] = 'yes' #turn flag to yes
    if pd.isna(sb_2025.at[idx, 'lon']) and sb_2025.at[idx, 'west_longitude'] ==sb_2025.at[idx, 'east_longitude']:
        sb_2025.at[idx, 'lon'] = float(sb_2025.west_longitude[idx][:-5])
        sb_2025.at[idx, 'coord_flag'] = 'yes'   

sb_2025['HPLC'] = 1 #assume not hplc unless i tell it otherwise
if 'chl_a' in sb_2025.columns:
    sb_2025.loc[sb_2025['chl_a'].notna(), 'HPLC'] = 0 #if chl_a in columns and is not empty, mark as hplc
#NOTE: we don't need to do as much QA/QC regarding the HPLC flag as we did in seabass_chl since data gathered from 2025 is more structed and follow column nameing standards 

sb_2025=sb_2025[['datetime', 'lat', 'lon', 'chl', 'station', 'affiliations', 'investigators',  'experiment', 'cruise', 'data_type',
        'depth',  'time_flag', 'coord_flag',   'chl_a', 'data_file_name','HPLC']]

#subset to study region shapefile 
shp = gpd.read_file(r'C:\Users\gianna.milton\Documents\Python\Shapefiles\combined_coastline.shp')
gdf = gpd.GeoDataFrame(sb_2025, geometry=gpd.points_from_xy(sb_2025.lon, sb_2025.lat), crs="EPSG:4269")
gdf = gdf.to_crs(shp.crs)
sb_2025 = gpd.sjoin(gdf, shp, how="inner", predicate="within")
columns_to_drop = ['geometry', 'index_right', 'merge_id']
sb_2025 = sb_2025.drop(columns=columns_to_drop)
sb_2025= sb_2025.reset_index(drop=True)

#triplicate
counts_series = sb_2025[['depth','datetime','lat','lon']].value_counts() #count how many unique datetime, lat, and lons there are
counts_df = counts_series.reset_index(name='freq_uniq')
sb_2025 = pd.merge(sb_2025, counts_df, on=['depth','datetime','lat','lon'], how='left') #add frequency column to original dataframe
sb_2025['date_hour'] = sb_2025['datetime'].dt.strftime('%Y-%m-%d %H')#some places have 3 different times close to gether but that's bc of recording each time for triplicate (3:00, 3:05, 3:10 )
counts_series = sb_2025[['date_hour','lat','lon','depth']].value_counts() #count how many unique datehour, lat, and lons there are
counts_df = counts_series.reset_index(name='freq_hour')
sb_2025 = pd.merge(sb_2025, counts_df, on=['date_hour','lat','lon','depth'], how='left') #add frequency column to original dataframe

sb_2025['triplicate'] = 1 #assume bad unless otherwise said
sb_2025.loc[sb_2025['freq_uniq'] == 3, 'triplicate'] = 0 #if there was a unique datetime, lat, and lon that happened 3 times, triplicate
sb_2025.loc[(sb_2025['freq_uniq'] == 1) &(sb_2025['freq_hour'] == 3), 'triplicate'] = 0 #if 1 unique datetime recorded and only 3 for datehour, assume triplicate 

#take out depths below 150m for this algorithm 
sb_2025['depth'] = pd.to_numeric(sb_2025['depth'], errors='coerce')
sb_2025 = sb_2025[sb_2025['depth'] <=150].reset_index(drop=True)

#save the same columns for all files
sb_2025=sb_2025[['datetime', 'lat', 'lon', 'chl', 'chl_a','depth','experiment', 'data_type','station', 'affiliations','investigators', 
           'cruise',  'time_flag','coord_flag', 'data_file_name', 'HPLC', 'triplicate']]

#run data_type_flag code on seabass data to append flags
sb_2025 = sb_flags(sb_2025)

sb_2025.to_excel('SB_chl_2025.xlsx', index = False) #sb data with HPLC and Triplicate flags, without any repeats


