# -*- coding: utf-8 -*-
"""
Created on Mon Feb  2 15:33:17 2026
CalCOFI_chl
Load in and organize raw Calcofi bottle data and add flags
@author: gianna.milton
"""
import pandas
import pandas as pd
import warnings
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

#load in bottle data from CalCOFI website
Calcofi_btl = pd.read_excel(r'CalCOFI_Database_194903-202105_csv_16October2023\CalCOFI_Database_194903-202105_csv_16October2023\CalCOFI_Database_194903-202105_csv_16October2023\194903-202105_Bottle.xlsx')#chl files
Calcofi_btl = Calcofi_btl[['Cst_Cnt','Sta_ID', 'Depthm',  'ChlorA', 'Chlqua','R_Depth']] #reduce to only needed columns

#since bottle data has no datetime, lat, or lon, need to load in CalCOFI meta data and match up to bottle data
Calcofi_cast = pd.read_excel(r'CalCOFI_Database_194903-202105_csv_16October2023\CalCOFI_Database_194903-202105_csv_16October2023\CalCOFI_Database_194903-202105_csv_16October2023\194903-202105_Cast.xlsx')
Calcofi_cast = Calcofi_cast[['Cst_Cnt', 'Cruise', 'Sta_ID', 'Sta_Code', 'Date', 'Time', 'Lat_Dec', 'Lon_Dec', 'Data_Type']]

#create datetime column
Calcofi_cast['Date'] = Calcofi_cast['Date'].astype(str)
Calcofi_cast['Time'] = Calcofi_cast['Time'].astype(str)
Calcofi_cast['Date'] = Calcofi_cast['Date'].str.slice(0, 10)  # Keeps only 'YYYY-MM-DD' from date
datetime_str = Calcofi_cast['Date'] + ' ' + Calcofi_cast['Time'] 
Calcofi_cast['datetime'] = pd.to_datetime(datetime_str, errors='coerce') #put date and time together to form datetime column

#to match up the metadata (Calcofi_cast) with the bottle data (Calcofi_btl), match by cast since each cast is unique ( from website: All CalCOFI casts ever conducted, consecutively numbered)
Calcofi_btl['lat'] = Calcofi_btl['Cst_Cnt'].map(Calcofi_cast.set_index('Cst_Cnt')['Lat_Dec']) # map a lat column to where Cst_counts match, lat will be a copy of Lat_Dec
Calcofi_btl['lon'] = Calcofi_btl['Cst_Cnt'].map(Calcofi_cast.set_index('Cst_Cnt')['Lon_Dec']) #same for lon
Calcofi_btl['datetime'] = Calcofi_btl['Cst_Cnt'].map(Calcofi_cast.set_index('Cst_Cnt')['datetime']) #same for datetime

#subset data from 2000 onward and above 150 meters 
Calcofi_btl = Calcofi_btl[Calcofi_btl['datetime'] > pd.to_datetime('2000-01-01')]
Calcofi_btl=Calcofi_btl.loc[Calcofi_btl['Depthm']<=150].reset_index(drop=True) 

#Remove questionable and bad data (data flagged 8 and 9 in column chlqua)
Calcofi_btl = Calcofi_btl[Calcofi_btl['Chlqua'] != 9]
Calcofi_btl = Calcofi_btl[Calcofi_btl['Chlqua'] != 8]

#HPLC flag
#based on this: https://calcofi.info/index.php/field-work/bottle-sampling and this: https://calcofi.org/sampling-info/methods/  CALCOFI did not use hplc on their chl bottle data
Calcofi_btl['HPLC'] = 1 

#triplicate flag
counts_series = Calcofi_btl[['Cst_Cnt','Depthm','datetime','lat','lon']].value_counts() #count how many unique datehour, lat, and lons there are
counts_df = counts_series.reset_index(name='unique')
Calcofi_btl = pd.merge(Calcofi_btl, counts_df, on=['Cst_Cnt','Depthm','datetime','lat','lon'], how='left') #add frequency column to original dataframe
#based on inspecting the Calcofi_btl dataframe, no triplicates recorded (i.e. no unique values = 3)
Calcofi_btl['triplicate'] = 1

#rename columns to match seabass columns
Calcofi_btl=Calcofi_btl.rename(columns={'Cst_Cnt':'cast', 'Sta_ID':'station','ChlorA':'chl','Depthm':'depth'})
Calcofi_btl = Calcofi_btl[['datetime','lat', 'lon','chl', 'cast', 'station', 'depth','HPLC', 'triplicate']]

#add additional metadata
Calcofi_btl['identifier_product_doi'] = 'https://calcofi.org'
Calcofi_btl['source'] = 'CalCOFI'
Calcofi_btl=Calcofi_btl[['datetime', 'lat', 'lon', 'chl', 'depth','cast', 'station', 'HPLC','triplicate', 'identifier_product_doi', 'source']]


Calcofi_btl.to_excel('calcofi_chl_qc.xlsx', index = False)

