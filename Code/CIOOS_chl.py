"""
Created on Wed Apr 15 10:37:34 2026
CIOOS_chl
CIOOS chlorophyll data, found by searching 'chlorophyll' on their erddap and only keeping non-flourecent (in-vivo) chlorophyll values

@author: gianna.milton
"""
import pandas as pd
import geopandas as gpd
import requests
import xarray as xr 


url='https://data.cioospacific.ca/erddap/tabledap/IYS_NISKIN_chl_phaeo.nc?cruise%2Cstation%2Ctime%2Clatitude%2Clongitude%2Cdepth%2Cchlorophyll_a&time%3E=2019-03-07T00%3A00%3A00Z&time%3C=2019-03-14T15%3A59%3A00Z'
url = requests.get(url, verify=False).content #load in data from their erddap
da = xr.open_dataset(url)
da1= da.to_dataframe() #format dataset into dataframe
da1 = da1.rename(columns={'time': 'datetime','latitude':'lat','longitude':'lon','chlorophyll_a':'chl'}) #standardize column names 
#add metadata
da1['experiment'] = da.project 
da1['investigators']=da.publisher 
da1['affiliations']=da.institution
da1['DOI_url']= da.infoUrl
da1['HPLC'] = 1 #after researching project, not HPLC methods used
counts_series = da1[['depth','datetime','lat','lon']].value_counts() #count how many unique cast,depth, datetime, lat, and lons there are
da1['triplicate'] = 1 #based on inpsecting counts_series, no triplicates



url='https://data.cioospacific.ca/erddap/tabledap/IOS_BOT_Profiles.nc?mission_id%2Cscientist%2Cproject%2Cagency%2Cplatform%2Cinstrument_type%2Cinstrument_model%2Clatitude%2Clongitude%2Ctime%2Cdepth%2CCPHLFLP1&time%3E=2000-01-01&time%3C=2024-08-30T03%3A17%3A44Z'
url = requests.get(url, verify=False).content
da = xr.open_dataset(url)
da2= da.to_dataframe() #convert to dataframe
da2 = da2.dropna(subset=['CPHLFLP1']) #if no chlorophyll data in row, drop
da2 = da2.rename(columns={'scientist': 'investigators','project':'experiment','agency':'affiliations','platform':'station',
                          'latitude':'lat','longitude':'lon','time':'datetime','CPHLFLP1':'chl'})  #standardize column name
#triplicate flag
counts_series = da2[['depth','datetime','lat','lon']].value_counts() #count how many unique cast,depth, datetime, lat, and lons there are
counts_df = counts_series.reset_index(name='freq_uniq')
da2 = pd.merge(da2, counts_df, on=['depth','datetime','lat','lon'], how='left') #add frequency column to original dataframe4

#sometimes, triplicate specific times are recorded (ex: 3:00, 3:05, 3:10 ), so also check for unique datehour entries
da2['date_hour'] = da2['datetime'].dt.strftime('%Y-%m-%d %H')
counts_series = da2[['depth','date_hour','lat','lon']].value_counts() #count how many unique datehour, lat, and lons there are
counts_df = counts_series.reset_index(name='freq_hour')
da2 = pd.merge(da2, counts_df, on=['depth','date_hour','lat','lon'], how='left') #add frequency column to original dataframe
da2['triplicate'] = 1 #assume bad unless otherwise said
da2.loc[da2['freq_uniq'] == 3, 'triplicate'] = 0 #if there was a unique datetime, lat, and lon that happened 3 times, triplicate
da2.loc[(da2['freq_uniq'] == 1) &(da2['freq_hour'] == 3), 'triplicate'] = 0 #if 1 unique datetime but 3 unique date hours, assume triplicate

da2=da2[['investigators', 'experiment', 'affiliations', 'station', 'lat', 'lon', 'datetime', 'depth', 'chl', 'triplicate']]
da2['HPLC'] = 1 #based on researching project, no HPLC methods used
da2['DOI_url']='https://data.cioospacific.ca/erddap/tabledap/IOS_BOT_Profiles'
da2=da2.loc[da2['depth']<=150].reset_index(drop=True)#only subset to top 150 m
da2 = da2[da2['chl'] >= 0] #remove any negative chlorophyll values


url='https://cioosatlantic.ca/erddap/tabledap/bio_atlantic_zone_monitoring_program_bottle_bbmp.nc?mission_descriptor%2Cinstitute%2Cstation%2Clatitude%2Clongitude%2Ctime%2Cdepth%2CChlorophyll_A%2CHPLC_chlorophyll_a&time%3E=2000-01-01&time%3C=2024-12-31T13%3A19%3A00Z'
url = requests.get(url, verify=False).content
da = xr.open_dataset(url)
da3= da.to_dataframe()
da3=da3.dropna(subset=['Chlorophyll_A', 'HPLC_chlorophyll_a'], how='all') #this project records both non-HPLC and HPLC data. remove any rows that have both types empty
da3 = da3.rename(columns={'mission_descriptor': 'cruise','institute':'affiliations','HPLC_chlorophyll_a':'chl_a',
                          'latitude':'lat','longitude':'lon','time':'datetime','Chlorophyll_A':'chl'}) 

#some chl and chl_a values are shifted down, creating duplicated datetime and sample information instead of being coincidental. so need to re aling them 
metadata_cols = ['cruise', 'affiliations', 'station', 'lat', 'lon', 'datetime', 'depth'] #designate columns to keep 
da3 = da3.groupby(metadata_cols, as_index=False).first() #group by unique metadata sample information
#add metadata information 
da3['experiment'] = da.program 
da3['investigators']=da.chief_scientist 
da3['affiliations']=da.institution
da3['DOI_url']= da.publisher_url
#HPLC
da3['HPLC'] = 0 #initiate all columns as HPLC= true, only empty values will be 1 
da3.loc[da3['chl_a'].isna(), 'HPLC'] = 1 #if chl_a not recorded, turn to false
counts_series = da3[['depth','datetime','lat','lon']].value_counts() #count how many unique cast,depth, datetime, lat, and lons there are
da3['triplicate'] = 1 #based on inpsecting counts_series, no triplicates

#combine the datasets into single dataframe
df_combined = pd.concat([da1, da2,da3], ignore_index=True)

#subset to the shapefile 
shp = gpd.read_file(r'C:\Users\gianna.milton\Documents\Python\Shapefiles\combined_coastline.shp')
gdf = gpd.GeoDataFrame(df_combined, geometry=gpd.points_from_xy(df_combined.lon, df_combined.lat), crs="EPSG:4269")
gdf = gdf.to_crs(shp.crs)
df_combined = gpd.sjoin(gdf, shp, how="inner", predicate="within")
columns_to_drop = ['geometry', 'index_right', 'merge_id']
df_combined = df_combined.drop(columns=columns_to_drop)
df_combined= df_combined.reset_index(drop=True)


df_combined.to_excel('CIOOS_chl.xlsx')
