# -*- coding: utf-8 -*-
"""
Created on Thu Feb 19 17:01:59 2026
BCO-DMO_cdom
@author: gianna.milton
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cartopy
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import geopandas as gpd

#BCO-dmo cdom
#https://www.bco-dmo.org/search/dataset?searchParameters=%7E%28%7E%28type%7E%27parameter%7Evalue%7E%28%7E%27CDOM%29%7Ebool%7E%27and%29%29
#any cdom with units mg/L or mg/m^3 kept, there's 11 files total
GoMX1 = pd.read_excel(r'C:\Users\gianna.milton\Documents\Python\CDOM\BCO-DMO\bottle_data.xlsx')
GoMX1['time_utc'] = [f"{int(t):04d}" for t in GoMX1['time_utc']]  #for every row in mtime pad with 0 unitl it's 4 numbers long (HH:mm) (i'm getting rid of seconds fyi)
GoMX1 = GoMX1.rename(columns={'year_utc': 'year','month_utc': 'month','day_utc': 'day',})
GoMX1['hour'] = [int(t[:2]) for t in GoMX1['time_utc']]
GoMX1['minute'] = [int(t[2:4]) for t in GoMX1['time_utc']]
GoMX1['datetime']= pd.to_datetime(GoMX1[['year', 'month', 'day', 'hour', 'minute']]) #datetime variable
GoMX1 = GoMX1[['datetime','lat', 'lon', 'depth','cruiseid', 'CDOM','turbidity']]
GoMX1 = GoMX1[GoMX1['CDOM'] != 'nd']
GoMX1 = GoMX1[GoMX1['turbidity'] != 'nd']
GoMX1['experiment']='GoMX - DHOS'
GoMX1['source']='BCO-DMO'
GoMX1['investigator']='Samantha B. Joye'
GoMX1['url']='https://www.bco-dmo.org/dataset/3727'


GoMX2 = pd.read_excel(r'C:\Users\gianna.milton\Documents\Python\CDOM\BCO-DMO\AT18-02_CTD.xlsx')
#GoMX2 = GoMX2.rename(columns={'date_start_utc': 'date','time_start_utc': 'time'})
GoMX2['time_start_utc'] = [f"{int(t):04d}" for t in GoMX2['time_start_utc']] 
GoMX2['hour'] = [int(t[:2]) for t in GoMX2['time_start_utc']]
GoMX2['minute'] = [int(t[2:4]) for t in GoMX2['time_start_utc']]
GoMX2['datetime'] =pd.to_datetime(GoMX2['date_start_utc'].dt.date.astype(str)+ ' ' +GoMX2['hour'].astype(str)+ ':' +GoMX2['minute'].astype(str), format='%Y-%m-%d %H:%M')
GoMX2 = GoMX2[['datetime','lat', 'lon', 'depth', 'CDOM','turbidity']]
GoMX2 = GoMX2[GoMX2['depth'] <=50] #848563 ->61711
GoMX2['experiment']='GoMX - DHOS'
GoMX2['source']='BCO-DMO'
GoMX2['investigator']='Samantha B. Joye'
GoMX2['url']='https://www.bco-dmo.org/dataset/3728'

GoMX3 = pd.read_excel(r'C:\Users\gianna.milton\Documents\Python\CDOM\BCO-DMO\WS1010_CTD.xlsx')
GoMX3['time_utc'] = [f"{int(t):04d}" for t in GoMX3['time_utc']]  #for every row in mtime pad with 0 unitl it's 4 numbers long (HH:mm) (i'm getting rid of seconds fyi)
GoMX3 = GoMX3.rename(columns={'month_utc': 'month','day_utc': 'day',})
GoMX3['hour'] = [int(t[:2]) for t in GoMX3['time_utc']]
GoMX3['minute'] = [int(t[2:4]) for t in GoMX3['time_utc']]
GoMX3['datetime']= pd.to_datetime(GoMX3[['year', 'month', 'day', 'hour', 'minute']]) #datetime variable
GoMX3 = GoMX3[['datetime','lat', 'lon', 'depth', 'CDOM']]
GoMX3 = GoMX3[GoMX3['depth'] <=50] #848563 ->61711
GoMX3['experiment']='GoMX - DHOS'
GoMX3['source']='BCO-DMO'
GoMX3['investigator']='Samantha B. Joye'
GoMX3['url']='https://www.bco-dmo.org/dataset/3729'

nerissa = pd.read_excel(r'C:\Users\gianna.milton\Documents\Python\CDOM\BCO-DMO\Nerissa_CTD.xlsx')
nerissa['Time'] = [f"{int(t):04d}" for t in nerissa['Time']] 
nerissa['Date'] = nerissa['Date'].astype(str)
nerissa['month'] = [int(t[4:6]) for t in nerissa['Date']]
nerissa['day'] = [int(t[6:8]) for t in nerissa['Date']]
nerissa['year'] = [int(t[0:4]) for t in nerissa['Date']]
nerissa['hour'] = [int(t[:2]) for t in nerissa['Time']]
nerissa['minute'] = [int(t[2:4]) for t in nerissa['Time']]
nerissa['datetime']= pd.to_datetime(nerissa[['year', 'month', 'day', 'hour', 'minute']]) #datetime variable
nerissa = nerissa.rename(columns={'Latitude': 'lat','Longitude': 'lon','Depth':'depth',})
nerissa = nerissa[['datetime','lat', 'lon', 'depth', 'CDOM','Station_ID']]
nerissa = nerissa[nerissa['depth'] <=50] #848563 ->61711
nerissa['experiment']='SoCalPlumeEx2012'
nerissa['source']='BCO-DMO'
nerissa['investigator']='Raphael M. Kudela'
nerissa['url']='https://www.bco-dmo.org/dataset/537627'

yfin= pd.read_excel(r'C:\Users\gianna.milton\Documents\Python\CDOM\BCO-DMO\YellowFin_CTD.xlsx')
yfin['Date'] = yfin['Date'].astype(str)
yfin['month'] = [int(t[4:6]) for t in yfin['Date']]
yfin['day'] = [int(t[6:8]) for t in yfin['Date']]
yfin['year'] = [int(t[0:4]) for t in yfin['Date']]
yfin['datetime']= pd.to_datetime(yfin[['year', 'month', 'day']]) #datetime variable
yfin = yfin.rename(columns={'Latitude': 'lat','Longitude': 'lon','Depth':'depth','Turbidity':'turbidity'})
yfin = yfin[['datetime','lat', 'lon', 'depth', 'CDOM','turbidity','Station_ID']]
yfin['experiment']='SoCalPlumeEx2012'
yfin['source']='BCO-DMO'
yfin['investigator']='Raphael M. Kudela'
yfin['url']='https://www.bco-dmo.org/dataset/537818'

GoMX4= pd.read_excel(r'C:\Users\gianna.milton\Documents\Python\CDOM\BCO-DMO\discrete_samples_concat.xlsx')
GoMX4['Date'] = GoMX4['Date'].astype(str)
GoMX4['Time'] = GoMX4['Time'].astype(str)
GoMX4['datetime'] = pd.to_datetime(GoMX4['Date'] + ' ' + GoMX4['Time'])
GoMX4 = GoMX4.rename(columns={'Latitude':'lat','Longitude':'lon','Turbidity':'turbidity','Cruise':'cruiseid','Station':'Station_ID',
                              'Sample_Depth':'depth','wetCDOM':'CDOM'})
GoMX4 = GoMX4[['datetime','lat', 'lon', 'depth', 'CDOM','turbidity','Station_ID','cruiseid']]
GoMX4['experiment']='nGOMx acidification'
GoMX4['source']='BCO-DMO'
GoMX4['investigator']='Wei-Jun Cai'
GoMX4['url']='https://www.bco-dmo.org/dataset/772513'


reu_oto = pd.read_excel(r'C:\Users\gianna.milton\Documents\Python\CDOM\BCO-DMO\combined.xlsx')
reu_oto = reu_oto.rename(columns={'date_time': 'datetime','Water_Depth':'depth','Latitude':'lat','Longitude': 'lon','Station':'Station_ID'})
reu_oto = reu_oto[['datetime','lat', 'lon', 'depth', 'CDOM','Station_ID']]
reu_oto = reu_oto[reu_oto['depth'] != 'nd']
reu_oto = reu_oto[reu_oto['depth'] <=50] 
reu_oto = reu_oto[reu_oto['CDOM'] != 'nd']
reu_oto['experiment']='REU-OTO'
reu_oto['source']='BCO-DMO'
reu_oto['investigator']='Lisa Campbell'
reu_oto['url']='https://www.bco-dmo.org/dataset/753882'

#scanfish: i deleted some columns from the raw xlsx dataset just so that it takes up less room 
scanfish = pd.read_excel(r'C:\Users\gianna.milton\Documents\Python\CDOM\BCO-DMO\scanfish_opc.xlsx')
scanfish['datetime']= pd.to_datetime(scanfish['ISO_DateTime_UTC']) #datetime variable
scanfish = scanfish[['datetime','lat', 'lon', 'depth', 'CDOM']]
scanfish = scanfish[scanfish['depth'] <=50] 
scanfish = scanfish[scanfish['CDOM'] != 'nd']
scanfish['experiment']='GoMX - DHOS'
scanfish['source']='BCO-DMO'
scanfish['investigator']=' Michael R. Roman'
scanfish['url']='https://www.bco-dmo.org/dataset/746081'

harvey = pd.read_excel(r'C:\Users\gianna.milton\Documents\Python\CDOM\BCO-DMO\oct_2017_discrete.xlsx')
harvey['datetime']= pd.to_datetime(harvey['DateTime']) #datetime variable
harvey = harvey.rename(columns={'Cruise':'cruiseid','Depth':'depth','Latitude':'lat','Longitude': 'lon','Station':'Station_ID',
                                'wetCDOM':'CDOM','Turbidity':'turbidity'})
harvey = harvey[['datetime','lat', 'lon', 'depth', 'CDOM','turbidity','Station_ID','cruiseid']]
harvey = harvey[harvey['CDOM'] != 'nd']
harvey = harvey[harvey['depth'] <=50] 
harvey['experiment']='HarveyCarbonCycle'
harvey['source']='BCO-DMO'
harvey['investigator']='Brian Roberts'
harvey['url']='https://www.bco-dmo.org/dataset/844721'

hrr=pd.read_excel(r'C:\Users\gianna.milton\Documents\Python\CDOM\BCO-DMO\HRR_ctd_2017.xlsx')
hrr['datetime']= pd.to_datetime(hrr['ISO_DateTime_UTC']) #datetime variable
hrr = hrr.rename(columns={'wetCDOM':'CDOM','depSM':'depth','lat_decdeg':'lat','lon_decdeg': 'lon','station':'Station_ID'})
hrr = hrr[['datetime','lat', 'lon', 'depth', 'CDOM','Station_ID']]
hrr = hrr[hrr['depth'] <=50] 
hrr['experiment']='RAPID HRR'
hrr['source']='BCO-DMO'
hrr['investigator']='Lisa Campbell'
hrr['url']='https://www.bco-dmo.org/dataset/809428'

rapid=pd.read_excel(r'C:\Users\gianna.milton\Documents\Python\CDOM\BCO-DMO\CTD.xlsx')
rapid['datetime']= pd.to_datetime(rapid['Start_ISO_DateTime_UTC']) #datetime variable
rapid = rapid.rename(columns={'Cruise_ID':'cruiseid','Station':'Station_ID','Depth': 'depth','Latitude':'lat','Longitude': 'lon',
                              'Fluorescence_WET_CDOM':'CDOM'})
rapid = rapid[['datetime','lat', 'lon', 'depth', 'CDOM','Station_ID','cruiseid']]
rapid = rapid[rapid['depth'] <=50] 
rapid['experiment']='RAPID Plankton'
rapid['source']='BCO-DMO'
rapid['investigator']='Beth Stauffer'
rapid['url']='https://www.bco-dmo.org/dataset/827969'

dfs=[GoMX1,GoMX2,GoMX3,nerissa,yfin,GoMX4,reu_oto,scanfish,harvey,hrr,rapid]
bcodmo_cdom = pd.concat(dfs).reset_index(drop=True)
bcodmo_cdom = bcodmo_cdom.rename(columns={'CDOM':'cdom'})
bcodmo_cdom['datetime']= pd.to_datetime(bcodmo_cdom['datetime'],utc=True) #datetime variable
bcodmo_cdom['datetime'] = bcodmo_cdom['datetime'].dt.tz_localize(None)

shp = gpd.read_file(r'C:\Users\gianna.milton\Documents\Python\Shapefiles\combined_coastline.shp')
gdf = gpd.GeoDataFrame(df_long, geometry=gpd.points_from_xy(df_long.lon, df_long.lat), crs="EPSG:4269")
gdf = gdf.to_crs(shp.crs)
df_long = gpd.sjoin(gdf, shp, how="inner", predicate="within")
columns_to_drop = ['geometry', 'index_right', 'merge_id']
df_long = df_long.drop(columns=columns_to_drop)
df_long= df_long.reset_index(drop=True)

fig=plt.figure(figsize=(12, 12))
axs1=fig.add_subplot(1,1,1,projection= cartopy.crs.PlateCarree())
axs1.add_feature(cfeature.LAND)
axs1.add_feature(cfeature.OCEAN)
axs1.add_feature(cfeature.BORDERS)
im=axs1.scatter(df_long.lon,df_long.lat,s=10)
gl=axs1.gridlines(linewidth=0.2,color='grey',alpha=0.5,linestyle='-',
                draw_labels=True, x_inline= False,y_inline=False)
gl.xformatter=LONGITUDE_FORMATTER
gl.yformatter=LATITUDE_FORMATTER
gl.top_labels = False    # Disable top labels
gl.right_labels = False  # Disable right labels