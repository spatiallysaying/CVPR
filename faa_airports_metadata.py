import pandas as pd
import os
import argparse
from tqdm import tqdm 
import wget 
import itertools  
from shapely.geometry import Point
import geopandas as gpd
from matplotlib import pyplot as plt
import requests


parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('TargetFolder', type=str, default='FAA_Data',
                    help='the folder to save the excel , geojson and PDF files')
args = parser.parse_args()

if not os.path.exists(args.TargetFolder):
    os.makedirs(args.TargetFolder)

excel_file_path = os.path.join(args.TargetFolder, 'all-airport-data.xlsx')
geojson_file_path = os.path.join(args.TargetFolder, 'FAA_Airports_Metadata.geojson')

# Download Excel file if not present
if not os.path.exists(excel_file_path):
    print('Downloading Excel file...')
    wget.download('https://adip.faa.gov/publishedAirports/all-airport-data.xlsx', excel_file_path)


def compLat_Long(deg, mins, secs, comp_dir):
    return (deg + (mins / 60) + (secs / 3600)) * comp_dir

def extract_DegMinSec(data):
    direction = {'N':1, 'S':-1, 'E': 1, 'W':-1}
    new = data.replace(u'°',' ').replace('\'',' ').replace('"',' ')
    secs=0
    deg, mins, comp_dir  = new.split()  
    deg=int(deg)
    mins=float(mins)
    comp_dir=direction[comp_dir]     
    return deg, mins, secs, comp_dir 

def extract_DD(lat_lon_str):
   deg, mins, secs, comp_dir=extract_DegMinSec(lat_lon_str)
   return compLat_Long(deg, mins, secs, comp_dir)

def extract_DegMinSec_2(data):
    direction = {'N':1, 'S':-1, 'E': 1, 'W':-1}
    comp_dir=data[-1]
    data = data[:-1]
    deg, mins,secs = data.split('-')
    deg = int(deg)
    mins= int(mins)
    secs= float(secs)
    comp_dir=direction[comp_dir]     
    return deg, mins, secs, comp_dir 

def extract_DD_2(lat_lon_str):
   deg, mins, secs, comp_dir=extract_DegMinSec_2(lat_lon_str)
   return compLat_Long(deg, mins, secs, comp_dir)

xl=pd.read_excel(excel_file_path,"Airports")
required_cols=['Facility Type','State Name', 'City','Name','ARP Latitude','ARP Longitude','Elevation','ICAO Id']
xl=xl[required_cols]
xl = xl.dropna(subset=['ICAO Id'])
xl[xl['Facility Type'] == 'AIRPORT'] 
print(xl.head(3))


xl['longitude'] = xl.apply(lambda x: extract_DD_2(x['ARP Longitude']), axis=1)
xl['latitude'] = xl.apply(lambda x: extract_DD_2(x['ARP Latitude']), axis=1)
print(xl.head())

arp_gdf = gpd.GeoDataFrame(xl, geometry=gpd.points_from_xy(xl.longitude, xl.latitude), crs="EPSG:4326")
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
# We restrict to North America.
ax = world[world.continent == 'North America'].plot(color='lightgray', edgecolor='white')
# We can now plot our ``GeoDataFrame``
arp_gdf.plot(ax=ax)
arp_gdf.to_file(geojson_file_path)
#os.remove(excel_file_path)
