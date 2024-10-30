from mesa import Model

from EdgeSimPy import edge_sim_py as espy


def resource_management_algorithm(parameters):
    DISTANCE_THRESHOLD = 0.8
    MIGRATION_RECENCY_THRESHOLD = 10

    service: espy.Service
    for service in espy.Service.all():
        # Initial allocation
        edge_servers: list[espy.EdgeServer] = espy.EdgeServer.all()
        edge_servers.sort(reverse=True, key=lambda server: server.current_capacity_score())
        if service.server is None and not service.being_provisioned:
            for edge_server in edge_servers:
                if edge_server.has_capacity_to_host(service=service):
                    if edge_server.model_name == "CLOUD":
                        print("Migrating service to cloud")
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
                    if edge_server.model_name == "CLOUD":
                        print("Migrating service to cloud")
                    service.provision(target_server=edge_server)
                    break


def stopping_criterion(model: Model):
    provisioned_services = sum(1 for service in espy.Service.all() if service.server is not None)
    return provisioned_services == espy.Service.count() and model.schedule.steps > 1200  # type: ignore
