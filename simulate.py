import os

import EdgeSimPy.edge_sim_py as espy
from algorithms import resource_management_algorithm, stopping_criterion
from scenario_build import (
    calc_infra_services,
    create_base_stations,
    create_edge_servers,
    create_grid,
    create_points_of_interest,
    create_providers,
    create_regitries,
    create_topology,
    create_user_metadata,
    export_scenario,
)


def main():
    if not os.path.exists("datasets/generated_dataset.json"):
        print("Generating dataset")
        grid = create_grid()
        create_base_stations(grid)
        create_topology()
        create_edge_servers()
        create_regitries()
        create_providers(grid)
        create_user_metadata()
        create_points_of_interest()
        calc_infra_services()
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
