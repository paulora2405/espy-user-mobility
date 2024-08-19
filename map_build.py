#!/bin/env python3
import numpy as np
import pandas as pd

COORD_LOWER_BOUND, COORD_UPPER_BOUND = 0, 100

# The pair of coordinates correspond to two points on the map,
# which are used to create a bounding box rectangle.
# ---------------
# | 1,0   -> 1,1  this one
# |
# | 0,0 <-   0,1  that other one
# ---------------
# Joinville
BOUNDING_BOX_START = {"Latitude": -26.200431, "Longitude": -48.748822}  # TOP RIGHT coordinates
BOUNDING_BOX_STOP = {"Latitude": -26.376193, "Longitude": -48.945546}  # BOTTOM LEFT coordinate
# How Longitude (x) and Latitude (y) work in a x,y plane
# y
# | +1,-1   +1,+0   +1,+1
# |
# | +0,-1   +0,+0   +1,+0
# |
# | -1,-1   -1,+0   +1,-1
# ----------------------- x


def create_edge_servers_df(csv_filepath="./datasets/geo-dataset-724.csv", bounding_box_normalization=True) -> pd.DataFrame:
    """Returns a dataframe of Latitude and Longitude coordinates of points,
    which will be transformed to Edge Servers, seem as grid and basestations will already be created.
    The coordinates can be mapped 1 to 1 from square grid to hexagonal grid.
    """
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
    df = pd.read_csv(csv_filepath, names=headers)

    df = df.loc[df.Longitude <= BOUNDING_BOX_START["Longitude"]]
    df = df.loc[df.Latitude <= BOUNDING_BOX_START["Latitude"]]

    df = df.loc[df.Longitude >= BOUNDING_BOX_STOP["Longitude"]]
    df = df.loc[df.Latitude >= BOUNDING_BOX_STOP["Latitude"]]

    df = df.reset_index(drop=True)

    df_norm = df.copy()

    LAT_MIN, LAT_MAX = 0.0, 0.0
    LON_MIN, LON_MAX = 0.0, 0.0
    if bounding_box_normalization:
        LON_MIN, LON_MAX = BOUNDING_BOX_STOP["Longitude"], BOUNDING_BOX_START["Longitude"]
        LAT_MIN, LAT_MAX = BOUNDING_BOX_STOP["Latitude"], BOUNDING_BOX_START["Latitude"]
    else:
        LON_MIN, LON_MAX = df_norm.Longitude.min(), df_norm.Longitude.max()
        LAT_MIN, LAT_MAX = df_norm.Latitude.min(), df_norm.Latitude.max()

    df_norm.Longitude = (df_norm.Longitude - LON_MIN) / (LON_MAX - LON_MIN) * (
        COORD_UPPER_BOUND - COORD_LOWER_BOUND
    ) + COORD_LOWER_BOUND
    df_norm.Longitude = df_norm.Longitude.astype(np.int64)

    df_norm.Latitude = (df_norm.Latitude - LAT_MIN) / (LAT_MAX - LAT_MIN) * (
        COORD_UPPER_BOUND - COORD_LOWER_BOUND
    ) + COORD_LOWER_BOUND
    df_norm.Latitude = df_norm.Latitude.astype(np.int64)

    df_dedup = df_norm.drop_duplicates(subset=["Longitude", "Latitude"], ignore_index=True)
    df_dedup = df_dedup[["Longitude", "Latitude"]]

    return translate_to_hexagonal_grid(df_dedup)


def create_points_of_interest_df(bounding_box_normalization=True) -> pd.DataFrame:
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

    LAT_MIN, LAT_MAX = 0.0, 0.0
    LON_MIN, LON_MAX = 0.0, 0.0
    if bounding_box_normalization:
        LON_MIN, LON_MAX = BOUNDING_BOX_STOP["Longitude"], BOUNDING_BOX_START["Longitude"]
        LAT_MIN, LAT_MAX = BOUNDING_BOX_STOP["Latitude"], BOUNDING_BOX_START["Latitude"]
    else:
        LAT_MIN, LAT_MAX = df_poi.Latitude.min(), df_poi.Latitude.max()
        LON_MIN, LON_MAX = df_poi.Longitude.min(), df_poi.Longitude.max()

    df_poi.Longitude = (df_poi.Longitude - LON_MIN) / (LON_MAX - LON_MIN) * (
        COORD_UPPER_BOUND - COORD_LOWER_BOUND
    ) + COORD_LOWER_BOUND
    df_poi.Longitude = df_poi.Longitude.astype(np.int64)

    df_poi.Latitude = (df_poi.Latitude - LAT_MIN) / (LAT_MAX - LAT_MIN) * (
        COORD_UPPER_BOUND - COORD_LOWER_BOUND
    ) + COORD_LOWER_BOUND
    df_poi.Latitude = df_poi.Latitude.astype(np.int64)

    return translate_to_hexagonal_grid(df_poi)


def translate_to_hexagonal_grid(df: pd.DataFrame) -> pd.DataFrame:
    def add_one_to_odd_latitude(row):
        if row["Latitude"] % 2 != 0:
            if row["Longitude"] + 1 <= COORD_UPPER_BOUND:
                return row["Longitude"] + 1
            else:
                return row["Longitude"] - 1
        else:
            return row["Longitude"]

    if "Longitude" in df.columns and "Latitude" in df.columns:
        df["Longitude"] = df["Longitude"] * 2
        df["Longitude"] = df.apply(add_one_to_odd_latitude, axis=1)
        return df
    else:
        raise Exception("Dataframe does not contain both 'Latitude' and 'Longitude' columns")


def to_tuple_list(df: pd.DataFrame) -> list[tuple[int, int]]:
    if "Longitude" in df.columns and "Latitude" in df.columns:
        return list(zip(df["Longitude"], df["Latitude"]))
    else:
        raise Exception("Dataframe does not contain both 'Latitude' and 'Longitude' columns")


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    import EdgeSimPy.edge_sim_py as espy
    from scenario_build import create_base_stations, create_grid

    df_edgeservers = create_edge_servers_df("./datasets/geo-dataset-724.csv")
    df_pois = create_points_of_interest_df()
    grid = create_grid()
    create_base_stations(grid)
    base_stations = espy.BaseStation.all()
    bs_coords = [b.coordinates for b in base_stations]
    # Create a figure and axis object
    fig, ax = plt.subplots()
    plot_size = 12
    fig.set_size_inches(plot_size, plot_size)
    # Plot the coordinates as a map
    for i, coord in enumerate(df_pois.Latitude):
        ax.plot([df_pois.Longitude[i]], [df_pois.Latitude[i]], "o", markersize=8, color="red")
    for i, coord in enumerate(df_edgeservers.Latitude):
        ax.plot([df_edgeservers.Longitude[i]], [df_edgeservers.Latitude[i]], "o", markersize=3, color="blue")
    for coord in bs_coords:
        ax.plot([coord[0]], [coord[1]], "o", markersize=1, color="green")
    # Set the axis labels
    ax.set_xlabel("Normalized Longitude")
    ax.set_ylabel("Normalized Latitude")
    # Show the plot
    plt.tight_layout(pad=0.1)
    plt.show()
