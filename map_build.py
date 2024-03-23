#!/bin/env python3
import pandas as pd
import numpy as np

COORD_LOWER_BOUND, COORD_UPPER_BOUND = 0, 100


def setup_map_dataframe():
    headers = [
        "Radio",  # The generation of broadband cellular network technology (Eg. LTE, GSM)
        "MCC",  # Mobile country code. This info is publicly shared by International Telecommunication Union (link)
        "MNC",  # Mobile network code. This info is publicly shared by International Telecommunication Union (link)
        "LAC/TAC/NID",  # Location Area Code
        "CID",  # This is a unique number used to identify each Base transceiver station or sector of BTS
        "Changeable=0",  # The location is directly obtained from the telecom firm
        "Longitude",  # Longitude, is a geographic coordinate that specifies the east-west position of a point on the Earth's surface
        "Latitude",  # Latitude is a geographic coordinate that specifies the north–south position of a point on the Earth's surface.
        "Range",  # Approximate area within which the cell could be. (In meters)
        "Samples",  # Number of measures processed to get a particular data point
        "Changeable=1",  # The location is determined by processing samples
        "Created",  # When a particular cell was first added to database (UNIX timestamp)
        "Updated",  # When a particular cell was last seen (UNIX timestamp)
        "AverageSignal",  # To get the positions of cells, OpenCelliD processes measurements from data contributors. Each measurement includes GPS location of device + Scanned cell identifier (MCC-MNC-LAC-CID) + Other device properties (Signal strength). In this process, signal strength of the device is averaged. Most ‘averageSignal’ values are 0 because OpenCelliD simply didn’t receive signal strength values.
    ]
    df_og = pd.read_csv("../datasets/geo-dataset-724.csv", names=headers)

    # ---------------
    # | 0,0       0,1
    # |
    # | 1,0       1,1
    # ---------------
    # Latitude, Longitude (x, y)
    # ---------------
    # | +1,-1   +1,+0   +1,+1
    # |
    # | +0,-1   +0,+0   +1,+0
    # |
    # | -1,-1   -1,+0   +1,-1
    # ---------------
    # São Paulo
    coord_start = {"Latitude": -23.438893, "Longitude": -46.324440}
    coord_final = {"Latitude": -23.814428, "Longitude": -46.911431}

    # Joinville
    coord_start = {"Latitude": -26.200431, "Longitude": -48.748822}
    coord_final = {"Latitude": -26.376193, "Longitude": -48.945546}

    df = df_og.copy()

    df = df.loc[df.Latitude <= coord_start["Latitude"]]
    df = df.loc[df.Longitude <= coord_start["Longitude"]]

    df = df.loc[df.Latitude >= coord_final["Latitude"]]
    df = df.loc[df.Longitude >= coord_final["Longitude"]]

    df = df.reset_index(drop=True)

    df_norm = df.copy()

    # TODO normalize using coord_start and coord_end of joinville
    lat_min, lat_max = df_norm.Latitude.min(), df_norm.Latitude.max()
    df_norm.Latitude = (df_norm.Latitude - lat_min) / (lat_max - lat_min) * (
        COORD_UPPER_BOUND - COORD_LOWER_BOUND
    ) + COORD_LOWER_BOUND
    df_norm.Latitude = df_norm.Latitude.astype(np.int64)

    lon_min, lon_max = df_norm.Longitude.min(), df_norm.Longitude.max()
    df_norm.Longitude = (df_norm.Longitude - lon_min) / (lon_max - lon_min) * (
        COORD_UPPER_BOUND - COORD_LOWER_BOUND
    ) + COORD_LOWER_BOUND
    df_norm.Longitude = df_norm.Longitude.astype(np.int64)


def build_points_of_interest_dataframe() -> pd.DataFrame:
    # Points of interest
    poi = []
    poi_header = ["Latitude", "Longitude", "PeakStart", "PeakEnd", "Name"]
    poi.append([-26.263246003308190, -48.861225375722130, 7.5, 17.5, "Doller"])
    poi.append([-26.252990373029380, -48.854708408036230, 8, 17, "UDESC"])
    poi.append([-26.319269027247838, -48.855449473777610, 18, 22.5, "Unisociesc"])
    poi.append([-26.301289513710334, -48.844462116106380, 6, 8, "Terminal_Centro_Manha"])
    poi.append([-26.301289513710334, -48.844462116106380, 17, 19, "Terminal_Centro_Tarde"])
    poi.append([-26.273045033616377, -48.850776060285575, 6, 8, "Terminal_Norte_Manha"])
    poi.append([-26.273045033616377, -48.850776060285575, 17, 19, "Terminal_Norte_Tarde"])
    poi.append([-26.288328365610113, -48.810846717956740, 8, 17, "Tupy"])
    poi.append([-26.303556261544664, -48.848987585420980, 18, 23, "Shopping_Muller"])
    poi.append([-26.252303610588786, -48.852610343093396, 18, 23, "Shopping_Garten"])
    poi_data = {
        poi_header[0]: [pi[0] for pi in poi],
        poi_header[1]: [pi[1] for pi in poi],
        poi_header[2]: [pi[2] for pi in poi],
        poi_header[3]: [pi[3] for pi in poi],
        poi_header[4]: [pi[4] for pi in poi],
    }

    df_poi = pd.DataFrame(data=poi_data)
    return df_poi
