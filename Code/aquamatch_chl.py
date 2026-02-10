# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 13:40:20 2026
aquamatch_qc
format and organize Aquamatch data with appropriate metadata and flags
@author: gianna.milton
"""
import pandas
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)
warnings.filterwarnings('ignore', category=FutureWarning)
import geopandas as gpd


# start
aqua_match1 = pd.read_excel(r'C:\Users\gianna.milton\Documents\Python\one off cruises\AquaMatch_chl.xlsx') #read in datafile

#to remove inland data, since only coastal data is needed, use shapefile from U.S. regional Fishery Managment Councils 
#link to shapefile: http://arcgis.com/home/item.html?id=84cbbc49011b49e1b959a7b6a7a0d339
shp = gpd.read_file('20210609_fishery_management_council_regions.shp')
gdf = gpd.GeoDataFrame(aqua_match1, geometry=gpd.points_from_xy(aqua_match1.lon, aqua_match1.lat), crs="EPSG:4269")
gdf = gdf.to_crs(shp.crs)
aqua_match1 = gpd.clip(gdf,shp)

#reduce dataframe to only needed columns for easier manipulation and rename columns to match seabass file structure
aqua_match1=aqua_match1[[ 'OrganizationIdentifier','field_flag','tier', 'harmonized_utc', 'harmonized_discrete_depth_value',  'harmonized_value', 'lat','lon']]
aqua_match1=aqua_match1.rename(columns={'OrganizationIdentifier':'station','harmonized_utc':'datetime','harmonized_discrete_depth_value':'depth',
                                      'harmonized_value':'chl','field_flag':'flag'})
aqua_match1['datetime'] = pd.to_datetime(aqua_match1['datetime']) #ensure datetime column is in pandas datetime format and datatype 

#for this project, only want data from 2000 thru 2024 
aqua_match1 = aqua_match1[(aqua_match1['datetime'] >= pd.to_datetime('2000-01-01 00:00:00').tz_localize('UTC')) & (aqua_match1['datetime'] <= pd.to_datetime('2025-01-01 00:00:00').tz_localize('UTC'))]

#Fill in affiliation using the station code from the water quality website:https://www.waterqualitydata.us/provider/STORET/
aqua_match1['affiliations']=np.nan
aqua_match1.affiliations[(aqua_match1['station'] =='21FLKWAT') | (aqua_match1['station'] =='21FLKWAT_WQX')] = 'Florida Lakewatch'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLKNMS_WQX')] = 'FLORIDA KEYS NATIONAL MARINE SANCTUARY'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLFMRI')] = 'Florida Fish & Wildlife C C / Marine Research Institute'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLFTM_WQX')] = 'FL Dept. of Environmental Protection, South District'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLDADE_WQX') | (aqua_match1['station'] =='21FLDADE')] = 'Dade Environmental Resource Management'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLBBAP_WQX')] = 'FDEP BISCAYNE BAY AQUATIC PRESERVES'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLCOMI_WQX')] = 'CITY OF MARCO ISLAND'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLBRA')] = 'Biological Research Associates'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLNAPL_WQX')] = 'City of Naples'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLEECO_WQX')] = 'Lee County'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLCHAR_WQX') | (aqua_match1['station'] =='21FLCHAR')] = 'FDEP Charlotte Harbor Aquatic/Buffer Preserves'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLPBCH_WQX') | (aqua_match1['station'] =='21FLPBCH')] = 'Palm Beach County Environmental Resources Managemnt'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLLOX_WQX') | (aqua_match1['station'] =='21FLLOX')] = 'Loxahatchee River District'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLSARA') | (aqua_match1['station'] =='21FLSARA_WQX')] = 'Sarasota County Environmental Services'
aqua_match1.affiliations[(aqua_match1['station'] =='11NPSWRD_WQX')] = 'National Park Service Water Resources Division'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLMANA_WQX') | (aqua_match1['station'] =='21FLMANA')] = 'Manatee County Environmental Management Dept'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLHILL_WQX')] = 'Environmental Protection Commission of Hillsborough County'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLPDEM') | (aqua_match1['station'] =='21FLPDEM_WQX')] = 'Pinellas County Dept. of Environmental Management'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLBSG')] = 'City of Tampa Bay Study Group'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLCOSP_WQX')] = 'City of St Petersburg'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLGW_WQX')] = 'FL Dept. of Environmental Protection'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLCEN_WQX')] = 'Fl Dept. of Environmental Protection, Central District'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLCEN_WQX')] = 'Fl Dept. of Environmental Protection, Central District'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLBREV_WQX') | (aqua_match1['station'] =='21FLBREV')] = 'Brevard County Stormwater Utility Department'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLPCSW') | (aqua_match1['station'] =='21FLPCSW_WQX')] = 'PROJECT COAST - Southwest Florida Water Management District'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLA_WQX')] = 'FL Dept. of Environmental Protection, Northeast District'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLANER') | (aqua_match1['station'] =='21FLANER_WQX')] = 'FDEP APALACHICOLA NATIONAL ESTUARINE RESEARCH RESERVE'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLNWFD')] = 'Northwest Florida Water District'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLPNS_WQX')] = 'FL Dept. of Environmental Protection, Northwest District'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLGTM') | (aqua_match1['station'] =='21FLGTM_WQX')] = 'GUANA TOLOMATO MATANZAS NATIONAL ESTUARINE RESEARCH RESERVE'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLPNS_WQX')] = 'ALABAMA DEPT. OF ENVIRONMENTAL MANAGEMENT'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLPNS_WQX')] = 'National Health and Environmental Effect Research-NHEERL'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLGBO1')] = 'National Health and Environmental Effect Research-NHEERL'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLECUA_WQX')] = 'EMERALD COAST UTLITIES AUTHORITY'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLESC_WQX')] = 'ESCAMBIA COUNTY'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLCBA_WQX') | (aqua_match1['station'] =='21FLCBA')] = 'Choctawhatchee Basin Alliance'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLNUTT_WQX')] = 'NUTTER AND ASSOCIATES'
aqua_match1.affiliations[(aqua_match1['station'] =='21FLCMP_WQX')] = 'FL Dept. of Environmental Protection, OCEC '
aqua_match1.affiliations[(aqua_match1['station'] =='21FLFRYD_WQX')] = 'FRYDENBORG ECOLOGIC LLC'
aqua_match1.affiliations[(aqua_match1['station'] =='21DELAWQ_WQX')] = 'Delaware Dept Natural Resources &amp; Environmental Control'

#from the aquamatch metadata file: chl_a workflow, Flags are used to check if data is reasonable (flag = 0), suspect (flag = 1), or inconclusive (flag = 2)
#flag defs from this website:https://portal.edirepository.org/nis/metadataviewer?packageid=edi.1756.2
#Remove bad flags 
aqua_match1 = aqua_match1[aqua_match1['flag'] != 1]
aqua_match1 = aqua_match1[aqua_match1['flag'] != 2] 
aqua_match1 = aqua_match1[aqua_match1['tier'] != 2] 

#only want points above 150 meters for algorithm development
aqua_match1 = aqua_match1[aqua_match1['depth'] <=150]
    
#while the aquamatch doi mentions HPLC, there is no definitive way of distinguishing HPLC from non HPLC, so assume no HPLC
aqua_match1['HPLC']=1
#triplicate flag 
counts_series = aqua_match1[['depth','datetime','lat','lon']].value_counts() #count how many unique depth, datetime, lat, and lons there are
counts_df = counts_series.reset_index(name='freq_uniq') #create new column where each unique entry aso shows howmany times that entry was recorded 
aqua_match1 = pd.merge(aqua_match1, counts_df, on=['depth','datetime','lat','lon'], how='left') #add frequency column to original dataframe

#sometimes, triplicate specific times are recorded (ex: 3:00, 3:05, 3:10 ), so also check for unique datehour entries
aqua_match1['date_hour'] = aqua_match1['datetime'].dt.strftime('%Y-%m-%d %H')
counts_series = aqua_match1[['depth','date_hour','lat','lon']].value_counts() #count how many unique datehour, lat, and lons there are
counts_df = counts_series.reset_index(name='freq_hour')
aqua_match1 = pd.merge(aqua_match1, counts_df, on=['depth','date_hour','lat','lon'], how='left') #add frequency column to original dataframe

aqua_match1['triplicate'] = 1 #assume bad unless otherwise said
aqua_match1.loc[aqua_match1['freq_uniq'] == 3, 'triplicate'] = 0 #if there are exactly 3 unique datetime, lat, and lons, assume triplicate
aqua_match1.loc[(aqua_match1['freq_uniq'] == 1) &(aqua_match1['freq_hour'] == 3), 'triplicate'] = 0 #if 1 unique datetime BUT 3 unique date_hours, assume triplicate

#reduce columns to only needed ones
aqua_match1=aqua_match1[['station', 'datetime', 'depth','chl', 'lat', 'lon', 'affiliations','HPLC','triplicate']].reset_index(drop=True)
aqua_match1['source']='AquaMatch'
aqua_match1['investigators']= 'Brousil, Matthew R'
aqua_match1['url']='https://doi.org/10.6073/pasta/2f750544112e5408928dd9a61e6ace30'
aqua_match1['datetime'] = aqua_match1['datetime'].dt.tz_localize(None) 

aqua_match1.to_excel('aquamatch_chl_qc.xlsx', index = False)

