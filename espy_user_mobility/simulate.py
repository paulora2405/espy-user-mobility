import os
import sys
import time

from mesa import Model

import EdgeSimPy.edge_sim_py as espy

from .map_build import plot_grid, plot_points_of_interest
from .scenario_build import (
    create_base_stations,
    create_cloud_servers,
    create_edge_servers,
    create_grid,
    create_points_of_interest,
    create_providers,
    create_regitries,
    create_topology,
    export_scenario,
)

DISTANCE_THRESHOLD = 0.8
MIGRATION_RECENCY_THRESHOLD = 8
STEPS_LIMIT = 1080 * 2


def resource_management_algorithm(parameters):
    service: espy.Service
    for service in espy.Service.all():
        # Initial allocation
        edge_servers: list[espy.EdgeServer] = espy.EdgeServer.all()
        edge_servers.sort(reverse=True, key=lambda server: server.current_capacity_score())
        if service.server is None and not service.being_provisioned:
            for edge_server in edge_servers:
                if edge_server.has_capacity_to_host(service=service):
                    service.provision(target_server=edge_server)
                    break
        # Reallocation
        elif (
            service.server is not None
            and not service.was_recently_migrated(MIGRATION_RECENCY_THRESHOLD)
            and service.total_dist_from_users > DISTANCE_THRESHOLD
        ):
            for edge_server in edge_servers:
                if (
                    edge_server.has_capacity_to_host(service=service)
                    and service.distance_from_edge_server_to_users(edge_server) < service.total_dist_from_users
                ):
                    service.provision(target_server=edge_server)
                    break


def stopping_criterion(model: Model):
    return model.schedule.steps >= STEPS_LIMIT  # type: ignore


def generate_dataset():
    if not os.path.exists("datasets/generated_dataset.json"):
        print("Generating dataset")
        start_time = time.time()
        grid = create_grid()
        create_base_stations(grid)
        topology = create_topology()
        create_cloud_servers(topology, grid)
        df_edge_servers = create_edge_servers()
        create_regitries()
        create_providers(grid)
        df_pois = create_points_of_interest()
        base_stations = espy.BaseStation.all()
        bs_coords = [b.coordinates for b in base_stations]
        os.makedirs("datasets/images", exist_ok=True)
        plot_grid(bs_coords, df_edge_servers, df_pois, save_path="datasets/images/grid.png")
        plot_points_of_interest(df_pois, save_path="datasets/images/pois.png")
        export_scenario()
        print(f"Dataset generated in {time.time() - start_time} seconds")
    else:
        print("Using existing dataset")


def main():
    if len(sys.argv) == 4:
        try:
            global DISTANCE_THRESHOLD, MIGRATION_RECENCY_THRESHOLD, STEPS_LIMIT
            DISTANCE_THRESHOLD = float(sys.argv[1])
            MIGRATION_RECENCY_THRESHOLD = int(sys.argv[2])
            STEPS_LIMIT = int(sys.argv[3])
        except ValueError:
            print("Usage: python3 script.py <distance_threshold> <migration_recency_threshold> <steps_limit>")
            print("Example: python3 main.py 0.8 16 1080")
            sys.exit(1)

    generate_dataset()

    logs_dir = (
        "logs/"
        f"{DISTANCE_THRESHOLD}dist-{MIGRATION_RECENCY_THRESHOLD}migr-{STEPS_LIMIT}steps/"
        f"{time.strftime('%Y-%m-%d_%H-%M-%S')}"
    )

    print(
        "Initializing simulator with parameters:"
        f"\n- Distance threshold: {DISTANCE_THRESHOLD}"
        f"\n- Migration recency threshold: {MIGRATION_RECENCY_THRESHOLD}"
        f"\n- Steps limit: {STEPS_LIMIT}"
    )

    simulator = espy.Simulator(
        dump_interval=5,
        tick_duration=1,
        tick_unit="minutes",
        stopping_criterion=stopping_criterion,
        resource_management_algorithm=resource_management_algorithm,
        logs_directory=logs_dir,
    )

    print("Initializing simulation")
    start_time = time.time()
    simulator.initialize(input_file="datasets/generated_dataset.json")
    print(f"Initialization finished in {time.time() - start_time} seconds")

    print("Running model")
    start_time = time.time()
    simulator.run_model()
    print(f"Simulation finished in {time.time() - start_time} seconds")


if __name__ == "__main__":
    main()
