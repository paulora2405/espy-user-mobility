from EdgeSimPy import edge_sim_py as espy

SERVERS_PER_SPEC_EDGE_PROVIDERS = 30
SERVERS_PER_SPEC_CLOUD_PROVIDERS = 4  # must have an integer square root

# Defining specifications for container images and container registries
CONTAINER_IMAGE_SPECIFICATIONS = [
    {
        "name": "alpine",
        "tag": "latest",
        "digest": "sha256:a777c9c66ba177ccfea23f2a216ff6721e78a662cd17019488c417135299cd89",
        "layers": [
            {
                "digest": "sha256:df9b9388f04ad6279a7410b85cedfdcb2208c0a003da7ab5613af71079148139",
                "size": 2,
                "instruction": "ADD file:5d673d25da3a14ce1f6cf",
            }
        ],
        "layers_digests": ["sha256:df9b9388f04ad6279a7410b85cedfdcb2208c0a003da7ab5613af71079148139"],
    },
    {
        "name": "registry",
        "tag": "latest",
        "digest": "sha256:6060f78eda124040cfeb19d2fcc9af417f5ee23dc05d0894fcfe21f24c9cbf9a",
        "layers": [
            {
                "digest": "sha256:df9b9388f04ad6279a7410b85cedfdcb2208c0a003da7ab5613af71079148139",
                "size": 2,
                "instruction": "ADD file:5d673d25da3a14ce1f6cf",
            },
            {
                "digest": "sha256:b6846b9db566bc2ea5e2b0056c49772152c9b7c8f06343efb1ef764b23bb9d96",
                "size": 5,
                "instruction": "/bin/sh -c set -eux; \tversion=",
            },
        ],
        "layers_digests": [
            "sha256:df9b9388f04ad6279a7410b85cedfdcb2208c0a003da7ab5613af71079148139",
            "sha256:b6846b9db566bc2ea5e2b0056c49772152c9b7c8f06343efb1ef764b23bb9d96",
        ],
    },
]

CONTAINER_REGISTRY_SPECIFICATIONS = [
    {
        "number_of_objects": 1,
        "cpu_demand": 0,
        "memory_demand": 0,
        "images": [
            {"name": "registry", "tag": "latest"},
            {"name": "alpine", "tag": "latest"},
        ],
    }
]

CONTAINER_REGISTRIES = espy.create_container_registries(
    container_registry_specifications=CONTAINER_REGISTRY_SPECIFICATIONS,
    container_image_specifications=CONTAINER_IMAGE_SPECIFICATIONS,
)


def sgi_rackable_c2112_4g10() -> object:
    """Creates an EdgeServer object according to XXXX [TODO].

    Returns:
        edge_server (object): Created EdgeServer object.
    """
    edge_server = espy.EdgeServer()
    # edge_server.model_name = "SGI Rackable C2112-4G10"
    edge_server.model_name = "SGI"

    # Computational capacity (CPU in cores, RAM memory in megabytes, and disk in megabytes)
    edge_server.cpu = 32
    edge_server.memory = 32_768
    edge_server.disk = 1_048_576
    edge_server.mips = 2_750

    # Power-related attributes
    edge_server.power_model_parameters = {
        "static_power_percentage": 265 / 1387,
        "max_power_consumption": 1387,
    }

    return edge_server


def proliant_dl360_gen9() -> object:
    """Creates an EdgeServer object according to XXXX [TODO].

    Returns:
        edge_server (object): Created EdgeServer object.
    """
    edge_server = espy.EdgeServer()
    # edge_server.model_name = "HPE ProLiant DL360 Gen9"
    edge_server.model_name = "HPE"

    # Computational capacity (CPU in cores, RAM memory in megabytes, and disk in megabytes)
    edge_server.cpu = 36
    edge_server.memory = 65_536
    edge_server.disk = 1_048_576
    edge_server.mips = 3_000

    # Power-related attributes
    edge_server.power_model_parameters = {
        "static_power_percentage": 45 / 276,
        "max_power_consumption": 276,
    }

    return edge_server


def ar585_f1() -> object:
    """Creates an EdgeServer object according to XXXX [TODO].

    Returns:
        edge_server (object): Created EdgeServer object.
    """
    edge_server = espy.EdgeServer()
    # edge_server.model_name = "Acer AR585 F1"
    edge_server.model_name = "Acer"

    # Computational capacity (CPU in cores, RAM memory in megabytes, and disk in megabytes)
    edge_server.cpu = 48
    edge_server.memory = 65_536
    edge_server.disk = 1_048_576
    edge_server.mips = 3_500

    # Power-related attributes
    edge_server.power_model_parameters = {
        "static_power_percentage": 127 / 559,
        "max_power_consumption": 559,
    }

    return edge_server


def cloud_server() -> object:
    """Creates an CloudServer object according to XXXX [TODO].

    Returns:
        cloud_server (object): Created CloudServer object.
    """
    cloud_server = espy.EdgeServer()
    cloud_server.model_name = "CLOUD"

    # Computational capacity (CPU in cores, RAM memory in megabytes, and disk in megabytes)
    cloud_server.cpu = 480
    cloud_server.memory = 4_398_046  # 4TiB
    cloud_server.disk = 17_592_186  # 16TiB
    cloud_server.mips = 35_000

    # Power-related attributes
    cloud_server.power_model_parameters = {
        "static_power_percentage": 1000 / 7000,
        "max_power_consumption": 7000,
    }

    return cloud_server


PROVIDER_SPECS = [
    {
        "id": 1,
        "edge_server_specs": [
            {"spec": sgi_rackable_c2112_4g10, "number_of_objects": SERVERS_PER_SPEC_EDGE_PROVIDERS},
            {"spec": proliant_dl360_gen9, "number_of_objects": SERVERS_PER_SPEC_EDGE_PROVIDERS},
            {"spec": ar585_f1, "number_of_objects": SERVERS_PER_SPEC_EDGE_PROVIDERS},
        ],
    },
    {
        "id": 4,
        "cloud_server_specs": [
            {"spec": cloud_server, "number_of_objects": SERVERS_PER_SPEC_CLOUD_PROVIDERS},
        ],
    },
]
