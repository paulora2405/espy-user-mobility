from scenario_build import (
    create_grid,
    create_base_stations,
    create_topology,
    create_edge_servers,
    create_regitries,
    create_providers,
    create_user_metadata,
    calc_infra_services,
    calc_infra_providers,
    stopping_criterion,
    resource_management_algorithm,
)
import EdgeSimPy.edge_sim_py as espy


def main():
    grid = create_grid()
    create_base_stations(grid)
    create_topology()
    create_edge_servers()
    create_regitries()
    create_providers(grid)
    create_user_metadata()
    calc_infra_services()
    calc_infra_providers()

    simulator = espy.Simulator(
        dump_interval=5,
        tick_duration=1,
        tick_unit="seconds",
        stopping_criterion=stopping_criterion,
        resource_management_algorithm=resource_management_algorithm,
    )

    simulator.initialize(input_file="datasets/generated_dataset.json")

    simulator.run_model()


if __name__ == "__main__":
    main()
