import random
from math import sqrt

import pandas as pd

from EdgeSimPy import edge_sim_py as espy

from .custom_serialization import application_to_dict, edge_server_to_dict, service_to_dict, user_to_dict
from .helper_methods import uniform
from .map_build import COORD_UPPER_BOUND, create_edge_servers_df, create_points_of_interest_df, to_tuple_list
from .servers import CONTAINER_REGISTRIES, PROVIDER_SPECS, SERVERS_PER_SPEC_CLOUD_PROVIDERS

APPLICATION_SPECIFICATIONS = [
    {"number_of_objects": 2, "number_of_services": 1},
    {"number_of_objects": 2, "number_of_services": 2},
    {"number_of_objects": 2, "number_of_services": 4},
    {"number_of_objects": 2, "number_of_services": 8},
]

DELAY_SLAS = uniform(
    n_items=sum([app_spec["number_of_objects"] for app_spec in APPLICATION_SPECIFICATIONS]) * 2,
    valid_values=[3, 6],
    shuffle_distribution=True,
)

SERVICE_DEMAND_VALUES = [
    {"cpu": 2, "memory": 2 * 1024},
    {"cpu": 4, "memory": 4 * 1024},
    {"cpu": 8, "memory": 8 * 1024},
    {"cpu": 16, "memory": 16 * 1024},
    {"cpu": 50, "memory": 32 * 1024},  # TESTING: force service to go to cloud server
]

NUMBER_OF_SERVICES = sum(
    [app_spec["number_of_objects"] * app_spec["number_of_services"] for app_spec in APPLICATION_SPECIFICATIONS]
) * len(PROVIDER_SPECS)

SERVICE_DEMANDS = uniform(
    n_items=NUMBER_OF_SERVICES,
    valid_values=SERVICE_DEMAND_VALUES,
    shuffle_distribution=True,
)

USERS_MIN, USERS_MAX = 10, 30
USER_SPEED_MIN, USER_SPEED_MAX = 0.3, 1.0
USER_CHANGE_OF_BECOMING_INTERESTED = 10
NUMBER_OF_CLOUD_BASE_STATIONS = SERVERS_PER_SPEC_CLOUD_PROVIDERS  # must have an integer square root
CLOUD_GRID_OFFSET = 10
CLOUD_LINK_DELAY = 10
CLOUD_LINK_BANDWIDTH = 100
EDGE_LINK_DELAY = 1
EDGE_LINK_BANDWIDTH = 10


def create_grid(x_size: int | None = None, y_size: int | None = None) -> list[tuple[int, int]]:
    print("Creating Grid")
    return espy.hexagonal_grid(
        x_size=COORD_UPPER_BOUND if x_size is None else x_size,
        y_size=COORD_UPPER_BOUND if y_size is None else y_size,
    )


def create_base_stations(grid_coordinates: list[tuple[int, int]]):
    print("Creating Edge Base Stations")
    for coordinates in grid_coordinates:
        base_station = espy.BaseStation()
        base_station.coordinates = coordinates
        base_station.wireless_delay = 1  # type: ignore
        network_switch = espy.sample_switch()
        base_station._connect_to_network_switch(network_switch=network_switch)


def create_topology() -> espy.Topology:
    print("Creating Edge Topology")
    return espy.partially_connected_hexagonal_mesh(
        network_nodes=espy.NetworkSwitch.all(),
        link_specifications=[{"delay": EDGE_LINK_DELAY, "bandwidth": EDGE_LINK_BANDWIDTH}],
    )


def create_cloud_servers(edge_topology: espy.Topology, edge_grid: list[tuple[int, int]]) -> list[tuple[int, int]]:
    print("Creating Cloud Base Stations and Switches")
    x_offset = max([coord[0] for coord in edge_grid]) + CLOUD_GRID_OFFSET
    y_offset = max([coord[1] for coord in edge_grid]) + CLOUD_GRID_OFFSET
    grid_size = int(sqrt(NUMBER_OF_CLOUD_BASE_STATIONS))
    cloud_coordinates = create_grid(x_size=grid_size, y_size=grid_size)
    cloud_coordinates = [(coord[0] + x_offset, coord[1] + y_offset) for coord in cloud_coordinates]

    # max_y = max([switch.coordinates[1] for switch in espy.NetworkSwitch.all()])
    max_y = edge_grid[-1][1]
    max_y_switches = [switch for switch in espy.NetworkSwitch.all() if switch.coordinates[1] == max_y]
    max_y_switches_sorted = sorted(max_y_switches, key=lambda s: s.coordinates[0])
    middle_switch = max_y_switches_sorted[len(max_y_switches_sorted) // 2]
    # edge_connection_to_cloud = espy.NetworkSwitch.last()
    edge_connection_to_cloud = middle_switch

    cloud_switches = []
    for coordinates in cloud_coordinates:
        cloud_base_station = espy.BaseStation()
        cloud_base_station.coordinates = coordinates
        cloud_base_station.wireless_delay = 5  # type: ignore
        network_switch: espy.NetworkSwitch = espy.sample_switch()  # type: ignore
        cloud_switches.append(network_switch)
        cloud_base_station._connect_to_network_switch(network_switch=network_switch)

    print("Creating Cloud Topology")
    edge_topology.add_nodes_from(cloud_switches)
    for cloud_switch in cloud_switches:
        if not edge_topology.has_edge(cloud_switch, edge_connection_to_cloud):
            link = espy.NetworkLink()
            link.topology = edge_topology
            link.delay = CLOUD_LINK_DELAY
            link.bandwidth = CLOUD_LINK_BANDWIDTH
            link.nodes = [cloud_switch, edge_connection_to_cloud]
            edge_topology.add_edge(cloud_switch, edge_connection_to_cloud)
            edge_topology._adj[cloud_switch][edge_connection_to_cloud] = link
            edge_topology._adj[edge_connection_to_cloud][cloud_switch] = link
        for sec_cloud_switch in cloud_switches:
            if cloud_switch != sec_cloud_switch and not edge_topology.has_edge(cloud_switch, sec_cloud_switch):
                link = espy.NetworkLink()
                link.topology = edge_topology
                link.delay = CLOUD_LINK_DELAY
                link.bandwidth = CLOUD_LINK_BANDWIDTH
                link.nodes = [cloud_switch, sec_cloud_switch]
                edge_topology.add_edge(cloud_switch, sec_cloud_switch)
                edge_topology._adj[cloud_switch][sec_cloud_switch] = link
                edge_topology._adj[sec_cloud_switch][cloud_switch] = link

    print("Creating Cloud Servers")
    for provider_spec in PROVIDER_SPECS:
        for cloud_server_spec in provider_spec.get("cloud_server_specs", []):
            for i in range(cloud_server_spec["number_of_objects"]):
                cloud_server = cloud_server_spec["spec"]()
                cloud_server.max_concurrent_layer_downloads = 3
                cloud_server.power_model = espy.LinearServerPowerModel
                cloud_server.infrastructure_provider = provider_spec["id"]
                base_station: espy.BaseStation = espy.BaseStation.find_by("coordinates", cloud_coordinates[i])  # type: ignore
                base_station._connect_to_edge_server(edge_server=cloud_server)

    edge_grid.extend(cloud_coordinates)
    return edge_grid


def create_edge_servers() -> pd.DataFrame:
    print("Creating Edge Servers")
    # Creating clusters of network switches based on the number of specified edge servers
    number_of_edge_servers = 0
    for provider in PROVIDER_SPECS:
        number_of_edge_servers += sum([spec["number_of_objects"] for spec in provider.get("edge_server_specs", [])])

    edge_servers_df = create_edge_servers_df()
    edge_servers_df = edge_servers_df.sample(n=number_of_edge_servers).reset_index(drop=True)
    edge_server_coordinates = to_tuple_list(edge_servers_df)

    for provider_spec in PROVIDER_SPECS:
        for edge_server_spec in provider_spec.get("edge_server_specs", []):
            for i in range(edge_server_spec["number_of_objects"]):
                # Creating the edge server object
                edge_server = edge_server_spec["spec"]()  # This calls espy.EdgeServer()

                # Defining the maximum number of layers that the edge server can pull simultaneously
                edge_server.max_concurrent_layer_downloads = 3

                # Specifying the edge server's power model
                edge_server.power_model = espy.LinearServerPowerModel

                # Edge server's infrastructure provider
                edge_server.infrastructure_provider = provider_spec["id"]

                # Connecting the edge server to a random base station
                # base_stations_without_edge_servers = [bs for bs in BaseStation.all() if len(bs.edge_servers) == 0]
                # base_station = random.sample(base_stations_without_edge_servers, 1)[0]
                base_station: espy.BaseStation = espy.BaseStation.find_by(
                    attribute_name="coordinates", attribute_value=edge_server_coordinates[i]
                )  # type: ignore
                base_station._connect_to_edge_server(edge_server=edge_server)

    return edge_servers_df


def create_regitries():
    espy.worst_fit_registries(container_registry_specifications=CONTAINER_REGISTRIES, servers=espy.EdgeServer.all())


def create_providers(grid_coordinates: list[tuple[int, int]]):
    print("Creating Providers")

    for _ in range(len(PROVIDER_SPECS)):
        for app_spec in APPLICATION_SPECIFICATIONS:
            for _ in range(app_spec["number_of_objects"]):
                app = espy.Application()
                app.provisioned = False  # type: ignore

                for _ in range(random.randint(USERS_MIN, USERS_MAX)):
                    # Creating the user that access the application
                    user = espy.User()

                    user.communication_paths[str(app.id)] = None
                    user.delays[str(app.id)] = None
                    user.delay_slas[str(app.id)] = DELAY_SLAS[(user.id - 1) % len(DELAY_SLAS)]

                    # Defining user's coordinates and connecting him to a base station
                    user.mobility_model = espy.point_of_interest_mobility
                    user.chance_of_becoming_interested = USER_CHANGE_OF_BECOMING_INTERESTED
                    user.movement_distance = random.random() * (USER_SPEED_MAX - USER_SPEED_MIN) + USER_SPEED_MIN
                    user._set_initial_position(
                        coordinates=espy.User.random_user_placement(grid_coordinates),
                        number_of_replicates=2,
                    )

                    # Defining user's access pattern
                    espy.CircularDurationAndIntervalAccessPattern(
                        user=user,
                        app=app,
                        start=1,
                        duration_values=[float("inf")],
                        interval_values=[0],
                    )

                    # Defining the relationship attributes between the user and the application
                    user.applications.append(app)
                    app.users.append(user)

                # Defining service privacy requirement values
                service_privacy_requirements = uniform(
                    n_items=app_spec["number_of_services"], valid_values=[0, 1, 2], shuffle_distribution=False
                )
                service_privacy_requirements = sorted(service_privacy_requirements)

                # Creating the services that compose the application
                for service_index in range(app_spec["number_of_services"]):
                    # Gathering information on the service image based on the specified 'name' and 'tag' parameters
                    service_image = next((img for img in espy.ContainerImage.all() if img.name == "alpine"), None)

                    # Creating the service object
                    service = espy.Service(
                        image_digest=service_image.digest,  # type: ignore
                        cpu_demand=None,  # type: ignore
                        memory_demand=None,  # type: ignore
                        label="Alpine",
                        state=0,
                    )
                    service.privacy_requirement = service_privacy_requirements[service_index]  # type: ignore
                    service.cpu_demand = SERVICE_DEMANDS[service.id - 1]["cpu"]
                    service.memory_demand = SERVICE_DEMANDS[service.id - 1]["memory"]

                    # Connecting the application to its new service
                    app.connect_to_service(service)


def create_points_of_interest() -> pd.DataFrame:
    df_poi = create_points_of_interest_df()
    for index, row in df_poi.iterrows():
        poi = espy.PointOfInterest()
        poi.coordinates = (row["Longitude"], row["Latitude"])
        poi.peak_start = row["PeakStart"]
        poi.peak_end = row["PeakEnd"]
        poi.name = row["Name"]

    return df_poi


def export_scenario():
    # Exporting scenario
    espy.Application._to_dict = application_to_dict
    espy.User._to_dict = user_to_dict
    espy.EdgeServer._to_dict = edge_server_to_dict
    espy.Service._to_dict = service_to_dict
    espy.ComponentManager.export_scenario(
        save_to_file=True, file_name="generated_dataset"
    )  # file_name is prepended with "datasets/"
