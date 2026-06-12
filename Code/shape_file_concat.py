# -*- coding: utf-8 -*-
"""
Created on Thu Feb 12 11:33:38 2026
Code for developing shapefile used in coastal_chlorophyll data by combining two shapefiles 
@author: gianna.milton
"""
import geopandas as gpd
import pandas as pd

#1. Marine ecosystems: this shapefile includes all coastal north american zones. however, it has less inland waters than desired, so need to comine with below shapefile
#link to shapefile: https://www.cec.org/north-american-environmental-atlas/marine-ecoregions/

#2. U.S. regional Fishery Managment Councils: while this shapefile is only the us, it includes more inland regions. combine with above. 
#link to shapefile: http://arcgis.com/home/item.html?id=84cbbc49011b49e1b959a7b6a7a0d339

def combine_coastal_shapefiles(na_shapefile_path, usa_shapefile_path, output_path):
    #read in both shapefiles useing geopandas
    gdf_na = gpd.read_file(na_shapefile_path) #shape file to north american
    gdf_usa = gpd.read_file(usa_shapefile_path) #shape file to usa fisheries region

    #check and align Coordinate Reference Systems (CRS)
    if gdf_na.crs != gdf_usa.crs:
        gdf_usa = gdf_usa.to_crs(gdf_na.crs)
    else:
        print("CRS matches")

    #combine the dataframes
    combined = pd.concat([gdf_na[['geometry']], gdf_usa[['geometry']]]) #combine by geometry
    combined['merge_id'] = 1
    dissolved_result = combined.dissolve(by='merge_id') #aggregate spatial geometries by merge_id
    dissolved_result.to_file(output_path) #output as shapefile 

na_file = r'C:\Users\gianna.milton\Documents\Python\Shapefiles\marineecoregions_shapefile\marineecoregions_shapefile\NA_Marine_Ecoregions_2008\data\Marine_Ecoregions_updated.shp'
usa_file = r'C:\Users\gianna.milton\Documents\Python\Shapefiles\Hawaii_Caribbean\20210609_fishery_management_council_regions.shp'

output_file = r'C:\Users\gianna.milton\Documents\Python\Shapefiles\combined_coastline.shp'

combine_coastal_shapefiles(na_file, usa_file, output_file)
