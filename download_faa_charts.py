# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 18:09:10 2022

@author: e442282
"""
import argparse
import csv
import os
import pandas as pd
import requests
import wget
from tqdm import tqdm
from xml.etree import ElementTree


# Convert Metadata in XML to CSV format
# Convert XML to CSV (filter only for Airport Diagrams)
'''
This function converts the XML metadata file to a CSV file, filtering only for APD charts. The CSV file contains 
information about the airport diagrams, and will help in mapping the pdf_name to icao_ident.
'''
def convert_metaxml2csv(xmlfile_path):
    # PARSE XML
    xml = ElementTree.parse(xmlfile_path)

    # create CSV file
    csv_file_path = xmlfile_path.replace('.xml', '.csv')
    csvfile = open(csv_file_path, 'w', newline='', encoding='utf-8')
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(["airport_name", "icao_ident", "pdf_name"])

    # for each airport, filter only for APD charts
    for airport in xml.findall('.//state_code/city_name/airport_name'):
        for record in airport.findall('.//record'):
            chart_code = record.findtext("chart_code")
            if chart_code == 'APD':
                icao_ident = airport.attrib['icao_ident']
                airport_name = airport.attrib['ID']
                pdf_name = record.findtext("pdf_name")
                csvwriter.writerow([airport_name, icao_ident, pdf_name])

    csvfile.close()

    return csv_file_path


# Download FAA PDFs containing Airport Diagrams
'''
This function downloads the FAA PDFs containing Airport Diagrams. It reads the previously generated CSV file containing 
information about the airport diagrams and uses the data to generate the appropriate download links for each chart. 
The downloaded charts are saved in the specified target_folder.
'''
def download_airport_diagrams(xml_file_path, src_url, target_folder):
    # convert metadata xml to csv
    print("Converting metadata XML to CSV...")
    csv_file = convert_metaxml2csv(xml_file_path)
    print("Metadata XML to CSV conversion complete.")
    df = pd.read_csv(csv_file)

    # download pdfs
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    for index, row in tqdm(df.iterrows()):
        try:
            actual_name = row['pdf_name']
            renamed_name = row['icao_ident'] + '.PDF'
            target_path = os.path.join(target_folder, renamed_name)
            download_link = os.path.join(src_url, actual_name)

            wget.download(download_link, target_path)
        except Exception:
            pass

    # remove csv file
    os.remove(csv_file)


'''
This script downloads FAA digital terminal procedure publications (d-TPP) data, which contains metadata for all the 
digital terminal procedures published by the Federal Aviation Administration (FAA) for a specific AIRAC cycle. The script 
downloads the metadata XML file, generates a list of the charts available for that AIRAC cycle, and downloads only the 
Airport Diagrams. The downloaded charts are saved in the specified TargetFolder.
'''
if __name__ == '__main__':

    # Download FAA PDFs
    # Get Metadata XML for a specific cycle that has list of all FAA charts  
    parser = argparse.ArgumentParser(description='Download FAA Digital Terminal Procedure Publication (d-TPP) data')
    parser.add_argument('TargetFolder', type=str,nargs='?', default='FAA_Data',help='the folder to save the excel, geojson and PDF files')
    parser.add_argument('cycle_number', metavar='CYCLE_NUMBER', type=str, help='the AIRAC cycle number in YYMM format (e.g., 2201 for January 2022)')
    args = parser.parse_args()

    if not os.path.exists(args.TargetFolder):
        os.makedirs(args.TargetFolder)

    cycle_number = args.cycle_number
    xml_file_path = os.path.join(args.TargetFolder, 'd-tpp_Metafile.xml')

    pdfs_url_base = 'https://aeronav.faa.gov/d-tpp/{}'.format(cycle_number)

    print("Downloading metadata XML..."
    metadata_xml_url ='https://aeronav.faa.gov/d-tpp/{}/xml_data/d-tpp_Metafile.xml'.format(cycle_number)
    wget.download(metadata_xml_url,args.TargetFolder)
    print("Metadata XML download complete.")
     
    #Download only Airport Charts 
    print("Downloading PDFs...")
    pdfs_folder = os.path.join(args.TargetFolder, 'charts') 
    download_airport_diagrams(xml_file_path,pdfs_url_base,pdfs_folder)
    print("PDF download complete.")
    os.remove(xml_file_path)
