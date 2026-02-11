# -*- coding: utf-8 -*-
"""
Created on Wed Jan 14 09:33:40 2026
QA/QC for all chlorophyll data

NOTE: data gathered with these entries on the seabass website:
    Description: Import chl HPLC,CTD, and DC  data from seabass
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

path_to_folder = 'west_coast\requested_files_1\requested_files' #NOTE: there are usually multiple requested_files, this is where you would manually loop thru them
all_folders = get_folder_names(path_to_folder)
#there can be thousands of columns to append in some of these .sb files. so create a selected_columns variable that will only append the needed columns to include 
selected_columns =['lat','lon','year','month','day','hour','minute','second','time','date','datetime', 'chl','Allo', 'alpha-beta-car', 'anth', 'asta', 'bchl_a',
                   'beta-beta-car', 'beta-epi-car', 'beta-psi-car', 'but-fuco', 'cantha', 'chl_a', 'chl_a_allom', 'chl_a_prime','chl_b', 'chl_c', 'chl_c1', 
                   'chl_c1c2', 'chl_c2', 'chl_c3', 'chlide_a', 'chlide_b', 'chors_id', 'croco', 'diadchr', 'diadino', 'diato', 'dino', 'dv_chl_a', 'dv_chl_b',
                   'echin', 'epi-epi-car', 'et-8-carot', 'et-chlide_a', 'et-chlide_b', 'fuco', 'gyro', 'hex-fuco', 'hex-kfuco', 'hpl_id', 'hplc_gsfc_id', 'lut', 
                   'lyco', 'me-chlide_a','me-chlide_b', 'mg_dvp', 'monado', 'mv_chl_a', 'mv_chl_b', 'neo', 'p-457', 'perid', 'phide_a', 'phide_b', 'phide_c',
                   'phytin_a','phytin_b', 'phytin_c',' phytyl-chl_c', 'pras', 'pyrophide_a', 'pyrophytin_a', 'pyrophytin_b', 'pyrophytin_c', 'siphn', 'siphx', 
                   'tot_chl_a', 'tot_chl_b', 'tot_chl_c', 'vauch', 'viola', 'zea','depth','station']

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
        columns_to_keep = [col for col in df.columns if col in selected_columns or col == 'datetime'] #only keep whatever columns are in selected_columns
        df_filtered = df[columns_to_keep]
        header = pd.DataFrame.from_dict(data1.headers, orient='index').T #create metedata header from dictionary and repeat it to match lenth of dataset
        header_repeated = pd.concat([header] * len(df_filtered), ignore_index=True)
        # Combine data and metadata
        combined = pd.concat([df_filtered.reset_index(drop=True), header_repeated], axis=1)
        combined = combined.loc[:, ~combined.columns.duplicated()]
        dfs.append(combined)
    #final concatenation
    globals()[str(all_folders[folders])] = pd.concat(dfs, ignore_index=True) #append all files in that specific affiliation file toether 

chl_columns =['chl','chl_a'] #for reducing rows without these in it (without ,'chl_experiment','chl_stimf')
for names in all_folders: #for each affilitation dataframe
    print(names)
    chl_cols=[col for col in (globals()[names]).columns if col in chl_columns] #detect the chlorophyll columns present 
    (globals()[names]).dropna(subset=chl_cols, how='all', inplace=True) #if rows in the chl columns empty, remove 

#for any remaining empty datetime, manually create it from the metadata date 
for names in all_folders:
    print(names)
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
            # If there's a parsing problem, skip gracefully
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


#strictly speaking, seabass marks chl as non-hplc and chl_a as hplc. however, sometimes hplc data is entered as chl. so to better detect if 
#the data is hplc or not, hplc_hints can be used to see if other HPLC exclusive variables were collected. 
hplc_hints =['Allo', 'alpha-beta-car', 'anth', 'asta', 'bchl_a', 'beta-beta-car', 'beta-epi-car', 'beta-psi-car', 'but-fuco', 'cantha', 
             'chl_a', 'chl_a_allom', 'chl_a_prime','chl_b', 'chl_c', 'chl_c1', 'chl_c1c2', 'chl_c2', 'chl_c3', 'chlide_a', 'chlide_b',
             'chors_id', 'croco', 'diadchr', 'diadino', 'diato', 'dino', 'dv_chl_a', 'dv_chl_b', 'echin', 'epi-epi-car', 'et-8-carot',
             'et-chlide_a', 'et-chlide_b', 'fuco', 'gyro', 'hex-fuco', 'hex-kfuco', 'hpl_id', 'hplc_gsfc_id', 'lut', 'lyco', 'me-chlide_a',
             'me-chlide_b', 'mg_dvp', 'monado', 'mv_chl_a', 'mv_chl_b', 'neo', 'p-457', 'perid', 'phide_a', 'phide_b', 'phide_c', 'phytin_a',
             'phytin_b', 'phytin_c',' phytyl-chl_c', 'pras', 'pyrophide_a', 'pyrophytin_a', 'pyrophytin_b', 'pyrophytin_c', 'siphn', 'siphx', 
             'tot_chl_a', 'tot_chl_b', 'tot_chl_c', 'vauch', 'viola', 'zea'] #columns that hint towards hplc 
      
# create HPLC flag
#if chl_a was recorded, flag as hplc.
#if chl is present WITHOUT chl_a, BUT other columns in hplc_hints are present, mark as suspected HPLC (2)
for names in all_folders:
    df = globals()[names] 
    df['HPLC'] = 1 #assume not hplc unless i tell it otherwise
    if 'chl_a' in df.columns:
        df.loc[df['chl_a'].notna(), 'HPLC'] = 0 #if chl_a in columns and is not empty, mark as hplc
    existing_hints = [col for col in hplc_hints if col in df.columns] #first, are there any hplc columns in the dataframe
    if 'chl' in df.columns:
        cond_chl_exists = df['chl'].notna() #if chl is not empty
        if 'chl_a' in df.columns: #if chl_a is either is empty or doesn't exist 
            cond_chla_empty = df['chl_a'].isna()
        else:
            cond_chla_empty = True 
        if existing_hints: #if the dataframe has these columns in it 
            cond_hints_exist = df[existing_hints].notna().any(axis=1) #pull these columns
        else:
            cond_hints_exist = False
        final_mask = cond_chl_exists & cond_chla_empty & cond_hints_exist #if chl is recorded AND chl_a is empty AND there are hplc_hint columns
        df.loc[final_mask, 'HPLC'] = 2 #flag as suspected hplc
        
        #you can stop above, the below is to detect when and where the suspected flags occur 
        flagged_rows = df[final_mask]
        for index, row in flagged_rows.iterrows(): #for the rows that agree with the final mask
            found_cols = [col for col in existing_hints if pd.notna(row[col])]
            print(f"DF: {names} | Row: {index} | Flagged as HPLC (2). Found hints: {found_cols}")
    
dfs_to_concat = [(globals()[names]) for names in all_folders] #concatinate the dataframes in all_folders

#east coast
east1 = pd.concat(dfs_to_concat, ignore_index=True) #save dfs_to_concat to single dataframe. STOP HERE and repeat if you have multiple requested files
east2 = pd.concat(dfs_to_concat, ignore_index=True)
east3 = pd.concat(dfs_to_concat, ignore_index=True)
east_coast = pd.concat([east1,east2,east3])
east_coast=east_coast[['datetime', 'lat', 'lon', 'chl', 'station', 'affiliations', 'investigators', 'contact', 'experiment', 'cruise', 'data_type',
        'water_depth', 'measurement_depth', 'water_depth ', 'depth', 'identifier_product_doi', 'instrument_name', 'instrument', 'time_flag', 
        'coord_flag',  'hplc_lab', 'chl_a', 'sequence_number','sample','data_file_name','HPLC']]

#alaska
alas1= pd.concat(dfs_to_concat, ignore_index=True)
alas2 = pd.concat(dfs_to_concat, ignore_index=True)
alas2['lat'] = pd.to_numeric(alas2['lat'], errors='coerce')
alas2['lon'] = pd.to_numeric(alas2['lon'], errors='coerce')
alaska = pd.concat([alas1, alas2])
alaska=alaska[['datetime', 'lon', 'lat', 'identifier_product_doi', 'affiliations', 'investigators', 'contact', 'experiment', 'cruise',
        'data_type',  'water_depth', 'measurement_depth',  'hplc_lab', 'station','depth', 'time_flag', 'coord_flag', 'chl', 'instrument_model',
          'chl_a','data_file_name','HPLC']]
#gom
gom= pd.concat(dfs_to_concat, ignore_index=True)
gom=gom[['datetime', 'lat', 'lon', 'chl', 'station', 'affiliations', 'investigators', 'contact', 'experiment', 'cruise', 'data_type',
        'measurement_depth', 'water_depth', 'depth', 'identifier_product_doi', 'instrument_name','data_file_name', 'instrument_model',
        'time_flag', 'coord_flag',  'hplc_lab', 'chl_a','sample','HPLC']]
#haw
haw= pd.concat(dfs_to_concat, ignore_index=True)
haw=haw[['datetime', 'lon', 'lat', 'identifier_product_doi', 'affiliations', 'investigators', 'contact', 'experiment', 'cruise',
        'data_type',  'water_depth', 'measurement_depth',  'hplc_lab', 'station','depth', 'time_flag', 'coord_flag', 'chl', 'instrument_model',
        'data_file_name', 'chl_a' ,'HPLC']]

#west coast
west1 = pd.concat(dfs_to_concat, ignore_index=True)
west2 = pd.concat(dfs_to_concat, ignore_index=True)
west_coast = pd.concat([west1,west2])
west_coast=west_coast[['datetime', 'station', 'depth', 'lat', 'lon', 'identifier_product_doi', 'investigators', 'affiliations', 'contact', 'experiment',
        'cruise', 'data_type', 'water_depth', 'time_flag', 'coord_flag', 'chl_a', 'measurement_depth', 'instrument_model', 
        'chl', 'hplc_lab', 'data_file_name','HPLC']]


shp = gpd.read_file(r'C:\Users\gianna.milton\Documents\Python\Shapefiles\Hawaii_Caribbean\20210609_fishery_management_council_regions.shp')
gdf = gpd.GeoDataFrame(west_coast, geometry=gpd.points_from_xy(west_coast.lon, west_coast.lat), crs="EPSG:4269")
gdf = gdf.to_crs(shp.crs)
west_coast = gpd.sjoin(gdf, shp, how="inner", predicate="within")
columns_to_drop = ['geometry','index_right', 'Shape__Are', 'Shape__Len','FishRegion']
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
axs1.set_xlim(-180,-65)
axs1.set_ylim(17,max(west_coast.lat)+2)
cb=fig.colorbar(im,ax=axs1,orientation='horizontal')


#east coast
east_coast.to_excel('raw_east_SB.xlsx', index = False)
  #all files from seabass products with chl, only qa is lat,lon, and datetime creation, shapefile, and column limiting

#alaska
alaska.to_excel('raw_alaska_SB.xlsx', index = False)

gom.to_excel('raw_gom_SB.xlsx', index = False)

#below is actually hawaii fyi
haw.to_excel('raw_haw_SB.xlsx', index = False)

#westcoast
#west coast dataframe is too large to save as single, need to seperate into 2
df_parts = np.array_split(west_coast, 2)
df1 = df_parts[0]
df2 = df_parts[1]
df1.to_excel('raw_west_SB1.xlsx', index = False)
df2.to_excel('raw_west_SB2.xlsx', index = False)





#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#step 2. now that all the raw sb files are concatinated and seperated, load them all in and create single dataframe
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#first, load in raw xlsx files one at a time and conduct qa/qc. repeat the steps below until all raw files are saved 
df = pd.read_excel('raw_west_SB.xlsx') 
df['datetime'] = pd.to_datetime(df['datetime']) #ensure datetime is in correct format
df = df[df['datetime'] >= '2000-01-01'] #only want data from 2000 on for this algorithm 

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
all_data = all_data.drop_duplicates()

all_data.to_excel('allchl_SB_tripFLAGS.xlsx', index = False) #sb data with HPLC and Triplicate flags, without any repeats



