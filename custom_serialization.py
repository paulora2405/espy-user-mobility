import copy
import random

import matplotlib.pyplot as plt
import networkx as nx

import EdgeSimPy.edge_sim_py as espy


def display_topology(topology: nx.Graph, output_filename: str = "topology"):
    # Customizing visual representation of topology
    positions = {}
    labels = {}
    colors = []
    sizes = []

    # Gathering the coordinates of edge servers
    edge_server_coordinates = [edge_server.coordinates for edge_server in espy.EdgeServer.all()]

    # Defining list of color options
    color_options = []
    for _ in range(espy.EdgeServer.count()):
        color_options.append([random.random(), random.random(), random.random()])

    for node in topology.nodes():
        positions[node] = node.coordinates
        labels[node] = node.id
        node_size = 500 if any(user.coordinates == node.coordinates for user in espy.User.all()) else 100
        sizes.append(node_size)

        if node.coordinates in edge_server_coordinates:
            colors.append("red")
            # colors.append([primary_color_value / 3 for primary_color_value in color_options[node_clusters[node.id - 1]]])
        else:
            colors.append("black")
            # colors.append(color_options[node_clusters[node.id - 1]])

    # Configuring drawing scheme
    nx.draw(
        topology,
        pos=positions,
        node_color=colors,
        node_size=sizes,
        labels=labels,
        font_size=6,
        font_weight="bold",
        font_color="whitesmoke",
    )

    # Saving a topology image in the disk
    plt.savefig(f"{output_filename}.png", dpi=120)


# Application -> provisioned
def application_to_dict(self) -> dict:
    """Method that overrides the way the object is formatted to JSON."
    Returns:
        dict: JSON-friendly representation of the object as a dictionary.
    """
    dictionary = {
        "attributes": {
            "id": self.id,
            "label": self.label,
            "provisioned": self.provisioned,
        },
        "relationships": {
            "services": [{"class": type(service).__name__, "id": service.id} for service in self.services],
            "users": [{"class": type(user).__name__, "id": user.id} for user in self.users],
        },
    }
    return dictionary


# User -> providers_trust
def user_to_dict(self) -> dict:
    """Method that overrides the way User objects are formatted to JSON."

    Returns:
        dict: JSON-friendly representation of the object as a dictionary.
    """
    access_patterns = {}
    for app_id, access_pattern in self.access_patterns.items():
        access_patterns[app_id] = {"class": access_pattern.__class__.__name__, "id": access_pattern.id}

    dictionary = {
        "attributes": {
            "id": self.id,
            "coordinates": self.coordinates,
            "coordinates_trace": self.coordinates_trace,
            "delays": copy.deepcopy(self.delays),
            "delay_slas": copy.deepcopy(self.delay_slas),
            "communication_paths": copy.deepcopy(self.communication_paths),
            "making_requests": copy.deepcopy(self.making_requests),
        },
        "relationships": {
            "access_patterns": access_patterns,
            "mobility_model": self.mobility_model.__name__,
            "applications": [{"class": type(app).__name__, "id": app.id} for app in self.applications],
            "base_station": {"class": type(self.base_station).__name__, "id": self.base_station.id},
        },
    }
    return dictionary


# EdgeServer -> infrastructure_provider
def edge_server_to_dict(self) -> dict:
    """Method that overrides the way EdgeServer objects are formatted to JSON."

    Returns:
        dict: JSON-friendly representation of the object as a dictionary.
    """
    dictionary = {
        "attributes": {
            "id": self.id,
            "available": self.available,
            "model_name": self.model_name,
            "cpu": self.cpu,
            "memory": self.memory,
            "disk": self.disk,
            "cpu_demand": self.cpu_demand,
            "memory_demand": self.memory_demand,
            "disk_demand": self.disk_demand,
            "coordinates": self.coordinates,
            "max_concurrent_layer_downloads": self.max_concurrent_layer_downloads,
            "active": self.active,
            "power_model_parameters": self.power_model_parameters,
            "infrastructure_provider": self.infrastructure_provider,
        },
        "relationships": {
            "power_model": self.power_model.__name__ if self.power_model else None,
            "base_station": (
                {"class": type(self.base_station).__name__, "id": self.base_station.id} if self.base_station else None
            ),
            "network_switch": (
                {"class": type(self.network_switch).__name__, "id": self.network_switch.id} if self.network_switch else None
            ),
            "services": [{"class": type(service).__name__, "id": service.id} for service in self.services],
            "container_layers": [{"class": type(layer).__name__, "id": layer.id} for layer in self.container_layers],
            "container_images": [{"class": type(image).__name__, "id": image.id} for image in self.container_images],
            "container_registries": [{"class": type(reg).__name__, "id": reg.id} for reg in self.container_registries],
        },
    }
    return dictionary


# Service -> privacy_requirement
def service_to_dict(self) -> dict:
    """Method that overrides the way Service objects are formatted to JSON."

    Returns:
        dict: JSON-friendly representation of the object as a dictionary.
    """
    dictionary = {
        "attributes": {
            "id": self.id,
            "label": self.label,
            "state": self.state,
            "_available": self._available,
            "cpu_demand": self.cpu_demand,
            "memory_demand": self.memory_demand,
            "image_digest": self.image_digest,
            "privacy_requirement": self.privacy_requirement,
        },
        "relationships": {
            "application": {"class": type(self.application).__name__, "id": self.application.id},
            "server": {"class": type(self.server).__name__, "id": self.server.id} if self.server else None,
        },
    }
    return dictionary
