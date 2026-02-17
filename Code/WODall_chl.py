# -*- coding: utf-8 -*-
"""
Created on Fri Jan 23 12:46:08 2026
WODall_chl
load in raw WOD chl data and organize / format to match seabass data, including hplc and triplicate flags. 

NOTE: raw data pulled from WOD select https://www.ncei.noaa.gov/access/world-ocean-database-select/dbsearch.html in multiple rounds (below)

Boundries: lon = -127 -> -52, lat = 76 -> 8
dates: 2000-01-01 to 2024- 04-28
dataset: OSD, MRB, SUR
Total chlorophyll

Boundries: lon = -162 -> -47, lat = 77 -> 15
dates: 2000-01-01 to 2025- 04-01
dataset: OSD, CTD,PFL
Total Chlorophyll

for ECOMON data, go to project query and only gather from project code 637 (ECOMON)

https://www.ncei.noaa.gov/access/world-ocean-database/wod-codes.html for specific code keys

@author: gianna.milton
"""
import pandas
import pandas as pd
import warnings
import matplotlib.pyplot as plt
import cartopy
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import geopandas as gpd
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)
warnings.filterwarnings('ignore', category=FutureWarning)
import geopandas as gpd
from datetime import timedelta

#start def loop for reading and organizing raw WOD files
def wod_df(excel_file):
    
    '''
    arg: path to the raw excelfile 
    return: dataframe with unique columns for each variable/ metadata 
    '''
    WOD_raw = pd.read_excel(excel_file, header=None) #load in that excel file 
    WOD_raw[0] = WOD_raw[0].str.lower() #since there are some inconsistancies with column cases, put everything as lower case
    #identify cast_blocks (rows between '#' and 'END OF VARIABLES SECTION')
    cast_blocks = []
    start_idx = None #to track the start of the index
    
    #first, identify and record the index positions of the cast blocks, i.e. the start and end of each cast
    for idx, row in WOD_raw.iterrows(): #for every row
        first_cell = str(row[0]) if pd.notna(row[0]) else "" #the first cell of the row (as long as it exists)
        if first_cell.startswith("#") and "end of variables section" not in first_cell: #if it's the start of the cast and NOT the end
            if start_idx is not None:
                cast_blocks.append((start_idx, idx)) #if the first cell is #, record the start indx
            start_idx = idx #start of the new cast
        
        elif "end of variables section" in first_cell: #if it's the end of a cast, record the index
            if start_idx is not None:
                cast_blocks.append((start_idx, idx)) #append this index as the end
                start_idx = None
                
                
    #now that we have the indeces to distinguish each cast block, process the casts individually 
    all_data = []
    for start, end in cast_blocks: #for each pair of index vales in cast_block
        cruise_df = WOD_raw.iloc[start:end+1].reset_index(drop=True) #loacte those indexes of that block and make a dataframe
        metadata = {}
        variable_data_started = False #flag to indicate if inside the VARIABLES section
        variable_data = []
        for _, row in cruise_df.iterrows(): #for each row in the block of the cast
            row_values = row.dropna().astype(str).tolist() #convert to string
            if not row_values: #skip all empty rows 
                continue
            if "variables" in row_values[0]: #if the start of the varibale section, turn to true
                variable_data_started = True
                continue
            if "end of variables section" in row_values[0]: #if at the end, break and go back to for loop
                break
    
    
            if not variable_data_started: #if we're in the metadata section
                key = row_values[0].strip() #seperate the row into sections
                if len(row_values) > 1: #if we are in the metadata section
                    value = row_values[1].strip() #take from column 2
                    metadata[key] = value #save as metadata
                    #metadata.columns.str.lower()

            else: #if in variable row
                try:
                    if row_values[0].isdigit() and len(row_values) >= 6: 
                        depth = float(row_values[1]) #append depth
                        chl = float(row_values[4]) # append chlorophyll
                        variable_data.append((depth, chl))
                        #variable_data.columns.str.lower()
                except:
                    continue
    
        #append metadata and variables
        for depth, chl in variable_data: #for this row of variables, rename, then append to the dataframe
            row = metadata.copy()
            row["depth (m)"] = depth
            row["chlorophyll (ug/l)"] = chl
            all_data.append(row)
   
    df = pd.DataFrame(all_data)
    #create datetime
    df["datetime"] = pd.to_datetime(df[["year", "month", "day"]]) + df["time"].apply(lambda t: timedelta(hours=float(t)) if pd.notnull(t) else pd.NaT)
    return df

#run first raw dataset
wod_1 = wod_df(r'C:\Users\gianna.milton\Documents\Python\WOD\ocldb1748619702.620293.OSD.csv\ocldb1748619702.620293.OSD.xlsx')
wod_1=wod_1[wod_1['project'] != '33'] #take out CalCOFI values since appended elsewhere
wod_1=wod_1[wod_1['project'] != '301'] #take out HOTS values since appended elsewhere

wod_1=wod_1.rename(columns={'depth (m)':'depth','longitude':'lon','latitude':'lat','chlorophyll (ug/l)':'chl'})
#for this project, only want top 150 meters
wod_1=wod_1.loc[wod_1['depth']<=150].reset_index(drop=True) 
wod_1.lon= wod_1.lon.astype(float)
wod_1.lat= wod_1.lat.astype(float)
wod_1.chl=wod_1.chl.astype(float)

#to flag for HPLC, go thru each project and research if HPLC was recorded 
#636 -> SHELF BASIN INTERACTION PROJECT (SBI), looks like not HPLC
#597 ->	HYPOXIA STUDIES IN THE NORTHERN GULF OF MEXICO (https://www.ncei.noaa.gov/archive/archive-management-system/OAS/bin/prd/jquery/project/details/489)
#Looks like not HPLC
#412 -> MMS/NORTHEAST GULF OF MEXICO PHYS OCEANOGRAPHIC PROGRAM (NEGOM) https://digital.library.unt.edu/ark:/67531/metadc955363/m2/1/high_res_d/3084.pdf
#Looks like HPLC
#311 	CARBON RETENTION IN A COLORED OCEAN (CARIACO), looks like HPLC

#Begin flagging
wod_1['HPLC']=1 #assume all points are not hplc
wod_1.loc[wod_1['project'] == '412', 'HPLC'] = 0 
wod_1.loc[wod_1['project'] == '311', 'HPLC'] = 0
wod_1=wod_1[[ 'datetime','lat', 'lon','chl','depth','cast','originators cruise id', 'project','institute','instrument', 'investigator', 'HPLC','accession number']]

# triplicate flag
counts_series = wod_1[['cast','depth','datetime','lat','lon']].value_counts() #count how many unique cast,depth, datetime, lat, and lons there are
counts_df = counts_series.reset_index(name='freq_uniq')
wod_1 = pd.merge(wod_1, counts_df, on=['cast','depth','datetime','lat','lon'], how='left') #add frequency column to original dataframe

#sometimes, triplicate specific times are recorded (ex: 3:00, 3:05, 3:10 ), so also check for unique datehour entries
wod_1['date_hour'] = wod_1['datetime'].dt.strftime('%Y-%m-%d %H')
counts_series = wod_1[['cast','depth','date_hour','lat','lon']].value_counts() #count how many unique datehour, lat, and lons there are
counts_df = counts_series.reset_index(name='freq_hour')
wod_1 = pd.merge(wod_1, counts_df, on=['cast','depth','date_hour','lat','lon'], how='left') #add frequency column to original dataframe

wod_1['triplicate'] = 1 #assume bad unless otherwise said
wod_1.loc[wod_1['freq_uniq'] == 3, 'triplicate'] = 0 #if there was a unique datetime, lat, and lon that happened 3 times, triplicate
wod_1.loc[(wod_1['freq_uniq'] == 1) &(wod_1['freq_hour'] == 3), 'triplicate'] =0 #if 1 unique datetime and 3 unique date_hours, assume triplicate

#second raw dataset
wod_2 = wod_df(r'C:\Users\gianna.milton\Documents\Python\WOD\WOD_round2_raw\ocldb1761586645.2754592.OSD.xlsx')
wod_2=wod_2[wod_2['project'] != '33'] #take out CalCOFI since appended elsewhere
wod_2=wod_2[wod_2['project'] != '301'] #take out HOTS since appended elsewhere
wod_2=wod_2.rename(columns={'depth (m)':'depth','longitude':'lon','latitude':'lat','chlorophyll (ug/l)':'chl'})
wod_2=wod_2.loc[wod_2['depth']<=150].reset_index(drop=True) 
wod_2.lon= wod_2.lon.astype(float)
wod_2.lat= wod_2.lat.astype(float)
wod_2.chl=wod_2.chl.astype(float)

#first go thru projects
# 597 ->HYPOXIA STUDIES IN THE NORTHERN GULF OF MEXICO (https://www.ncei.noaa.gov/archive/archive-management-system/OAS/bin/prd/jquery/project/details/489), no HPLC
# 636 -> SHELF BASIN INTERACTION PROJECT (SBI), no HPLC
# 412 ->MMS/NORTHEAST GULF OF MEXICO PHYS OCEANOGRAPHIC PROGRAM (NEGOM) https://digital.library.unt.edu/ark:/67531/metadc955363/m2/1/high_res_d/3084.pdf yes HPLC
#Begin flagging
wod_2['HPLC']=1 #assume all points are not hplc
wod_2.loc[wod_2['project'] == '412', 'HPLC'] = 0
wod_2=wod_2[[ 'datetime','lat', 'lon','chl','depth','cast','originators cruise id', 'project','institute','instrument', 'investigator', 'HPLC','accession number']]

#triplicate flag
counts_series = wod_2[['cast','depth','datetime','lat','lon']].value_counts() 
counts_df = counts_series.reset_index(name='freq_uniq')
wod_2 = pd.merge(wod_2, counts_df, on=['cast','depth','datetime','lat','lon'], how='left') 
wod_2['date_hour'] = wod_2['datetime'].dt.strftime('%Y-%m-%d %H')
counts_series = wod_2[['cast','depth','date_hour','lat','lon']].value_counts() 
counts_df = counts_series.reset_index(name='freq_hour')
wod_2 = pd.merge(wod_2, counts_df, on=['cast','depth','date_hour','lat','lon'], how='left') 

wod_2['triplicate'] = 1 #assume bad unless otherwise said
wod_2.loc[wod_2['freq_uniq'] == 3, 'triplicate'] = 0 #if there was a unique datetime, lat, and lon that happened 3 times, triplicate
wod_2.loc[(wod_2['freq_uniq'] == 1) &(wod_2['freq_hour'] == 3), 'triplicate'] = 0 #if 1 unique datetime recorded and only 3 for datehour, assume triplicate 

#don't run ocldb1761586645.2754592.PFL.xlsx since it's only invivo 

wod_3 = wod_df(r'C:\Users\gianna.milton\Documents\Python\WOD\WOD_round2_raw\ocldb1761586645.2754592.CTD.xlsx')
wod_3=wod_3[wod_3['project'] != '301'] #take out HOTS 
wod_3=wod_3[wod_3['project'] != '637'] #take out ECOMON since running it later

#121 ->SOUTHEAST AREA MONITORING AND ASSESSMENT PROGRAM (SEAMAP) https://www.gsmfc.org/seamap-gomrs, no hplc
#597 ->HYPOXIA STUDIES IN THE NORTHERN GULF OF MEXICO, no hplc 
wod_3['HPLC']=1

wod_3=wod_3.rename(columns={'depth (m)':'depth','longitude':'lon','latitude':'lat','chlorophyll (ug/l)':'chl'})
wod_3=wod_3.loc[wod_3['depth']<=150].reset_index(drop=True) 
wod_3.lon= wod_3.lon.astype(float)
wod_3.lat= wod_3.lat.astype(float)
wod_3.chl=wod_3.chl.astype(float)

wod_3=wod_3[[ 'datetime','lat', 'lon','chl','depth','cast','originators cruise id', 'project','institute','instrument', 'investigator', 'HPLC','accession number']]
counts_series = wod_3[['cast','depth','datetime','lat','lon']].value_counts()
counts_df = counts_series.reset_index(name='freq_uniq')
wod_3 = pd.merge(wod_3, counts_df, on=['cast','depth','datetime','lat','lon'], how='left') 
wod_3['date_hour'] = wod_3['datetime'].dt.strftime('%Y-%m-%d %H')
counts_series = wod_3[['cast','depth','date_hour','lat','lon']].value_counts() 
counts_df = counts_series.reset_index(name='freq_hour')
wod_3 = pd.merge(wod_3, counts_df, on=['cast','depth','date_hour','lat','lon'], how='left')

wod_3['triplicate'] = 1 #assume bad unless otherwise said
wod_3.loc[wod_3['freq_uniq'] == 3, 'triplicate'] = 0 
wod_3.loc[(wod_3['freq_uniq'] == 1) &(wod_3['freq_hour'] == 3), 'triplicate'] =0 

#WOD_4
wod_4 = wod_df(r'C:\Users\gianna.milton\Documents\Python\WOD\WOD_round2_raw\ocldb1761586645.2754592.CTD2.xlsx')
wod_4=wod_4[wod_4['project'] != '637'] #take out ECOMON

#same projects as last file, so no HPLC
wod_4['HPLC']=1 #no hplc here i think

wod_4=wod_4.rename(columns={'depth (m)':'depth','longitude':'lon','latitude':'lat','chlorophyll (ug/l)':'chl'})
wod_4=wod_4.loc[wod_4['depth']<=150].reset_index(drop=True) 
wod_4.lon= wod_4.lon.astype(float)
wod_4.lat= wod_4.lat.astype(float)
wod_4.chl=wod_4.chl.astype(float)

wod_4=wod_4[[ 'datetime','lat', 'lon','chl','depth','cast','originators cruise id', 'project','institute','instrument', 'investigator', 'HPLC','accession number']]
counts_series = wod_4[['cast','depth','datetime','lat','lon']].value_counts()
counts_df = counts_series.reset_index(name='freq_uniq')
wod_4 = pd.merge(wod_4, counts_df, on=['cast','depth','datetime','lat','lon'], how='left')
wod_4['date_hour'] = wod_4['datetime'].dt.strftime('%Y-%m-%d %H')
counts_series = wod_4[['cast','depth','date_hour','lat','lon']].value_counts() 
counts_df = counts_series.reset_index(name='freq_hour')
wod_4 = pd.merge(wod_4, counts_df, on=['cast','depth','date_hour','lat','lon'], how='left')

wod_4['triplicate'] = 1 #assume bad unless otherwise said
wod_4.loc[wod_4['freq_uniq'] == 3, 'triplicate'] = 0 
wod_4.loc[(wod_4['freq_uniq'] == 1) &(wod_4['freq_hour'] == 3), 'triplicate'] = 0 

#ECOMON
wod_ecomon = wod_df(r'C:\Users\gianna.milton\Documents\Python\WOD\ocldb1761249916.1960703.CTD.csv\ocldb1761249916.1960703.CTD.xlsx')
wod_ecomon['HPLC']=1 
wod_ecomon=wod_ecomon.rename(columns={'depth (m)':'depth','longitude':'lon','latitude':'lat','chlorophyll (ug/l)':'chl'})
wod_ecomon=wod_ecomon.loc[wod_ecomon['depth']<=150].reset_index(drop=True) 
wod_ecomon.lon= wod_ecomon.lon.astype(float)
wod_ecomon.lat= wod_ecomon.lat.astype(float)
wod_ecomon.chl=wod_ecomon.chl.astype(float)

wod_ecomon=wod_ecomon[[ 'datetime','lat', 'lon','chl','depth','cast','originators cruise id', 'project','institute', 'HPLC','accession number']]
counts_series = wod_ecomon[['cast','depth','datetime','lat','lon']].value_counts()
counts_df = counts_series.reset_index(name='freq_uniq')
wod_ecomon = pd.merge(wod_ecomon, counts_df, on=['cast','depth','datetime','lat','lon'], how='left')
wod_ecomon['date_hour'] = wod_ecomon['datetime'].dt.strftime('%Y-%m-%d %H')
counts_series = wod_ecomon[['cast','depth','date_hour','lat','lon']].value_counts() 
counts_df = counts_series.reset_index(name='freq_hour')
wod_ecomon = pd.merge(wod_ecomon, counts_df, on=['cast','depth','date_hour','lat','lon'], how='left')

wod_ecomon['triplicate'] = 1 
wod_ecomon.loc[wod_ecomon['freq_uniq'] == 3, 'triplicate'] = 0 
wod_ecomon.loc[(wod_ecomon['freq_uniq'] == 1) &(wod_ecomon['freq_hour'] == 3), 'triplicate'] = 0

#concatinate into 1 dataframe
dfs = [wod_1,wod_2,wod_3,wod_4,wod_ecomon]
wod_all = pd.concat(dfs)
wod_all=wod_all[['datetime', 'lat', 'lon', 'chl', 'depth', 'cast','originators cruise id', 'project', 'institute', 'instrument',
       'investigator', 'HPLC', 'triplicate','accession number']]
wod_all = wod_all.rename(columns={'originators cruise id':'cruise','project':'experiment','institute':'affiliations','investigator':'investigators'})

shp = gpd.read_file(r'C:\Users\gianna.milton\Documents\Python\Shapefiles\combined_coastline.shp')
gdf = gpd.GeoDataFrame(wod_all, geometry=gpd.points_from_xy(wod_all.lon, wod_all.lat), crs="EPSG:4269")
gdf = gdf.to_crs(shp.crs)
wod_all = gpd.sjoin(gdf, shp, how="inner", predicate="within")
columns_to_drop = ['geometry', 'index_right', 'merge_id']
wod_all = wod_all.drop(columns=columns_to_drop)
wod_all= wod_all.reset_index(drop=True)

fig=plt.figure(figsize=(12, 12))
axs1=fig.add_subplot(1,1,1,projection= cartopy.crs.PlateCarree())
axs1.add_feature(cfeature.LAND)
axs1.add_feature(cfeature.OCEAN)
axs1.add_feature(cfeature.BORDERS)
im=axs1.scatter(wod_all.lon,wod_all.lat,s=10)
gl=axs1.gridlines(linewidth=0.2,color='grey',alpha=0.5,linestyle='-',
                draw_labels=True, x_inline= False,y_inline=False)
gl.xformatter=LONGITUDE_FORMATTER
gl.yformatter=LATITUDE_FORMATTER
gl.top_labels = False    # Disable top labels
gl.right_labels = False  # Disable right labels
axs1.set_xlim(-180,-65)
cb=fig.colorbar(im,ax=axs1,orientation='horizontal')


#save as xlsx 
wod_all.to_excel('wod_chl_na.xlsx', index = False)

