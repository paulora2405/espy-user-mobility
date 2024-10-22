import os

import EdgeSimPy.edge_sim_py as espy
from algorithms import resource_management_algorithm, stopping_criterion
from scenario_build import (
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


def main():
    if not os.path.exists("datasets/generated_dataset.json"):
        print("Generating dataset")
        grid = create_grid()
        create_base_stations(grid)
        topology = create_topology()
        create_cloud_servers(topology, grid)
        create_edge_servers()
        create_regitries()
        create_providers(grid)
        create_points_of_interest()
        export_scenario()
    else:
        print("Using existing dataset")

    simulator = espy.Simulator(
        dump_interval=5,
        tick_duration=1,
        tick_unit="minutes",
        stopping_criterion=stopping_criterion,
        resource_management_algorithm=resource_management_algorithm,
    )

    print("Initializing simulation")
    simulator.initialize(input_file="datasets/generated_dataset.json")

    print("Running model")
    simulator.run_model()

    print("Simulation finished")


if __name__ == "__main__":
    main()
