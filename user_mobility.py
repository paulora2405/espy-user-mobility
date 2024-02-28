import networkx as nx
import random
from EdgeSimPy import edge_sim_py as espy


def add_pi_to_user(user: espy.User):
    if user.point_of_interest is not None:
        return

    current_step = user.model.schedule.steps + 1
    user.point_of_interest = _pick_random_poi(current_step)


def _pick_random_poi(current_step: int):
    pass


def point_of_interest_mobility(user: espy.User):
    parameters = user.mobility_model_parameters if hasattr(user, "mobility_model_parameters") else {}

    n_paths = parameters["n_paths"] if "n_paths" in parameters else 1

    current_node = espy.BaseStation.find_by(attribute_name="coordinates", attribute_value=user.coordinates)

    mobility_path = []

    for i in range(n_paths):
        target_node = random.choice([bs for bs in espy.BaseStation.all() if bs != current_node])

        path = nx.shortest_path(G=user.model.topology, source=current_node.network_switch, target=target_node.network_switch)
        mobility_path.extend([network_switch.base_station for network_switch in path])

        if i < n_paths - 1:
            current_node = mobility_path.pop(-1)

        user_base_station = espy.BaseStation.find_by(attribute_name="coordinates", attribute_value=user.coordinates)
        if user_base_station == mobility_path[0]:
            mobility_path.pop(0)

    if "seconds_to_move" in parameters and isinstance(parameters["seconds_to_move"], int) and parameters["seconds_to_move"] < 1:
        raise Exception("The 'seconds_to_move' key passed inside the mobility model's 'parameters' attribute must be > 1")

    seconds_to_move = parameters["seconds_to_move"] if "seconds_to_move" in parameters else 60
    seconds_to_move = max(1, int(seconds_to_move / user.model.tick_duration))

    mobility_path = [item for item in mobility_path for _ in range(seconds_to_move)]

    user.coordinates_trace.extend([bs.coordinates for bs in mobility_path])
