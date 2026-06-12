# -*- coding: utf-8 -*-
"""
Created on Tue May  6 16:13:27 2025

@author: gianna.milton
Title: SeaBass_flags
Description: create functions that will read in SeaBass dataframe and create datatype flags
For Datatype flags, 0= in vitro, 1 = in vivo, 2 = undetermined 
"""
import pandas
import numpy as np
import pandas as pd

def sb_flags(df): #df is dataframe of variables from SeaBass
    
    def measure(lat1, lon1, lat2, lon2): #function to convert lat/lon to km. used to measure horizontal distance between measurements 
        R = 6378.137 #Radius of earth in KM
        #calculate the difference in lat and lon
        dLat = lat2 * np.pi / 180 - lat1 * np.pi / 180 
        dLon = lon2 * np.pi / 180 - lon1 * np.pi / 180
        #find difference in coordinate by applying Haversine formula
        a = np.sin(dLat/2) * np.sin(dLat/2) +np.cos(lat1 * np.pi/ 180) * np.cos(lat2 * np.pi / 180) *np.sin(dLon/2) * np.sin(dLon/2)
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        d = R * c;
        return d * 1000 # distance in kilometers
    
    a=df.copy()
    a['t_flag']=0 #initialize temporal resolution flag, 0=good, 1= bad (less than 1hour),2=flag (time is 0 i.e repeated)
    a['s_flag']=0 #initialize spatial resolution flag, 0=good, 1= bad (less than 2km),2=flag (lat/lon is 0 i.e repeated)
    a['data_flag'] = 0 #column to populate with datatypes as values for organization
    a['d_flag'] = 0 #initialize depth flag, 0=good, 1=bad (less than 5m), 2=flag
    a['decision'] = 2 #ultimate decision flag inidcating whether to keep or toss data point (0=good, 1=bad,2=flag)
    a.loc[a['data_type'].str.contains('bottle'), 'data_flag'] = 4
    a.loc[a['data_type'].str.contains('cast'), 'data_flag'] = 3 
    a.loc[a['data_type'].str.contains('flow_thru'), 'data_flag'] = 2
    a.loc[a['data_type'].str.contains('pigment'), 'data_flag'] = 1
    if 'station' not in a.columns: #if no station column, create empty station column
        a['station'] = np.nan
    if 1 in a.data_flag.values: #pigment
        p=a.loc[a['data_flag']==1].reset_index(drop=True)  #subset to all pigment data
        pp=p.station.unique() #identify number of stations 
        if p.station.empty or len(p)== len(pp): #if the metadata has no stations or every point is a unique station (i.e samples did not record station names)
            #time flag
            p['diff_time']= p['datetime'].diff() #calculate change in time
            p.t_flag=np.where(p['diff_time']< pd.to_timedelta('10 minutes'), 1, p.t_flag) #if delta t is less than 10 mins, flag as bad
            p.t_flag=np.where(p['diff_time']== pd.to_timedelta(0), 2, p.t_flag) #if 0, then just a repeat so not necessarily bad
            #space flag
            c=[]
            for i in range(len(p)-1): #calculate distance between measurment coordinates 
                meters=measure(float(p.lat[i]),float(p.lon[i]),float(p.lat[i+1]),float(p.lon[i+1]))
                c.append(meters) #append the length in kilometers
                #add nan on top to make the list shift down and fit
            c.insert(0,float('nan'))
            p['diff_space']=pd.Series(c) #append c as the diff_space 
            p.s_flag=np.where(p['diff_space']< 1000, 1, p.s_flag) #if the difference in space is less than 1km, flag as bad
            p.s_flag=np.where(p['diff_space']== 0, 2, p.s_flag) #if 0, then just a multi samples so not necessarily bad
            #add decicion flags tree
            p.decision[(p['t_flag'] ==0) & (p['s_flag'] ==0)] = 0 #if both good, then good
            p.decision[(p['t_flag'] ==1) & (p['s_flag'] ==1)] = 1 #if both bad, then flag bad
            p.decision[(p['t_flag'] ==1) & (p['s_flag'] ==0)] = 1 
            p.decision[(p['t_flag'] ==0) & (p['s_flag'] ==1)] = 2 
        else: #if the station column is NOT empty i.e stations are recorded or just 1 station, then we can measure how many samples are recorded per datetime next 
            p.sort_values(['datetime'], inplace=True)        
            pp=p.groupby(['datetime']).size() #Group by datetime i.e station and time
            pp=pd.DataFrame(pp)        
            pp_n=p.groupby(['datetime']).size().reset_index() #group again, this time with datetime in column to manipulate
            pp_n['diff_s'] = pp_n.datetime.diff() #caluclate change in time between each station
            pp_n=pd.DataFrame(pp_n)

            pp['diff_s']=pp_n['diff_s'].to_numpy() #populate pp dataframe with change in station time
            station_count = pp[0] #sample rate i.e how many samples per station
            time_count = pp['diff_s'] #time between stations
            p['diff_time'] = p['datetime'].map(time_count) #Map onto original dataframe so that dataframe has per sample change in time and station count
            p['num_s']=p['datetime'].map(station_count) #number of measurments per stations
            p.t_flag=np.where(p['diff_time']< pd.to_timedelta('10 minutes'), 1, p.t_flag) #if change in time less than 10 mins, flag as bad
            p.t_flag=np.where(p['num_s']>1000, 1, p.t_flag) #if the number of measurments at one station is too high i.e sample rate, flag it
            #calculate change in horizontal distance between samples
            c=[]
            for i in range(len(p)-1):
                meters=measure(float(p.lat[i]),float(p.lon[i]),float(p.lat[i+1]),float(p.lon[i+1]))
                c.append(meters)    
            c.insert(0,float('nan'))
            p['diff_space']=pd.Series(c)
            p.s_flag=np.where(p['diff_space']< 1000, 1, p.s_flag) #if the change is less than 1km, flag as bad 
            p.s_flag=np.where(p['diff_space']== 0, 0, p.s_flag) #if 0, then mark as good because diff_time and num_s will stop bad data points
            
            #depth flag
            if 'depth' in p.columns:
            #calculate change in depth between samples 
                depth_diff =abs(p.depth.diff())#calculate absolute change in depth
                p.loc[p[depth_diff<1].index,'d_flag']=1 #if the change in depth is less than 1 meter, flag as bad 
                p.loc[p[depth_diff==0].index,'d_flag']=2 #if the change in depth doesn't move, set as 2, diff_time and num_s will take care of it


            #add decicion flags tree
            p.decision[(p['t_flag'] ==0) & (p['s_flag'] ==0) & (p['d_flag']==0)] = 0 #if both good, then good
            p.decision[(p['t_flag'] ==0) & (p['s_flag'] ==0) & (p['d_flag']==1)] = 1 #if everything else is good but the depth is too short, flag as nad
            p.decision[(p['t_flag'] ==0) & (p['s_flag'] ==0) & (p['d_flag']==2)] = 0 #if everything else is good and depth repeats, good
            p.decision[(p['t_flag'] ==0) & (p['s_flag'] ==1) & (p['d_flag']==0)] = 2 #if time per station is ok and depth ok but space no, just flag
            p.decision[(p['t_flag'] ==0) & (p['s_flag'] ==1) & (p['d_flag']==1)] = 1 #if depth range bad, and space bad, no
            p.decision[(p['t_flag'] ==0) & (p['s_flag'] ==1) & (p['d_flag']==2)] = 2 
            p.decision[(p['t_flag'] ==1) & (p['s_flag'] ==0) & (p['d_flag']==0)] = 1 #IF TIME IS EVER BAD then the whole thing is bad
            p.decision[(p['t_flag'] ==1) & (p['s_flag'] ==0) & (p['d_flag']==1)] = 1
            p.decision[(p['t_flag'] ==1) & (p['s_flag'] ==0) & (p['d_flag']==2)] = 1
            p.decision[(p['t_flag'] ==1) & (p['s_flag'] ==1) & (p['d_flag']==0)] = 1
            p.decision[(p['t_flag'] ==1) & (p['s_flag'] ==1) & (p['d_flag']==1)] = 1
            p.decision[(p['t_flag'] ==1) & (p['s_flag'] ==1) & (p['d_flag']==2)] = 1
            if 'diff_space' in p.columns:
                p.decision[(pd.isna(p.diff_time)) & (pd.isna(p.num_s)) & (pd.isna(p.diff_space))] = 1 #if change in time, stations, and change in space all empty, flag bad
    else:
        p=pd.DataFrame() #if there is no pigmant data, make empty dataframe to append
    if 2 in a.data_flag.values: #flowthru
        f=a.loc[a['data_flag']==2].reset_index(drop=True) #subset all flowthru data 
        if not 'datetime' in f.columns: #IF no datetime (just one file SEA), then make datetime from pulling elements 
            if 'year' and 'month' and 'day' and 'hour' and 'minute' in f.columns: 
                time_test = pd.DataFrame({'year': f.get('year'),
                                    'month':  f.get('month'),
                                    'day':  f.get('day'),
                                    'hour': f.get('hour'),
                                    'minute': f.get('minute')})
                time=pd.to_datetime(time_test)
                f.insert(0,'datetime',time)#insert datetime column into datamatrix
            elif 'year' and 'month' and 'day' in f.columns:
                time_test = pd.DataFrame({'year': f.get('year'), 
                                    'month':  f.get('month'),
                                    'day':  f.get('day')})
                time=pd.to_datetime(time_test)
                f.insert(0,'datetime',time)#insert datetime column into datamatrix    
        else: #if dateteim in f.columns:
            f.sort_values(['datetime'], inplace=True)
        f['diff_time']= f['datetime'].diff() #calculate temporal resolution
        f.t_flag=np.where(f['diff_time']< pd.to_timedelta('10 minutes'), 1, f.t_flag)  #if change in time is less than 10 mins, then flag
        #calculate change in coordinates 
        c=[]
        for i in range(len(f)-1):
            meters=measure(float(f.lat[i]),float(f.lon[i]),float(f.lat[i+1]),float(f.lon[i+1]))
            c.append(meters)
        c.insert(0,float('nan'))
        f['diff_space']=pd.Series(c)
        f.s_flag=np.where(f['diff_space']< 1000, 1, f.s_flag) #if change is less than 1km, then flag 
        f.decision[(f['t_flag'] ==0) & (f['s_flag'] ==0)] = 0 #if both good, then good
        f.decision[(f['t_flag'] ==1) & (f['s_flag'] ==1)] = 1 #if both bad, then flag bad
        f.decision[(f['t_flag'] ==1) & (f['s_flag'] ==0)] = 1 
        f.decision[(f['t_flag'] ==0) & (f['s_flag'] ==1)] = 0 
    else:
        f=pd.DataFrame()
    if 3 in a.data_flag.values: #cast
        ca=a.loc[a['data_flag']==3].reset_index(drop=True) 
        cc=ca.station.unique() #gather all stations 
        if not 'datetime' in ca.columns: #if no datetime, populate manually 
            tt=pd.DataFrame()
            for i in range(len(ca)):
                time_test1 = pd.DataFrame({'year': [int(str(ca.start_date[i])[:4])], #pull datetime from metadata, start and endtime
                                    'month':  [int(str(ca.start_date[i])[4:6])],
                                    'day':  [int(str(ca.start_date[i])[6:8])],
                                    'hour': [int(str(ca.start_time[i])[:-11])],
                                    'minute':[int(str(ca.start_time[i])[-10:-8])],
                                    'second':[int(str(ca.start_time[i])[-7:-5])]})
                
                time_test2 = pd.DataFrame({'year': [int(str(ca.end_date[i])[:4])], 
                                    'month':  [int(str(ca.end_date[i])[4:6])],
                                    'day':  [int(str(ca.end_date[i])[6:8])],
                                    'hour': [int(str(ca.end_time[i])[:-11])],
                                    'minute':[int(str(ca.end_time[i])[-10:-8])],
                                    'second':[int(str(ca.end_time[i])[-7:-5])]})
                tt['end_time']=pd.to_datetime(time_test2)
                tt['start_time']=pd.to_datetime(time_test1)
                tt['change']=tt['end_time']-tt['start_time'] #calculate the change in time for each datetime
                datetime_test=np.where(tt.change[0] < pd.to_timedelta('10 minutes'),tt.end_time[0],np.nan) #if change is less than 1 day, populate with end time, otherwise put in nan
                #this is to stop cases where the start/end dates correspond with dates of the project, not dates the data was collected 
                datetime_test=pd.to_datetime(datetime_test.astype(str))
                ca.loc[i,'datetime']=datetime_test #add datetime to cast df
        else: #if datetime is in columns
            ca.sort_values(['datetime'], inplace=True)        
        #identify stations
        if ca.station.empty or len(ca)== len(cc):    #if the amount of stations is the same as rows, don't have to calculate sample rate
            ca['diff_time']= ca['datetime'].diff()
            ca.t_flag=np.where(ca['diff_time']< pd.to_timedelta('10 minutes'), 1, ca.t_flag) 
            ca.t_flag=np.where(ca['diff_time']== pd.to_timedelta(0), 2, ca.t_flag) 
            c=[]
            for i in range(len(ca)-1):
                meters=measure(float(ca.lat[i]),float(ca.lon[i]),float(ca.lat[i+1]),float(ca.lon[i+1]))
                c.append(meters)
            c.insert(0,float('nan'))
            ca['diff_space']=pd.Series(c)
            ca.s_flag=np.where(ca['diff_space']< 1000, 1, ca.s_flag) #if less than 1km, flag
            ca.s_flag=np.where(ca['diff_space']== 0, 2, ca.s_flag) 
            #add decicion flags
            ca.decision[(ca['t_flag'] ==0) & (ca['s_flag'] ==0)] = 0 #if both good, then good
            ca.decision[(ca['t_flag'] ==1) & (ca['s_flag'] ==1)] = 1 #if both bad, then flag bad
            ca.decision[(ca['t_flag'] ==1) & (ca['s_flag'] ==0)] = 1 #
            ca.decision[(ca['t_flag'] ==0) & (ca['s_flag'] ==1)] = 2 
        else: #if the station column is NOT empty i.e stations are recorded or just 1 station
            ca.sort_values(['datetime'], inplace=True)        
            cc=ca.groupby(['datetime']).size() #.reset_index()
            cc=pd.DataFrame(cc)
            cc_n=ca.groupby(['datetime']).size().reset_index()
            cc_n['diff_s'] = cc_n.datetime.diff()
            cc_n=pd.DataFrame(cc_n)

            cc['diff_s']=cc_n['diff_s'].to_numpy()
            station_count = cc[0] #sample rate i.e how many samples per station
            time_count = cc['diff_s'] #time between stations
            
            ca['diff_time'] = ca['datetime'].map(time_count) #change in time for easch station
            ca['num_s']=ca['datetime'].map(station_count) #number of measurments per stations
            #both of these above should trigger t_flag
            ca.t_flag=np.where(ca['diff_time']< pd.to_timedelta('1 hour'), 1, ca.t_flag) #if the change in time is less than 1 hour, flag. this is 1 hour rather than 10 mins because casts are usually bottle data so we can be less strict
            ca.t_flag=np.where(ca['num_s']>1000, 1, ca.t_flag) #if the number of measurments at one station is too high i.e sample rate, flag it
            if 'lat' in ca.columns:
                c=[]
                for i in range(len(ca)-1):
                    meters=measure(float(ca.lat[i]),float(ca.lon[i]),float(ca.lat[i+1]),float(ca.lon[i+1]))
                    c.append(meters) 
                c.insert(0,float('nan'))
                ca['diff_space']=pd.Series(c)
                ca.s_flag=np.where(ca['diff_space']< 1000, 1,ca.s_flag) #2000m ie 1km
                ca.s_flag=np.where(ca['diff_space']== 0, 0, ca.s_flag) #if 0, then mark as good because diff_time and num_s will stop bad flags
            else:
                ca['s_flag']=0 # if no lat and lon, shouldn't be flagged as bad. again, t_flags will stop any bad data
            
            #depth flag
            if 'depth' in ca.columns:
                depth_diff =abs(ca.depth.diff())
                ca.loc[ca[depth_diff<1].index,'d_flag']=1 #if the change in depth is too small, flag as bad
                ca.loc[ca[depth_diff==0].index,'d_flag']=2 #if the change in depth doesn't move, set as 2, diff_time and num_s will take care of it
            else:
                ca['d_flag'] =0#if no depths, then the flag is ok 

            #decition flag tree 
            ca.decision[(ca['t_flag'] ==0) & (ca['s_flag'] ==0) & (ca['d_flag']==0)] = 0 #if both good, then good
            ca.decision[(ca['t_flag'] ==0) & (ca['s_flag'] ==0) & (ca['d_flag']==1)] = 1 #if everything else is good but the depth is too short, flag as nad
            ca.decision[(ca['t_flag'] ==0) & (ca['s_flag'] ==0) & (ca['d_flag']==2)] = 0 #if everything else is good and depth repeats, good
            ca.decision[(ca['t_flag'] ==0) & (ca['s_flag'] ==1) & (ca['d_flag']==0)] = 2 #if time per station is ok and depth ok but space no, just flag
            ca.decision[(ca['t_flag'] ==0) & (ca['s_flag'] ==1) & (ca['d_flag']==1)] = 1 #if depth range bad, and space bad, no
            ca.decision[(ca['t_flag'] ==0) & (ca['s_flag'] ==1) & (ca['d_flag']==2)] = 2 
            ca.decision[(ca['t_flag'] ==1) & (ca['s_flag'] ==0) & (ca['d_flag']==0)] = 1 #IF TIME IS EVER BAD then the whole thing is bad
            ca.decision[(ca['t_flag'] ==1) & (ca['s_flag'] ==0) & (ca['d_flag']==1)] = 1
            ca.decision[(ca['t_flag'] ==1) & (ca['s_flag'] ==0) & (ca['d_flag']==2)] = 1
            ca.decision[(ca['t_flag'] ==1) & (ca['s_flag'] ==1) & (ca['d_flag']==0)] = 1
            ca.decision[(ca['t_flag'] ==1) & (ca['s_flag'] ==1) & (ca['d_flag']==1)] = 1
            ca.decision[(ca['t_flag'] ==1) & (ca['s_flag'] ==1) & (ca['d_flag']==2)] = 1
            #hyper specific tag for UFI since they don't have any changes in time, station, or space 
            if 'diff_space' in ca.columns:
                ca.decision[(pd.isna(ca.diff_time)) & (pd.isna(ca.num_s)) & (pd.isna(ca.diff_space))] = 1 #if change in time, stations, and change in space all empty, flag

    else:
        ca=pd.DataFrame()
    if 4 in a.data_flag.values: #bottle
        b=a.loc[a['data_flag']==4].reset_index(drop=True) #subset all data type bottle data 
        bb=b.station.unique()
        if not 'datetime' in b.columns: #if no datetime, populate
            tt=pd.DataFrame()
            for i in range(len(b)):
                time_test1 = pd.DataFrame({'year': [int(str(b.start_date[i])[:4])], #pull datetime from metadata
                                    'month':  [int(str(b.start_date[i])[4:6])],
                                    'day':  [int(str(b.start_date[i])[6:8])],
                                    'hour': [int(str(b.start_time[i])[:-11])],
                                    'minute':[int(str(b.start_time[i])[-10:-8])],
                                    'second':[int(str(b.start_time[i])[-7:-5])]})
                
                time_test2 = pd.DataFrame({'year': [int(str(b.end_date[i])[:4])], #pull datetime from metadata
                                    'month':  [int(str(b.end_date[i])[4:6])],
                                    'day':  [int(str(b.end_date[i])[6:8])],
                                    'hour': [int(str(b.end_time[i])[:-11])],
                                    'minute':[int(str(b.end_time[i])[-10:-8])],
                                    'second':[int(str(b.end_time[i])[-7:-5])]})
                tt['end_time']=pd.to_datetime(time_test2)
                tt['start_time']=pd.to_datetime(time_test1)
                tt['change']=tt['end_time']-tt['start_time']
                b.loc[i,'datetime'] =np.where(tt.change[0] < pd.to_timedelta('10 minutes'),tt.end_time[0],np.nan)
                datetime_test=b['datetime']
                datetime_test=pd.to_datetime(datetime_test.astype(str))
            b['datetime'] = datetime_test
        else:
            b.sort_values(['datetime'], inplace=True)        
        #identify stations
        if b.station.empty or len(b)== len(bb):    #if the amount of stations is the same as rows, don't have to calculate sample rate
            b['diff_time']= b['datetime'].diff()
            b.t_flag=np.where(b['diff_time']< pd.to_timedelta('10 minutes'), 1, b.t_flag) 
            b.t_flag=np.where(b['diff_time']== pd.to_timedelta(0), 2, b.t_flag) #if 0, then just a repeat so not necessarily bad
            c=[]
            for i in range(len(b)-1):
                meters=measure(float(b.lat[i]),float(b.lon[i]),float(b.lat[i+1]),float(b.lon[i+1]))
                c.append(meters)
            c.insert(0,float('nan'))
            b['diff_space']=pd.Series(c)
            b.s_flag=np.where(b['diff_space']< 1000, 1, b.s_flag) #1000m ie 1km
            b.s_flag=np.where(b['diff_space']== 0, 2, b.s_flag) #if 0, then just a repeat so not necessarily bad
            #add decicion flags
            b.decision[(b['t_flag'] ==0) & (b['s_flag'] ==0)] = 0 #if both good, then good
            b.decision[(b['t_flag'] ==1) & (b['s_flag'] ==1)] = 1 #if both bad, then flag bad
            b.decision[(b['t_flag'] ==1) & (b['s_flag'] ==0)] = 1 #if both bad, then flag bad
            b.decision[(b['t_flag'] ==0) & (b['s_flag'] ==1)] = 2 #if both bad, then flag bad
        else: #if the station column is NOT empty i.e stations are recorded or just 1 station
            b.sort_values(['datetime'], inplace=True)        
            bb=b.groupby(['datetime']).size() 
            bb=pd.DataFrame(bb)
            bb_n=b.groupby(['datetime']).size().reset_index()
            bb_n['diff_s'] = bb_n.datetime.diff()
            bb_n=pd.DataFrame(bb_n)

            bb['diff_s']=bb_n['diff_s'].to_numpy()
            station_count = bb[0] #sample rate i.e how many samples per station
            time_count = bb['diff_s'] #time between stations
            
            b['diff_time'] = b['datetime'].map(time_count) #change in time for easch station
            b['num_s']=b['datetime'].map(station_count) #number of measurments per stations
            #both of these above should trigger t_flag
            b.t_flag=np.where(b['diff_time']< pd.to_timedelta('1 hour'), 1, b.t_flag)
            b.t_flag=np.where(b['num_s']>1000, 1, b.t_flag) 
            if 'lat' in b.columns:
                c=[]
                for i in range(len(b)-1):
                    meters=measure(float(b.lat[i]),float(b.lon[i]),float(b.lat[i+1]),float(b.lon[i+1]))
                    c.append(meters) 
                    c.insert(0,float('nan'))
                b['diff_space']=pd.Series(c)
                b.s_flag=np.where(b['diff_space']< 1000, 1,b.s_flag) #2000m ie 1km
                b.s_flag=np.where(b['diff_space']== 0, 0, b.s_flag) #if 0, then mark as good because diff_time and num_s will stop bad flags
            else:
                b['s_flag']=0 #no lat and lon calculations
            
            #depth flag
            if 'depth' in b.columns:
                depth_diff =abs(b.depth.diff())
                b.loc[b[depth_diff<1].index,'d_flag']=1 #if the change in depth is too large, flag as bad
                b.loc[b[depth_diff==0].index,'d_flag']=2 #if the change in depth doesn't move, set as 2, diff_time and num_s will take care of it
            else:
                b['d_flag'] =0#if no depths, then the flag is ok 

            #add decicion flags
            b.decision[(b['t_flag'] ==0) & (b['s_flag'] ==0) & (b['d_flag']==0)] = 0 #if both good, then good
            b.decision[(b['t_flag'] ==0) & (b['s_flag'] ==0) & (b['d_flag']==1)] = 1 #if everything else is good but the depth is too short, flag as nad
            b.decision[(b['t_flag'] ==0) & (b['s_flag'] ==0) & (b['d_flag']==2)] = 0 #if everything else is good and depth repeats, good
            b.decision[(b['t_flag'] ==0) & (b['s_flag'] ==1) & (b['d_flag']==0)] = 2 #if time per station is ok and depth ok but space no, just flag
            b.decision[(b['t_flag'] ==0) & (b['s_flag'] ==1) & (b['d_flag']==1)] = 1 #if depth range bad, and space bad, no
            b.decision[(b['t_flag'] ==0) & (b['s_flag'] ==1) & (b['d_flag']==2)] = 2 
            b.decision[(b['t_flag'] ==1) & (b['s_flag'] ==0) & (b['d_flag']==0)] = 1 #IF TIME IS EVER BAD then the whole thing is bad
            b.decision[(b['t_flag'] ==1) & (b['s_flag'] ==0) & (b['d_flag']==1)] = 1
            b.decision[(b['t_flag'] ==1) & (b['s_flag'] ==0) & (b['d_flag']==2)] = 1
            b.decision[(b['t_flag'] ==1) & (b['s_flag'] ==1) & (b['d_flag']==0)] = 1
            b.decision[(b['t_flag'] ==1) & (b['s_flag'] ==1) & (b['d_flag']==1)] = 1
            b.decision[(b['t_flag'] ==1) & (b['s_flag'] ==1) & (b['d_flag']==2)] = 1

    else:
        b=pd.DataFrame()
    if 0 in a.data_flag.values: #other data type methods
        o=a.loc[a['data_flag']==0].reset_index(drop=True) 
        o.dropna(axis=1, how='all', inplace=True) #drop all empty columns 
        o.loc[o['data_type'].str.contains('drifter'), 'decision'] = 2 
        o.loc[o['data_type'].str.contains('mooring'), 'decision'] = 2
        o.loc[o['data_type'].str.contains('above_water'), 'decision'] = 0 #set above water as good 
        o.loc[o['data_type'].str.contains('matchup'), 'decision'] = 2

    else:
        o=pd.DataFrame()      

    aa=pd.DataFrame()
    aa=pd.concat([p,f,ca,b,o],axis=0).reset_index(drop=True) #concatinate all dataframes of datatypes together
    return aa

