#!/bin/env python3
import numpy as np
import pandas as pd
from faker import Faker

from EdgeSimPy.edge_sim_py.components.point_of_interest import DAY_END_IN_MINUTES, DAY_START_IN_MINUTES

COORD_LOWER_BOUND, COORD_UPPER_BOUND = 0, 100
NUMBER_OF_POINT_OF_INTERESTS = 30
MIN_PEAK_DURATION_POI_MINUTES = 2 * 60
MAX_PEAK_DURATION_POI_MINUTES = 6 * 60


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

    df_translated = translate_to_hexagonal_grid(df_norm)
    df_translated = df_translated[["Longitude", "Latitude"]]
    df_translated = df_translated.drop_duplicates(subset=["Longitude", "Latitude"], ignore_index=True)

    return df_translated


def create_points_of_interest_df(bounding_box_normalization=True) -> pd.DataFrame:
    fake = Faker()

    # Points of interest
    poi = []
    poi_header = ["Latitude", "Longitude", "PeakStart", "PeakEnd", "Name"]
    # poi.append([-26.263246003308190, -48.861225375722130, 07.5, 17.5, "Doller"])
    # poi.append([-26.252990373029380, -48.854708408036230, 08.0, 17.0, "UDESC"])
    # poi.append([-26.319269027247838, -48.855449473777610, 18.0, 22.5, "Unisociesc"])
    # poi.append([-26.301289513710334, -48.844462116106380, 05.0, 08.0, "Terminal_Centro_Manha"])
    # poi.append([-26.301289513710334, -48.844462116106380, 17.0, 19.0, "Terminal_Centro_Tarde"])
    # poi.append([-26.273045033616377, -48.850776060285575, 05.0, 08.0, "Terminal_Norte_Manha"])
    # poi.append([-26.273045033616377, -48.850776060285575, 17.0, 19.0, "Terminal_Norte_Tarde"])
    # poi.append([-26.288328365610113, -48.810846717956740, 08.0, 17.0, "Tupy"])
    # poi.append([-26.303556261544664, -48.848987585420980, 18.0, 23.0, "Shopping_Muller"])
    # poi.append([-26.252303610588786, -48.852610343093396, 18.0, 23.0, "Shopping_Garten"])

    for i in range(NUMBER_OF_POINT_OF_INTERESTS):
        latitude = fake.random.uniform(BOUNDING_BOX_STOP["Latitude"], BOUNDING_BOX_START["Latitude"])
        longitude = fake.random.uniform(BOUNDING_BOX_STOP["Longitude"], BOUNDING_BOX_START["Longitude"])
        peak_start = fake.random.uniform(
            DAY_START_IN_MINUTES, DAY_END_IN_MINUTES - MAX_PEAK_DURATION_POI_MINUTES
        )  # Adjusted to ensure at least N units of time for peak duration
        peak_end = fake.random.uniform(
            peak_start + MIN_PEAK_DURATION_POI_MINUTES, min(peak_start + MAX_PEAK_DURATION_POI_MINUTES, DAY_END_IN_MINUTES)
        )  # Ensuring peak_end is at least N units after peak_start and within max duration
        name = f"POI_{chr(65 + i // 26)}{chr(65 + i % 26)}"
        poi.append([latitude, longitude, peak_start, peak_end, name])

    # transform hours to minutes
    # for p in poi:
    #     p[2] = int(p[2] * 60)
    #     p[3] = int(p[3] * 60)

    # create dictionary to create dataframe
    poi_data = {header: [p[i] for p in poi] for i, header in enumerate(poi_header)}

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


def to_tuple_list(df: pd.DataFrame) -> list[tuple[float, float]]:
    if "Longitude" in df.columns and "Latitude" in df.columns:
        return list(zip(df["Longitude"].astype(np.float64), df["Latitude"].astype(np.float64)))
    else:
        raise Exception("Dataframe does not contain both 'Latitude' and 'Longitude' columns")


def test_gen_plots():
    import EdgeSimPy.edge_sim_py as espy

    from .scenario_build import create_base_stations, create_grid
    from .servers import PROVIDER_SPECS

    df_edgeservers = create_edge_servers_df("./datasets/geo-dataset-724.csv")
    number_of_edge_servers = 0
    for provider in PROVIDER_SPECS:
        number_of_edge_servers += sum([spec["number_of_objects"] for spec in provider.get("edge_server_specs", [])])
    print(f"{number_of_edge_servers = }")
    df_edgeservers = df_edgeservers.sample(n=number_of_edge_servers).reset_index(drop=True)
    df_pois = create_points_of_interest_df()
    print(df_pois)

    grid = create_grid()
    create_base_stations(grid)

    base_stations = espy.BaseStation.all()
    bs_coords = [b.coordinates for b in base_stations]

    plot_grid(bs_coords, df_edgeservers, df_pois)
    plot_points_of_interest(df_pois)


def plot_grid(
    basestations_coordinates: list[tuple[int, int]],
    df_edgeservers: pd.DataFrame,
    df_pois: pd.DataFrame,
    save_path: str | None = None,
):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    plot_size = 12
    fig.set_size_inches(plot_size, plot_size)
    for i, coord in enumerate(df_pois.Latitude):
        ax.plot([df_pois.Longitude[i]], [df_pois.Latitude[i]], "o", markersize=8, color="red")
    for i, coord in enumerate(df_edgeservers.Latitude):
        ax.plot([df_edgeservers.Longitude[i]], [df_edgeservers.Latitude[i]], "o", markersize=3, color="blue")
    for coord in basestations_coordinates:
        ax.plot([coord[0]], [coord[1]], "o", markersize=1, color="green")
    red_patch = plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="red", markersize=6, label="Points of Interest")  # type: ignore
    blue_patch = plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="blue", markersize=6, label="Edge/Cloud Servers")  # type: ignore
    green_patch = plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="green", markersize=6, label="Base Stations")  # type: ignore
    ax.legend(handles=[red_patch, blue_patch, green_patch], loc="upper left", ncol=3)
    ax.set_xlabel("Normalized Longitude")
    ax.set_ylabel("Normalized Latitude")
    plt.tight_layout(pad=0.1)
    if save_path is not None:
        plt.savefig(save_path)
    else:
        plt.show()


def plot_points_of_interest(df_pois: pd.DataFrame, save_path: str | None = None):
    import random

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    fig.set_size_inches(14, 6)
    for i, row in df_pois.iterrows():
        color = (random.random(), random.random(), random.random())
        ax.barh(i, row["PeakEnd"] - row["PeakStart"], left=row["PeakStart"], color=color, edgecolor="black")  # type: ignore
    ax.set_yticks(range(len(df_pois)))
    ax.set_yticklabels(df_pois["Name"])
    ax.set_xlim(DAY_START_IN_MINUTES, DAY_END_IN_MINUTES)
    ax.set_xlabel("Time (minutes)")
    ax.set_ylabel("Points of Interest")
    ax.set_title("Peak Duration for Points of Interest")
    plt.tight_layout(pad=0.1)
    if save_path is not None:
        plt.savefig(save_path)
    else:
        plt.show()


if __name__ == "__main__":
    test_gen_plots()
