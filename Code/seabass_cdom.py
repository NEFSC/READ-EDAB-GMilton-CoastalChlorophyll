# -*- coding: utf-8 -*-
"""
Created on Wed Dec 17 14:53:43 2025
CDOM products from SEABASS

all products related to suspended matter in water from SeaBASS
Data was gathered from the seabass website following the subsetL
    dates: 2000-01-01 -> 2025-12-17
    lat: 74-17, lon: -171 - -52, 
    products: a, DC, PC, SPM
@author: gianna.milton
"""
import pandas as pd
import geopandas as gpd
from datetime import datetime
import os
import datetime as dt
import SB_support as sb 

def get_files(dir):
    file_list = []
    for root, _, files in os.walk(dir): #here, dir would be the path to the requested_files
        for file in files:
            if file.endswith(".sb"): #gather all files that end with .sb
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

#only retain cdom and metadata columns relevant 
selected_columns =['lat','lon','year','month','day','hour','minute','second','time','date','datetime' ,'ag', 'abs_ag', 'cdomf', 'cdmf', 'cdmf_rfu',
                   'pim', 'pic', 'spm', 'pom', 'turbidity', 'cdom','depth','station','wavelength'] #detect any column related to cdom

path_to_folder = r'CDOM\SB_products_all2\requested_files_5\requested_files'
all_folders = get_folder_names(path_to_folder) #gather all folders in the path_to_folder 

for folders in range(len(all_folders)):
    f_list1 =  path_to_folder +'\\'+str(all_folders[folders]) #create file structure pathe
    f_list = get_files(f_list1) #gather all .sb files
    print(str(all_folders[folders]))
    dfs = []  # list to collect all processed DataFrames
    #for all the files in f_list
    for file in f_list:
        data1 = sb.readSB(filename=file, no_warn=True) #run readSB file to read in files
        data2 = data1.data #pull environmental data 
        df = pd.DataFrame.from_dict(data2, orient='index').T #turn data into dataframe with column as name
        
        dt = None  # initialize datetime variable
        # Generate datetime column if possible by pulling datetime elements depending on how file structure is
        if all(col in df.columns for col in ['year', 'month', 'day', 'hour', 'minute', 'second']):
            dt = pd.to_datetime(df[['year', 'month', 'day', 'hour', 'minute', 'second']])
        elif all(col in df.columns for col in ['year', 'month', 'day', 'hour', 'minute']):
            dt = pd.to_datetime(df[['year', 'month', 'day', 'hour', 'minute']])
        elif all(col in df.columns for col in ['year', 'month', 'day', 'time']):
            df['hour'] = df['time'].astype(str).str[:-6].astype(int)
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
        else:
            dt = pd.NaT #if the above can't detect datetime, then for now do not make datetime. we'll appended it from metadata later
        df.insert(0, 'datetime', dt) #insert datetime column into df
        columns_to_keep = [col for col in df.columns if col in selected_columns or col == 'datetime'] #only keep whatever columns are in selected_columns
        df_filtered = df[columns_to_keep]
        header = pd.DataFrame.from_dict(data1.headers, orient='index').T #create metedata header from dictionary and repeat it to match lenth of dataset
        header_repeated = pd.concat([header] * len(df_filtered), ignore_index=True) #ensure each measurment has it's metadata 
        # Combine data and metadata
        combined = pd.concat([df_filtered.reset_index(drop=True), header_repeated], axis=1)
        combined = combined.loc[:, ~combined.columns.duplicated()]
        dfs.append(combined)
    #final concatenation
    globals()[str(all_folders[folders])] = pd.concat(dfs, ignore_index=True)
    
#remove any rows that do not have the cdom relevant samples recorded
cdom_columns =['ag', 'abs_ag', 'cdomf', 'cdmf', 'cdmf_rfu','pim', 'pic', 'spm', 'pom', 'turbidity', 'cdom',] #for reducing rows without these in it 
for names in all_folders: #for each affilitation dataframe
    cdom_cols=[col for col in (globals()[names]).columns if col in cdom_columns] #detect the chlorophyll columns present 
    (globals()[names]).dropna(subset=cdom_cols, how='all', inplace=True) #if rows in the chl columns empty, remove 

#if a sample does not have datetime, see if it can be added from metadata
for names in all_folders:
    print(names)
    (globals()[names])['time_flag']='no' #add a flag to dictate if the sample's datetime was appended from metadata
    if 'datetime' not in (globals()[names]).columns:
        (globals()[names])['datetime']=pd.NaT #if datetime not in column, add an empty datetime column
    for idx in (globals()[names]).index:
        try:
            if pd.isna((globals()[names]).at[idx, 'datetime']) and (globals()[names]).at[idx, 'start_date'] == (globals()[names]).at[idx, 'end_date']:#first, make sure the start_date and end_date equal 
                #sometimes, start_date and end_date are concerning the start and end of the cruise/project, not that specific data recording. so only enter if loop if start_date = end_date
                # Extract strings
                date_str = str((globals()[names]).at[idx, 'end_date'])  # e.g. "20240520"
                time_str = str((globals()[names]).at[idx, 'end_time'])  # e.g. "14:30:00.000"
                # Parse date and time parts
                year = int(date_str[:4])
                month = int(date_str[4:6])
                day = int(date_str[6:8])
                hour = int(time_str[:-11])
                minute = int(time_str[-10:-8])
                second = int(float(time_str[-7:-5]))  # Handles "00.000"

                dt = datetime(year, month, day, hour, minute, second)
                (globals()[names]).at[idx, 'datetime'] = dt
                (globals()[names]).at[idx, 'time_flag'] = 'yes'
        except Exception as e:
            # If there's a parsing problem, skip gracefully
            print(f"Row {idx} failed — start_date: {date_str}, end_time: {time_str}")
            (globals()[names]).at[idx, 'time_flag'] = f'error: {e}'

#populate empty lat lon with lat lon from dataframe          
for names in all_folders:
    (globals()[names])['coord_flag'] = 'no'    #print(str(a))
    if 'lat' not in (globals()[names]).columns:
        (globals()[names])['lat']=pd.NA
        (globals()[names])['lon']=pd.NA
    for idx in (globals()[names]).index:
        if pd.isna((globals()[names]).at[idx, 'lat']) and (globals()[names]).at[idx, 'north_latitude'] ==(globals()[names]).at[idx, 'south_latitude']:#first, make sure north and south latitude equal
            #sometimes, north_lat and south_lat show the total boundry of the project rather than specific point. so only append if they equal each other
            (globals()[names]).at[idx, 'lat'] = float((globals()[names]).north_latitude[idx][:-5])
            (globals()[names]).at[idx, 'coord_flag'] = 'yes'
        if pd.isna((globals()[names]).at[idx, 'lon']) and (globals()[names]).at[idx, 'west_longitude'] ==(globals()[names]).at[idx, 'east_longitude']:
            (globals()[names]).at[idx, 'lon'] = float((globals()[names]).west_longitude[idx][:-5])
            (globals()[names]).at[idx, 'coord_flag'] = 'yes'   


dfs_to_concat = [(globals()[names]) for names in all_folders] #concatinate all the dataframes in all_folders into single dataframe

#next, save dfs_to_concat as unique variable and then move back to line 43, change the folder path, and repeat for all folders. Below are steps to take once all folders are loaded in. 
cdom1 = pd.concat(dfs_to_concat, ignore_index=True) #save dfs_to_concat to single dataframe. STOP HERE and repeat if you have multiple requested files
cdom2 = pd.concat(dfs_to_concat, ignore_index=True)
cdom3 = pd.concat(dfs_to_concat, ignore_index=True)
cdom4 = pd.concat(dfs_to_concat, ignore_index=True)
cdom5 = pd.concat(dfs_to_concat, ignore_index=True)
#concat into single dataframe
cdom_all= pd.concat([cdom1,cdom2,cdom3,cdom4,cdom5])
#ensure coordinates are values
cdom_all['lat'] = pd.to_numeric(cdom_all['lat'], errors='coerce')
cdom_all['lon'] = pd.to_numeric(cdom_all['lon'], errors='coerce')

#only retain relevant columns
cdom_sb = cdom_all[['datetime', 'lon', 'lat', 'identifier_product_doi', 'affiliations', 'investigators', 'contact', 'experiment', 'cruise',
                     'data_type',  'station','depth', 'time_flag', 'coord_flag','pim', 'pic', 'spm', 'pom', 'cdom']]    
cdom_sb = cdom_sb.dropna(subset=['cdom','spm','pim', 'pom',], how='all') #if row does not have these sample values, remove
cdom_sb = cdom_sb.dropna(subset=['lat'], how='all')
cdom_sb = cdom_sb.dropna(subset=['datetime'], how='all').reset_index(drop=True)

#subset to shapefile stufy region
shp = gpd.read_file(r'C:\Users\gianna.milton\Documents\Python\Shapefiles\combined_coastline.shp')
gdf = gpd.GeoDataFrame(cdom_sb, geometry=gpd.points_from_xy(cdom_sb.lon, cdom_sb.lat), crs="EPSG:4269")
gdf = gdf.to_crs(shp.crs)
cdom_sb = gpd.sjoin(gdf, shp, how="inner", predicate="within")
columns_to_drop = ['geometry', 'index_right', 'merge_id']
cdom_sb = cdom_sb.drop(columns=columns_to_drop)
cdom_sb= cdom_sb.reset_index(drop=True)


cdom_sb['datetime'] = pd.to_datetime(cdom_sb['datetime']) #ensure datetime is in correct format
cdom_sb = cdom_sb[cdom_sb['datetime'] >= '2000-01-01'] #only want data from 2000 on for this algorithm 

cdom_sb['depth'] = pd.to_numeric(cdom_sb['depth'], errors='coerce')
cdom_sb = cdom_sb[cdom_sb['depth'] <=150].reset_index(drop=True)

cdom_sb = cdom_sb.dropna(axis=1, how='all')

cdom_sb.to_excel('SB_cdom_na.xlsx', index = False)

#if ag is wanted, uncomment below 

# ag_sb = cdom_all[['ag','abs_ag','wavelength','datetime', 'lon', 'lat', 'identifier_product_doi', 'affiliations', 'investigators', 'contact', 'experiment', 'cruise',
#                      'data_type',  'water_depth', 'measurement_depth', 'station','depth', 'time_flag', 'coord_flag',]]
# ag_sb = ag_sb.dropna(subset=['ag'], how='all')
# ag_sb = ag_sb.dropna(subset=['lat'], how='all')
# ag_sb = ag_sb.dropna(subset=['datetime'], how='all').reset_index(drop=True)

# shp = gpd.read_file(r'C:\Users\gianna.milton\Documents\Python\Shapefiles\combined_coastline.shp')
# gdf = gpd.GeoDataFrame(ag_sb, geometry=gpd.points_from_xy(ag_sb.lon, ag_sb.lat), crs="EPSG:4269")
# gdf = gdf.to_crs(shp.crs)
# ag_sb = gpd.sjoin(gdf, shp, how="inner", predicate="within")
# columns_to_drop = ['geometry', 'index_right', 'merge_id']
# ag_sb = ag_sb.drop(columns=columns_to_drop)
# ag_sb= ag_sb.reset_index(drop=True)

# #remove wavelengths with too high resolution 
# dec_mask = pd.to_numeric(ag_sb['wavelength'], errors='coerce').fillna(0) % 1 == 0 #only keep whole numbers
# ag_sb = ag_sb[dec_mask]
# ag_sb=ag_sb[(ag_sb['wavelength']<900) & (ag_sb['wavelength']>300)]

# df_parts = np.array_split(ag_sb, 2)
# df1 = df_parts[0]
# df2 = df_parts[1]
# df1.to_excel('sb_ag_raw_1.xlsx', index = False)
# df2.to_excel('sb_ag_raw_2.xlsx', index = False)

