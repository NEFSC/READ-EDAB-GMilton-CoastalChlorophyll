# -*- coding: utf-8 -*-
"""
Created on Wed Jan 14 09:33:40 2026
QA/QC for all AOP data

NOTE: data gathered with these entries on the seabass website:
    Description: Import AOP data from seabass
    boudries for east coast: 47.11N - 23.87S  -83.67W - -69.26E
    boundries for westcoast 53N 19S, -131W -111E
    boundries for gulf of mexico: 31N - 18S  -100W - -79.5E 
    boundries for Hawaii: -180W -150E, 25N 0S
    boundries for Alaska: -180W -136, 87N 42S
@author: gianna.milton
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cartopy
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import geopandas as gpd
from datetime import datetime
import os
import datetime as dt
import SB_support as sb 
import warnings
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=RuntimeWarning)

'''
Since seabass organizes their raw data in a unique way, this data concatination section is also unique.
1. raw sb. files to raw dataframes
    a. the variable 'path_to_folder' needs to be manually changed for each 'requested files' you have.
    b. once 'dfs_to_concat' is run, you need to save that as a unique id before running the next 'requested files'. in this case I saved them as the number of regional data folders i have (3 folders for east coast for example)
    c. once all 'requested files' are run and saved as unique entries, concat them all together and save as csv to be inported in step 2. 
2. raw dataframes to qz/qc'd dataframe with triplicate flags
'''
def standardize_rrs_data(df):
    """
    Transforms a mixed-format oceanographic dataframe into a consistent long format.
    turn columns in format rrs### into the wavelength column and rrs column
    """
    # metadata columns that stay the same for every row
    id_vars = ['datetime', 'lon', 'lat', 'identifier_product_doi', 'affiliations', 'investigators', 'contact', 'experiment', 'cruise',
            'data_type',  'water_depth', 'measurement_depth', 'station', 'time_flag','depth','coord_flag',] #'depth',
    # identify the 'wide' columns (the rrs### columns), exclude the generic 'rrs' column itself from this list
    wide_cols = [col for col in df.columns if col.startswith('rrs') and col != 'rrs']
    #select rows/cols that are already in the target format (rrs + wavelength)
    df_long_existing = df[id_vars + ['rrs', 'wavelength']].copy()
    #filter out rows where 'rrs' is NaN (assuming these rows hold the wide data)
    df_long_existing = df_long_existing.dropna(subset=['rrs'])
    #select the identifiers plus the wide columns
    df_wide_subset = df[id_vars + wide_cols].copy() #all the rrs### columns
    # "Melt" the data: unpivot the wide columns into rows
    df_melted = df_wide_subset.melt(id_vars=id_vars, value_vars=wide_cols, var_name='raw_wavelength', value_name='rrs')
    df_melted = df_melted.dropna(subset=['rrs'])
    #clean the wavelength column: 'rrs340' -> 340 by emove the 'rrs' string and convert the remainder to an integer (or float)
    df_melted['raw_wavelength'] = df_melted['raw_wavelength'].str.replace('rrs', '')
    df_melted['wavelength'] = pd.to_numeric(df_melted['raw_wavelength'])
    df_melted = df_melted.drop(columns=['raw_wavelength'])
    #concatenate the originally long data with the newly melted data
    final_df = pd.concat([df_long_existing, df_melted], ignore_index=True)
    return final_df

#step 1.a, turn raw .sb files in 'requested files' into dataframes per affiliation folder in 'requested files'
def get_files(dir): #def to gather name of all .sb files in a folder 
    file_list = []
    for root, _, files in os.walk(dir): #here, dir would be the path to the requested_files
        for file in files:
            if file.endswith(".sb"):
                file_list.append(os.path.join(root, file))
    return file_list

def get_folder_names(folder_path): 
  """
  Returns a list of folder names in the given directory.
  """
  folder_names = []
  for item in os.listdir(folder_path):
    item_path = os.path.join(folder_path, item)
    if os.path.isdir(item_path):
      folder_names.append(item)
  return folder_names
#there can be thousands of columns to append in some of these .sb files. so create a selected_columns variable that will only append the needed columns to include 
selected_columns =['lat','lon','year','month','day','hour','minute','second','time','date','datetime','depth','station','wavelength']
contain='rrs'

#alaska1, east 1,2,3,4,5,6,7,8, gulf, haw, west1
path_to_folder = r'C:\Users\gianna.milton\Documents\Python\SeaBass\data\SB_reflectance\west coast\requested_files_2\requested_files' #NOTE: there are usually multiple requested_files, this is where you would manually loop thru them
all_folders = get_folder_names(path_to_folder)

for folders in range(len(all_folders)): #for each affiliation folder in all_folders
    f_list1 =   path_to_folder +'\\'+str(all_folders[folders]) #create path to that specific folder 
    f_list = get_files(f_list1) #gather all .sb files in f_list1
    print(str(all_folders[folders]))
    dfs = []  # list to collect all processed DataFrames
    for file in f_list: #for each .sb file
        data1 = sb.readSB(filename=file, no_warn=True) #read it using readSB from the seabass website
        data2 = data1.data #append the data 
        df = pd.DataFrame.from_dict(data2, orient='index').T #turn data into dataframe
        dt = None  # initialize datetime variable
        #Detect the datetime columns in the dataframe and create single datetime column 
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
        list_columns=list(df.columns[df.columns.str.contains(contain)]) #gather all columns that have rrs in them (rrs and any rrs500, ect)
        list_columns = [item for item in list_columns if '_' not in item] #take out columns names with _ in them i.e _unc
        list_columns = [item for item in list_columns if '.' not in item] #take out columns names with . in them i.e only 1nm bins
        list_columns = [item for item in list_columns if ')' not in item]
        
        if list_columns: #if the dataframe has rrs in them 
            all_columns = selected_columns+list_columns
            columns_to_keep = [col for col in df.columns if col in all_columns or col == 'datetime']
            df_filtered = df[columns_to_keep]
            header = pd.DataFrame.from_dict(data1.headers, orient='index').T #create header from dictionary and repeat it to match dataset
            header_repeated = pd.concat([header] * len(df_filtered), ignore_index=True)
            # Combine data and metadata
            combined = pd.concat([df_filtered.reset_index(drop=True), header_repeated], axis=1)
            combined = combined.loc[:, ~combined.columns.duplicated()]
            dfs.append(combined)
            
        #else:#if no rrs, (if there are only the other aop's there, not rrs) then skip 
    if not dfs: #if dfs empty, 
        globals()[str(all_folders[folders])] = pd.DataFrame()
    else:
        globals()[str(all_folders[folders])] = pd.concat(dfs, ignore_index=True)
 
for names in all_folders:
    (globals()[names])['time_flag']='no' #create a flag stating if datetime populated from metadata, initiate as no 
    if 'datetime' not in (globals()[names]).columns: #if the dataframe does not have datetime column, create one
        (globals()[names])['datetime']=pd.NaT
    for idx in (globals()[names]).index: #loop through each row 
        try:
            if pd.isna((globals()[names]).at[idx, 'datetime']) and (globals()[names]).at[idx, 'start_date'] == (globals()[names]).at[idx, 'end_date']: 
                #sometimes, start_date and end_date are concerning the start and end of the cruise/project, not that specific data recording. so only enter if loop if start_date = end_date
                #extract strings
                date_str = str((globals()[names]).at[idx, 'end_date'])  # e.g. "20240520"
                time_str = str((globals()[names]).at[idx, 'end_time'])  # e.g. "14:30:00.000"
                #parse date and time parts
                year = int(date_str[:4])
                month = int(date_str[4:6])
                day = int(date_str[6:8])
                hour = int(time_str[:-11])
                minute = int(time_str[-10:-8])
                second = int(float(time_str[-7:-5]))  # Handles "00.000"

                dt = datetime(year, month, day, hour, minute, second)
                (globals()[names]).at[idx, 'datetime'] = dt #populate that specific datetime row with dt
                (globals()[names]).at[idx, 'time_flag'] = 'yes' #turn the time_flag to yes
        except Exception as e:
            print(f"Row {idx} failed — start_date: {date_str}, end_time: {time_str}")
            (globals()[names]).at[idx, 'time_flag'] = f'error: {e}'

#if lat or lon are empty, populate with the metadata      
for names in all_folders:
    (globals()[names])['coord_flag'] = 'no' #create a flag stating if coordinates populated from metadata, initiate as no 
    if 'lat' not in (globals()[names]).columns: #if lat and lon not in columns, create an empty column
        (globals()[names])['lat']=pd.NA
        (globals()[names])['lon']=pd.NA
    for idx in (globals()[names]).index: #for each row
        if pd.isna((globals()[names]).at[idx, 'lat']) and (globals()[names]).at[idx, 'north_latitude'] ==(globals()[names]).at[idx, 'south_latitude']:
            #sometimes, north_lat and south_lat show the total boundry of the project rather than specific point. so only append if they equal each other
            (globals()[names]).at[idx, 'lat'] = float((globals()[names]).north_latitude[idx][:-5]) #pull latitude value out of north_lat
            (globals()[names]).at[idx, 'coord_flag'] = 'yes' #turn flag to yes
        if pd.isna((globals()[names]).at[idx, 'lon']) and (globals()[names]).at[idx, 'west_longitude'] ==(globals()[names]).at[idx, 'east_longitude']:
            (globals()[names]).at[idx, 'lon'] = float((globals()[names]).west_longitude[idx][:-5])
            (globals()[names]).at[idx, 'coord_flag'] = 'yes'   

dfs_to_concat = [(globals()[names]) for names in all_folders] #concatinate the dataframes in all_folders

#east coast
east1 = pd.concat(dfs_to_concat, ignore_index=True) #save dfs_to_concat to single dataframe. STOP HERE and repeat if you have multiple requested files
east2 = pd.concat(dfs_to_concat, ignore_index=True)
east3 = pd.concat(dfs_to_concat, ignore_index=True)
east4 = pd.concat(dfs_to_concat, ignore_index=True)
east5 = pd.concat(dfs_to_concat, ignore_index=True)
east6 = pd.concat(dfs_to_concat, ignore_index=True)
east7 = pd.concat(dfs_to_concat, ignore_index=True)
east8 = pd.concat(dfs_to_concat, ignore_index=True)
east_coast = pd.concat([east1,east2,east3,east4,east5,east6,east7,east8])
list_columns=list(east_coast.columns[east_coast.columns.str.contains('rrs')]) #gather all columns that have rrs in them (rrs and any rrs500, ect)
east_coast=east_coast[['datetime', 'lon', 'lat', 'identifier_product_doi', 'affiliations', 'investigators', 'contact', 'experiment', 'cruise',
        'data_type',  'water_depth', 'measurement_depth', 'station', 'time_flag', 'coord_flag', 'wavelength']+list_columns]
east_coast = standardize_rrs_data(east_coast)
east_coast['lat'] = pd.to_numeric(east_coast['lat'], errors='coerce')
east_coast['lon'] = pd.to_numeric(east_coast['lon'], errors='coerce')

#alaska
alaska= pd.concat(dfs_to_concat, ignore_index=True) #20443 x 61
list_columns=list(alaska.columns[alaska.columns.str.contains('rrs')]) #gather all columns that have rrs in them (rrs and any rrs500, ect)
alaska=alaska[['datetime', 'lon', 'lat', 'identifier_product_doi', 'affiliations', 'investigators', 'contact', 'experiment', 'cruise',
        'data_type',  'water_depth', 'measurement_depth', 'station','depth', 'time_flag', 'coord_flag', 'wavelength']+list_columns]
alaska = standardize_rrs_data(alaska)

#gom
gom= pd.concat(dfs_to_concat, ignore_index=True)
list_columns=list(gom.columns[gom.columns.str.contains('rrs')]) #gather all columns that have rrs in them (rrs and any rrs500, ect)
gom=gom[['datetime', 'lon', 'lat', 'identifier_product_doi', 'affiliations', 'investigators', 'contact', 'experiment', 'cruise',
        'data_type',  'water_depth', 'measurement_depth', 'station', 'time_flag', 'coord_flag', 'wavelength']+list_columns]
gom = standardize_rrs_data(gom)

#haw
haw= pd.concat(dfs_to_concat, ignore_index=True)
list_columns=list(haw.columns[haw.columns.str.contains('rrs')]) #gather all columns that have rrs in them (rrs and any rrs500, ect)
haw=haw[['datetime', 'lon', 'lat', 'identifier_product_doi', 'affiliations', 'investigators', 'contact', 'experiment', 'cruise',
        'data_type',  'water_depth', 'measurement_depth', 'station', 'time_flag', 'coord_flag', 'depth','wavelength']+list_columns]
haw = standardize_rrs_data(haw)
haw['lat'] = pd.to_numeric(haw['lat'], errors='coerce')
haw['lon'] = pd.to_numeric(haw['lon'], errors='coerce')

#west coast
west1 = pd.concat(dfs_to_concat, ignore_index=True)
west2 = pd.concat(dfs_to_concat, ignore_index=True)
west_coast = pd.concat([west1,west2])
list_columns=list(west_coast.columns[west_coast.columns.str.contains('rrs')]) #gather all columns that have rrs in them (rrs and any rrs500, ect)
west_coast=west_coast[['datetime', 'lon', 'lat', 'identifier_product_doi', 'affiliations', 'investigators', 'contact', 'experiment', 'cruise',
        'data_type',  'water_depth', 'measurement_depth', 'station', 'time_flag', 'coord_flag', 'depth','wavelength']+list_columns]
west_coast = standardize_rrs_data(west_coast)


shp = gpd.read_file(r'C:\Users\gianna.milton\Documents\Python\Shapefiles\combined_coastline.shp')
gdf = gpd.GeoDataFrame(west_coast, geometry=gpd.points_from_xy(west_coast.lon, west_coast.lat), crs="EPSG:4269")
gdf = gdf.to_crs(shp.crs)
west_coast = gpd.sjoin(gdf, shp, how="inner", predicate="within")
columns_to_drop = ['geometry', 'index_right', 'merge_id']
west_coast = west_coast.drop(columns=columns_to_drop)
west_coast= west_coast.reset_index(drop=True)

fig=plt.figure(figsize=(12, 12))
axs1=fig.add_subplot(1,1,1,projection= cartopy.crs.PlateCarree())
axs1.add_feature(cfeature.LAND)
axs1.add_feature(cfeature.OCEAN)
axs1.add_feature(cfeature.BORDERS)
im=axs1.scatter(west_coast.lon,west_coast.lat,s=10)
gl=axs1.gridlines(linewidth=0.2,color='grey',alpha=0.5,linestyle='-',
                draw_labels=True, x_inline= False,y_inline=False)
gl.xformatter=LONGITUDE_FORMATTER
gl.yformatter=LATITUDE_FORMATTER
gl.top_labels = False    # Disable top labels
gl.right_labels = False  # Disable right labels

#east coast
east_coast.to_excel('raw_east_SB_rrs.xlsx', index = False)
  #all files from seabass products with chl, only qa is lat,lon, and datetime creation, shapefile, and column limiting

#alaska
alaska.to_excel('raw_alaska_SB_rrs.xlsx', index = False)

gom.to_excel('raw_gom_SB_rr.xlsx', index = False)

#below is actually hawaii fyi
haw.to_excel('raw_haw_SB_rrs.xlsx', index = False)

#westcoast
west_coast.to_excel('raw_west_SB_rrs.xlsx', index = False)




#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#step 2. now that all the raw sb files are concatinated and seperated, load them all in and create single dataframe
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#when it's time to concat, remove all nanometer wavelengths i.e. anything with 350.1, 350.2, ect 
#also take out repeats
#figure out best way to just have single depth value
#take out any days before 2000

east = pd.read_excel('raw_east_SB_rrs.xlsx') 
west = pd.read_excel('raw_west_SB_rrs.xlsx') 
gulf = pd.read_excel('raw_gom_SB_rr.xlsx') 
haw = pd.read_excel('raw_haw_SB_rrs.xlsx') 
alas = pd.read_excel('raw_alaska_SB_rrs.xlsx') 

rrs_all = pd.concat([east,west,gulf,haw,alas])
 
#first, want to take out if the wavelength is a decimal (i.e only want integers )
dec_mask = pd.to_numeric(rrs_all['wavelength'], errors='coerce').fillna(0) % 1 == 0 #only keep whole numbers
rrs_all = rrs_all[dec_mask]

rrs_all['datetime'] = pd.to_datetime(rrs_all['datetime']) #ensure datetime is in correct format
rrs_all = rrs_all[rrs_all['datetime'] >= '2000-01-01'] #only want data from 2000 on for this algorithm

test=rrs_all[rrs_all["depth"].isnull()]













#first, load in raw xlsx files one at a time and conduct qa/qc. repeat the steps below until all raw files are saved 
df = pd.read_excel('raw_west_SB.xlsx') 
 

#if depth is na and the data_type is flow_thru or mooring, replace depth with measurment depth or water_depth from metadata
df['depth'] = np.where((df['depth'].isna()) & (df['data_type']=='flow_thru'), df['measurement_depth'], df['depth'])
df['depth'] = np.where((df['depth'].isna()) & (df['data_type']=='mooring'), df['water_depth'], df['depth'])

#FLAG for triplicates 
counts_series = df[['datetime','lat','lon']].value_counts() #count how many unique datetime, lat, and lons there are
counts_df = counts_series.reset_index(name='freq_uniq')
df = pd.merge(df, counts_df, on=['datetime','lat','lon'], how='left') #add frequency column to original dataframe
df['date_hour'] = df['datetime'].dt.strftime('%Y-%m-%d %H')#some places have 3 different times close to gether but that's bc of recording each time for triplicate (3:00, 3:05, 3:10 )
counts_series = df[['date_hour','lat','lon']].value_counts() #count how many unique datehour, lat, and lons there are
counts_df = counts_series.reset_index(name='freq_hour')
df = pd.merge(df, counts_df, on=['date_hour','lat','lon'], how='left') #add frequency column to original dataframe

df['triplicate'] = 1 #assume bad unless otherwise said
df.loc[df['freq_uniq'] == 3, 'triplicate'] = 0 #if there was a unique datetime, lat, and lon that happened 3 times, triplicate
df.loc[(df['freq_uniq'] == 1) &(df['freq_hour'] == 3), 'triplicate'] = 0 #if 1 unique datetime recorded and only 3 for datehour, assume triplicate 

#take out depths below 150m for this algorithm 
df['depth'] = pd.to_numeric(df['depth'], errors='coerce')
df = df[df['depth'] <=150].reset_index(drop=True)

#save the same columns for all files
df=df[['datetime', 'lat', 'lon', 'chl', 'chl_a','depth','experiment', 'data_type','station', 'affiliations','investigators', 'contact',
           'cruise', 'identifier_product_doi', 'time_flag','coord_flag', 'data_file_name', 'HPLC', 'triplicate']]

#save the df, then repeat for however many raw xlsx files you have 
east = df.copy()
alas = df.copy()
gom = df.copy()
hawaii=df.copy()
west = df.copy()

#once all datasets loaded in, need to take out any repeats. put all dataframes into single dataframe and take out dubplicates 
all_data = pd.concat([alas,east, gom,hawaii,west], axis=0) 
all_data = all_data.drop_duplicates()#265715->253719

#add data type flag
#For this dataset, we want to avoid in vivo chl as much as possible. Since sometimes seabass data is mislabled or miscategorized, run the dataset thru a flagging system that helps detect if the chl is from fluorescence  
#all_data = pd.read_excel('SB_chl_na.xlsx')
#for these flags, 1 is bad, 0 is good, 2 is indeterminate 
all_data1 = sb_flags(all_data)
all_data1.to_excel('SB_chl_na.xlsx', index = False) #sb data with HPLC and Triplicate flags, without any repeats



