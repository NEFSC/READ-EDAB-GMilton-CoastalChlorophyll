# -*- coding: utf-8 -*-
"""
Created on Thu Feb 19 17:01:59 2026
BCO-DMO_cdom, go through BCO-DMO cdom datasets and compile/ clean
@author: gianna.milton
"""
import numpy as np
import pandas as pd
import geopandas as gpd

#https://www.bco-dmo.org/search/dataset?searchParameters=%7E%28%7E%28type%7E%27parameter%7Evalue%7E%28%7E%27CDOM%29%7Ebool%7E%27and%29%29
#go through these results, inspecting them, and if cdom was sampled and had the correct units, locally downloaded

GoMX1 = pd.read_excel(r'CDOM\BCO-DMO\bottle_data.xlsx')
GoMX1['time_utc'] = [f"{int(t):04d}" for t in GoMX1['time_utc']]  #for every row in mtime pad with 0 unitl it's 4 numbers long (HH:mm)
GoMX1 = GoMX1.rename(columns={'year_utc': 'year','month_utc': 'month','day_utc': 'day',})
GoMX1['hour'] = [int(t[:2]) for t in GoMX1['time_utc']] #pull hour values from column
GoMX1['minute'] = [int(t[2:4]) for t in GoMX1['time_utc']] #pull min values from column
GoMX1['datetime']= pd.to_datetime(GoMX1[['year', 'month', 'day', 'hour', 'minute']]) #create datetime variable from individual time elements
GoMX1 = GoMX1[['datetime','lat', 'lon', 'depth','cruiseid', 'CDOM','turbidity']] #subset to only needed columns
#add metadata
GoMX1['experiment']='GoMX - DHOS'
GoMX1['source']='BCO-DMO'
GoMX1['investigators']='Samantha B. Joye'
GoMX1['affiliations']='University of Georgia'
GoMX1['url']='https://www.bco-dmo.org/dataset/3727'


GoMX2 = pd.read_excel(r'CDOM\BCO-DMO\AT18-02_CTD.xlsx')
GoMX2['time_start_utc'] = [f"{int(t):04d}" for t in GoMX2['time_start_utc']] 
GoMX2['hour'] = [int(t[:2]) for t in GoMX2['time_start_utc']]
GoMX2['minute'] = [int(t[2:4]) for t in GoMX2['time_start_utc']]
GoMX2['datetime'] =pd.to_datetime(GoMX2['date_start_utc'].dt.date.astype(str)+ ' ' +GoMX2['hour'].astype(str)+ ':' +GoMX2['minute'].astype(str), format='%Y-%m-%d %H:%M')
GoMX2 = GoMX2[['datetime','lat', 'lon', 'depth', 'CDOM','turbidity']]
GoMX2['experiment']='GoMX - DHOS'
GoMX2['source']='BCO-DMO'
GoMX2['investigators']='Samantha B. Joye'
GoMX2['affiliations']='University of Georgia'
GoMX2['url']='https://www.bco-dmo.org/dataset/3728'

GoMX3 = pd.read_excel(r'CDOM\BCO-DMO\WS1010_CTD.xlsx')
GoMX3['time_utc'] = [f"{int(t):04d}" for t in GoMX3['time_utc']]
GoMX3 = GoMX3.rename(columns={'month_utc': 'month','day_utc': 'day',})
GoMX3['hour'] = [int(t[:2]) for t in GoMX3['time_utc']]
GoMX3['minute'] = [int(t[2:4]) for t in GoMX3['time_utc']]
GoMX3['datetime']= pd.to_datetime(GoMX3[['year', 'month', 'day', 'hour', 'minute']])
GoMX3 = GoMX3[['datetime','lat', 'lon', 'depth', 'CDOM']]
GoMX3['experiment']='GoMX - DHOS'
GoMX3['source']='BCO-DMO'
GoMX3['investigators']='Samantha B. Joye'
GoMX3['affiliations']='University of Georgia'
GoMX3['url']='https://www.bco-dmo.org/dataset/3729'

nerissa = pd.read_excel(r'CDOM\BCO-DMO\Nerissa_CTD.xlsx')
nerissa['Time'] = [f"{int(t):04d}" for t in nerissa['Time']] 
nerissa['Date'] = nerissa['Date'].astype(str) #change Date column datatype for easy datetime element extraction
#exctract individual datetime elements from Date column 
nerissa['month'] = [int(t[4:6]) for t in nerissa['Date']]
nerissa['day'] = [int(t[6:8]) for t in nerissa['Date']]
nerissa['year'] = [int(t[0:4]) for t in nerissa['Date']]
nerissa['hour'] = [int(t[:2]) for t in nerissa['Time']]
nerissa['minute'] = [int(t[2:4]) for t in nerissa['Time']]
nerissa['datetime']= pd.to_datetime(nerissa[['year', 'month', 'day', 'hour', 'minute']]) #Create datetime column
nerissa = nerissa.rename(columns={'Latitude': 'lat','Longitude': 'lon','Depth':'depth',}) #rename columns for consistancy 
nerissa = nerissa[['datetime','lat', 'lon', 'depth', 'CDOM','Station_ID']]
#add metadata 
nerissa['experiment']='SoCalPlumeEx2012'
nerissa['source']='BCO-DMO'
nerissa['investigators']='Raphael M. Kudela'
nerissa['affiliations']='University of California-Santa Cruz'
nerissa['url']='https://www.bco-dmo.org/dataset/537627'

yfin= pd.read_excel(r'CDOM\BCO-DMO\YellowFin_CTD.xlsx')
yfin['Date'] = yfin['Date'].astype(str)#change Date column datatype for easy datetime element extraction
#exctract individual datetime elements from Date column 
yfin['month'] = [int(t[4:6]) for t in yfin['Date']]
yfin['day'] = [int(t[6:8]) for t in yfin['Date']]
yfin['year'] = [int(t[0:4]) for t in yfin['Date']]
yfin['datetime']= pd.to_datetime(yfin[['year', 'month', 'day']])  #create datetime column
yfin = yfin.rename(columns={'Latitude': 'lat','Longitude': 'lon','Depth':'depth','Turbidity':'turbidity'}) #rename column for consistancy
yfin = yfin[['datetime','lat', 'lon', 'depth', 'CDOM','turbidity','Station_ID']]
#add metadata
yfin['experiment']='SoCalPlumeEx2012'
yfin['source']='BCO-DMO'
yfin['investigators']='Raphael M. Kudela'
yfin['affiliations']='University of California-Santa Cruz'
yfin['url']='https://www.bco-dmo.org/dataset/537818'

GoMX4= pd.read_excel(r'CDOM\BCO-DMO\discrete_samples_concat.xlsx')
GoMX4['Date'] = GoMX4['Date'].astype(str)
GoMX4['Time'] = GoMX4['Time'].astype(str)
GoMX4['datetime'] = pd.to_datetime(GoMX4['Date'] + ' ' + GoMX4['Time']) #create datetime from combining Date and Time columns 
GoMX4 = GoMX4.rename(columns={'Latitude':'lat','Longitude':'lon','Turbidity':'turbidity','Cruise':'cruiseid','Station':'Station_ID',
                              'Sample_Depth':'depth','wetCDOM':'CDOM'}) #standardize column names
GoMX4 = GoMX4[['datetime','lat', 'lon', 'depth', 'CDOM','turbidity','Station_ID','cruiseid']]
#add metadata
GoMX4['experiment']='nGOMx acidification'
GoMX4['source']='BCO-DMO'
GoMX4['investigators']='Wei-Jun Cai'
GoMX4['affiliations']='University of Delaware'
GoMX4['url']='https://www.bco-dmo.org/dataset/772513'

reu_oto = pd.read_excel(r'CDOM\BCO-DMO\combined.xlsx')
reu_oto = reu_oto.rename(columns={'date_time': 'datetime','Water_Depth':'depth','Latitude':'lat','Longitude': 'lon','Station':'Station_ID'})
reu_oto = reu_oto[['datetime','lat', 'lon', 'depth', 'CDOM','Station_ID']]
reu_oto['experiment']='REU-OTO'
reu_oto['source']='BCO-DMO'
reu_oto['investigators']='Lisa Campbell'
reu_oto['affiliations']='Texas A&M University'
reu_oto['url']='https://www.bco-dmo.org/dataset/753882'

scanfish = pd.read_excel(r'CDOM\BCO-DMO\scanfish_opc.xlsx')
scanfish['datetime']= pd.to_datetime(scanfish['ISO_DateTime_UTC']) #Format datetime column to pandas datetime 
scanfish = scanfish[['datetime','lat', 'lon', 'depth', 'CDOM']]
#add metadata
scanfish['experiment']='GoMX - DHOS'
scanfish['source']='BCO-DMO'
scanfish['investigators']=' Michael R. Roman'
scanfish['affiliations']='University of Maryland Center for Environmental Science'
scanfish['url']='https://www.bco-dmo.org/dataset/746081'

harvey = pd.read_excel(r'CDOM\BCO-DMO\oct_2017_discrete.xlsx')
harvey['datetime']= pd.to_datetime(harvey['DateTime']) #Format datetime column to pandas datetime 
harvey = harvey.rename(columns={'Cruise':'cruiseid','Depth':'depth','Latitude':'lat','Longitude': 'lon','Station':'Station_ID',
                                'wetCDOM':'CDOM','Turbidity':'turbidity'})#standardize column names
harvey = harvey[['datetime','lat', 'lon', 'depth', 'CDOM','turbidity','Station_ID','cruiseid']]
#add metadata
harvey['experiment']='HarveyCarbonCycle'
harvey['source']='BCO-DMO'
harvey['investigators']='Brian Roberts'
harvey['affiliations']='Louisiana Universities Marine Consortium'
harvey['url']='https://www.bco-dmo.org/dataset/844721'

hrr=pd.read_excel(r'CDOM\BCO-DMO\HRR_ctd_2017.xlsx')
hrr['datetime']= pd.to_datetime(hrr['ISO_DateTime_UTC']) #Format datetime column to pandas datetime 
hrr = hrr.rename(columns={'wetCDOM':'CDOM','depSM':'depth','lat_decdeg':'lat','lon_decdeg': 'lon','station':'Station_ID'})#standardize column names
hrr = hrr[['datetime','lat', 'lon', 'depth', 'CDOM','Station_ID']]
#add metadata
hrr['experiment']='RAPID HRR'
hrr['source']='BCO-DMO'
hrr['investigators']='Lisa Campbell'
hrr['affiliations']='Texas A&M University'
hrr['url']='https://www.bco-dmo.org/dataset/809428'

rapid=pd.read_excel(r'CDOM\BCO-DMO\CTD.xlsx')
rapid['datetime']= pd.to_datetime(rapid['Start_ISO_DateTime_UTC']) #Format datetime column to pandas datetime 
rapid = rapid.rename(columns={'Cruise_ID':'cruiseid','Station':'Station_ID','Depth': 'depth','Latitude':'lat','Longitude': 'lon',
                              'Fluorescence_WET_CDOM':'CDOM'})#standardize column names
rapid = rapid[['datetime','lat', 'lon', 'depth', 'CDOM','Station_ID','cruiseid']]
rapid['experiment']='RAPID Plankton'
rapid['source']='BCO-DMO'
rapid['investigators']='Beth Stauffer'
rapid['affiliations']='University of Louisiana at Lafayette'
rapid['url']='https://www.bco-dmo.org/dataset/827969'

#concatinate all project data into single dataframe
dfs=[GoMX1,GoMX2,GoMX3,nerissa,yfin,GoMX4,reu_oto,scanfish,harvey,hrr,rapid]
bcodmo_cdom = pd.concat(dfs).reset_index(drop=True)

bcodmo_cdom = bcodmo_cdom.replace('nd', np.nan) #Standardize nan entries to numpy.nan
bcodmo_cdom = bcodmo_cdom[bcodmo_cdom['depth'] <=150] #only retain top 150m of water column
bcodmo_cdom = bcodmo_cdom.dropna(how='all', subset=['CDOM', 'turbidity']) #if cdom is empty, remove it 
bcodmo_cdom = bcodmo_cdom.rename(columns={'CDOM':'cdom','cruiseid':'cruise','Station_ID':'station'})
bcodmo_cdom['datetime']= pd.to_datetime(bcodmo_cdom['datetime'],utc=True) #one last check to make sure datetime column is formatted 
bcodmo_cdom['datetime'] = bcodmo_cdom['datetime'].dt.tz_localize(None)

#subset data to shapefile
shp = gpd.read_file(r'Shapefiles\combined_coastline.shp')
gdf = gpd.GeoDataFrame(bcodmo_cdom, geometry=gpd.points_from_xy(bcodmo_cdom.lon, bcodmo_cdom.lat), crs="EPSG:4269")
gdf = gdf.to_crs(shp.crs)
bcodmo_cdom = gpd.sjoin(gdf, shp, how="inner", predicate="within")
columns_to_drop = ['geometry', 'index_right', 'merge_id']
bcodmo_cdom = bcodmo_cdom.drop(columns=columns_to_drop)
bcodmo_cdom= bcodmo_cdom.reset_index(drop=True)

bcodmo_cdom.to_excel('bco_dmo_cdom_qc.xlsx', index = False)

