import random
import sys

import networkx as nx
import numpy as np
from mesa import Model
from sklearn.cluster import KMeans

import EdgeSimPy.edge_sim_py as espy
import map_build
from custom_serialization import application_to_dict, edge_server_to_dict, service_to_dict, user_to_dict
from helper_methods import uniform
from servers import CONTAINER_REGISTRIES, PROVIDER_SPECS

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
]

NUMBER_OF_SERVICES = (
    sum([app_spec["number_of_objects"] * app_spec["number_of_services"] for app_spec in APPLICATION_SPECIFICATIONS]) * 2
)

SERVICE_DEMANDS = uniform(
    n_items=NUMBER_OF_SERVICES,
    valid_values=SERVICE_DEMAND_VALUES,
    shuffle_distribution=True,
)


def create_grid() -> list[tuple[int, int]]:
    print("Creating Grid")
    return espy.hexagonal_grid(x_size=map_build.COORD_UPPER_BOUND, y_size=map_build.COORD_UPPER_BOUND)


def create_base_stations(grid_coordinates: list[tuple[int, int]]):
    print("Creating Base Stations")
    for coordinates in grid_coordinates:
        base_station = espy.BaseStation()
        base_station.coordinates = coordinates
        base_station.wireless_delay = 1
        network_switch = espy.sample_switch()
        base_station._connect_to_network_switch(network_switch=network_switch)


def create_topology() -> espy.Topology:
    print("Creating Topology")
    return espy.partially_connected_hexagonal_mesh(
        network_nodes=espy.NetworkSwitch.all(),
        link_specifications=[{"delay": 1, "bandwidth": 10}],
    )


def create_edge_servers():
    print("Creating Edge Servers")
    # Creating clusters of network switches based on the number of specified edge servers
    number_of_edge_servers = 0
    for provider in PROVIDER_SPECS:
        number_of_edge_servers += sum([spec["number_of_objects"] for spec in provider["edge_server_specs"]])

    edge_servers_df = map_build.create_edge_servers_df()
    edge_server_coordinates = random.sample(map_build.to_tuple_list(edge_servers_df), number_of_edge_servers)

    for provider_spec in PROVIDER_SPECS:
        for edge_server_spec in provider_spec["edge_server_specs"]:
            for _ in range(edge_server_spec["number_of_objects"]):
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
                    attribute_name="coordinates", attribute_value=edge_server_coordinates[edge_server.id - 1]
                )  # type: ignore
                base_station._connect_to_edge_server(edge_server=edge_server)


def create_regitries():
    espy.worst_fit_registries(container_registry_specifications=CONTAINER_REGISTRIES, servers=espy.EdgeServer.all())


def create_providers(grid_coordinates: list[tuple[int, int]]):
    print("Creating Providers")
    # Defining user/provider trust patterns
    providers_trust_patterns = [[2, 1, 0], [1, 2, 0]]

    for provider_trust_pattern in providers_trust_patterns:
        for app_spec in APPLICATION_SPECIFICATIONS:
            for _ in range(app_spec["number_of_objects"]):
                app = espy.Application()
                app.provisioned = False

                for _ in range(random.randint(1, 3)):
                    # Creating the user that access the application
                    user = espy.User()

                    # Defining user trust on the providers
                    user.providers_trust = {
                        1: provider_trust_pattern[0],
                        2: provider_trust_pattern[1],
                        3: provider_trust_pattern[2],
                    }

                    user.communication_paths[str(app.id)] = None
                    user.delays[str(app.id)] = None
                    user.delay_slas[str(app.id)] = DELAY_SLAS[(user.id - 1) % len(DELAY_SLAS)]

                    # Defining user's coordinates and connecting him to a base station
                    user.mobility_model = espy.point_of_interest_mobility
                    user._set_initial_position(
                        coordinates=espy.User.random_user_placement(grid_coordinates), number_of_replicates=2
                    )
                    user.point_of_interest = user.step_point_of_interest()

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
                        image_digest=service_image.digest,
                        cpu_demand=None,
                        memory_demand=None,
                        label="Alpine",
                        state=0,
                    )
                    service.privacy_requirement = service_privacy_requirements[service_index]
                    service.cpu_demand = SERVICE_DEMANDS[service.id - 1]["cpu"]
                    service.memory_demand = SERVICE_DEMANDS[service.id - 1]["memory"]

                    # Connecting the application to its new service
                    app.connect_to_service(service)


def create_user_metadata():
    print("Creating User Metadata")
    # Calculating the network delay between users and edge servers (useful for defining reasonable delay SLAs)
    users = []
    all_users = espy.User.all()
    for i_users, user in enumerate(all_users):
        user_metadata = {"object": user, "all_delays": []}
        _edge_servers = []
        all_edgeservers = espy.EdgeServer.all()
        for i_edgeservers, edge_server in enumerate(all_edgeservers):
            if i_edgeservers % 10 == 0:
                sys.stdout.write("\r")
                sys.stdout.write(f"{i_edgeservers:04d}/{len(all_edgeservers)} of {i_users:02d}/{len(all_users)}")
                sys.stdout.flush()
            path = nx.shortest_path(
                G=espy.Topology.first(),
                source=user.base_station.network_switch,
                target=edge_server.network_switch,
                weight="delay",
            )
            user_metadata["all_delays"].append(espy.Topology.first().calculate_path_delay(path=path))
        sys.stdout.write("\r")
        sys.stdout.flush()
        user_metadata["min_delay"] = min(user_metadata["all_delays"])
        user_metadata["max_delay"] = max(user_metadata["all_delays"])
        user_metadata["avg_delay"] = sum(user_metadata["all_delays"]) / len(user_metadata["all_delays"])
        user_metadata["delays"] = {}
        for delay in sorted(list(set(user_metadata["all_delays"]))):
            user_metadata["delays"][delay] = user_metadata["all_delays"].count(delay)

        users.append(user_metadata)
    sys.stdout.write("\r")
    sys.stdout.flush()

    print("\n\n==== NETWORK DISTANCE (DELAY) BETWEEN USERS AND EDGE SERVERS ====")
    for user_metadata in users:
        user_attrs = {
            "object": user_metadata["object"],
            "sla": user_metadata["object"].delay_slas[str(user_metadata["object"].applications[0].id)],
            "min": user_metadata["min_delay"],
            "max": user_metadata["max_delay"],
            "avg": round(user_metadata["avg_delay"]),
            "delays": user_metadata["delays"],
        }
        print(f"{user_attrs}")
        if user_attrs["min"] > user_attrs["sla"]:
            print(f"\n\nWARNING: {user_attrs['object']} delay SLA is not achievable!\n\n")


def create_points_of_interest():
    df_poi = map_build.create_points_of_interest_df()
    for index, row in df_poi.iterrows():
        poi = espy.PointOfInterest()
        poi.coordinates = (row["Longitude"], row["Latitude"])
        poi.peak_start = row["PeakStart"]
        poi.peak_end = row["PeakEnd"]
        poi.name = row["Name"]


def calc_infra_services():
    print("Creating Calculating Infrastructure services")
    # Calculating the infrastructure occupation and information about the services
    edge_server_cpu_capacity = 0
    edge_server_memory_capacity = 0
    service_cpu_demand = 0
    service_memory_demand = 0

    for edge_server in espy.EdgeServer.all():
        edge_server_cpu_capacity += edge_server.cpu
        edge_server_memory_capacity += edge_server.memory

    for service in espy.Service.all():
        service_cpu_demand += service.cpu_demand
        service_memory_demand += service.memory_demand

    overall_cpu_occupation = round((service_cpu_demand / edge_server_cpu_capacity) * 100, 1)
    overall_memory_occupation = round((service_memory_demand / edge_server_memory_capacity) * 100, 1)

    print("\n\n==== INFRASTRUCTURE OCCUPATION OVERVIEW ====")
    print(f"Edge Servers: {espy.EdgeServer.count()}")
    print(f"\tCPU Capacity: {edge_server_cpu_capacity}")
    print(f"\tRAM Capacity: {edge_server_memory_capacity}")
    print(f"Services: {espy.Service.count()}")
    print(f"\tCPU Demand: {service_cpu_demand}")
    print(f"\t\t[Privacy Requirement = 0] {sum([s.cpu_demand for s in espy.Service.all() if s.privacy_requirement == 0])}")
    print(f"\t\t[Privacy Requirement = 1] {sum([s.cpu_demand for s in espy.Service.all() if s.privacy_requirement == 1])}")
    print(f"\t\t[Privacy Requirement = 2] {sum([s.cpu_demand for s in espy.Service.all() if s.privacy_requirement == 2])}")
    print(f"\tRAM Demand: {service_memory_demand}")
    print(f"\t\t[Privacy Requirement = 0] {sum([s.memory_demand for s in espy.Service.all() if s.privacy_requirement == 0])}")
    print(f"\t\t[Privacy Requirement = 1] {sum([s.memory_demand for s in espy.Service.all() if s.privacy_requirement == 1])}")
    print(f"\t\t[Privacy Requirement = 2] {sum([s.memory_demand for s in espy.Service.all() if s.privacy_requirement == 2])}")
    print("Overall Occupation")
    print(f"\tCPU: {overall_cpu_occupation}%")
    print(f"\tRAM: {overall_memory_occupation}%")


def calc_infra_providers():
    print("Creating Calculating Infrastructure Providers")
    # Calculating the occupation of each infrastructure provider
    print("==== INFRASTRUCTURE PROVIDERS OVERVIEW ====")
    for provider_id in range(1, len(PROVIDER_SPECS) + 1):
        provider_edge_servers = [s for s in espy.EdgeServer.all() if s.infrastructure_provider == provider_id]

        users_with_trust0 = [user for user in espy.User.all() if user.providers_trust[provider_id] == 0]
        users_with_trust1 = [user for user in espy.User.all() if user.providers_trust[provider_id] == 1]
        users_with_trust2 = [user for user in espy.User.all() if user.providers_trust[provider_id] == 2]

        demand_trust0 = sum(
            [sum([s.cpu_demand for s in u.applications[0].services if s.privacy_requirement == 0]) for u in users_with_trust0]
        )
        demand_trust1 = sum(
            [sum([s.cpu_demand for s in u.applications[0].services if s.privacy_requirement == 0]) for u in users_with_trust1]
        )
        demand_trust2 = sum(
            [sum([s.cpu_demand for s in u.applications[0].services if s.privacy_requirement == 0]) for u in users_with_trust2]
        )

        print(f"=== Provider {provider_id} ===")
        print(f"Overall CPU: {sum([s.cpu for s in provider_edge_servers])}")
        print(f"Overall RAM: {sum([s.memory for s in provider_edge_servers])}")
        print(f"\tUsers with trust 0: {len(users_with_trust0)}. CPU Demand: {demand_trust0}")
        print(f"\tUsers with trust 1: {len(users_with_trust1)}. CPU Demand: {demand_trust1}")
        print(f"\tUsers with trust 2: {len(users_with_trust2)}. CPU Demand: {demand_trust2}\n")


def export_scenario():
    # Exporting scenario
    espy.Application._to_dict = application_to_dict
    espy.User._to_dict = user_to_dict
    espy.EdgeServer._to_dict = edge_server_to_dict
    espy.Service._to_dict = service_to_dict
    espy.ComponentManager.export_scenario(
        save_to_file=True, file_name="generated_dataset"
    )  # file_name is prepended with "datasets/"
