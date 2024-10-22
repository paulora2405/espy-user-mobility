import networkx as nx
from mesa import Model

import EdgeSimPy.edge_sim_py as espy


def resource_management_algorithm(parameters):
    DISTANCE_THRESHOLD = 0.8
    MIGRATION_RECENCY_THRESHOLD = 10
    service: espy.Service
    for service in espy.Service.all():
        if service.server is None and not service.being_provisioned:
            # TODO: sort edge server by a best fit objective function (current capacity - service demand)
            edge_servers = espy.EdgeServer.all()
            edge_servers.sort(key=lambda x: x.cpu - service.cpu_demand)  # TODO: implement edge_server.py:capacity_score()
            edge_server: espy.EdgeServer
            for edge_server in edge_servers:
                if edge_server.has_capacity_to_host(service=service):
                    if edge_server.model_name == "CLOUD":
                        print("Migrating service to cloud")
                    service.provision(target_server=edge_server)
                    break

    for service in espy.Service.all():
        if (
            service.server is not None
            and not service.being_provisioned
            and not service.was_recently_migrated(MIGRATION_RECENCY_THRESHOLD)
            and service.total_dist_from_users > DISTANCE_THRESHOLD
        ):
            for edge_server in espy.EdgeServer.all():
                if (
                    edge_server.has_capacity_to_host(service=service)
                    and distance_from_edge_server_to_users(service, edge_server) < service.total_dist_from_users
                ):
                    if edge_server.model_name == "CLOUD":
                        print("Migrating service to cloud")
                    service.provision(target_server=edge_server)
                    break


def distance_from_edge_server_to_users(service: espy.Service, edge_server: espy.EdgeServer) -> float:
    # TODO: extract to separate method
    total_distance_from_users: float = 0.0
    max_distance: float = 0.0
    if service.server is not None and len(service.application.users) > 0:
        for user in service.application.users:
            curr_distance: float = nx.shortest_path_length(
                G=service.model.topology,
                source=service.server.base_station.network_switch,
                weight="delay",
                method="dijkstra",
                target=user.base_station.network_switch,
            )
            total_distance_from_users += curr_distance
            if curr_distance > max_distance:
                max_distance = curr_distance
        total_distance_from_users = total_distance_from_users / (len(service.application.users) * max_distance)
    return total_distance_from_users


# Algorithm 1: Application Reallocation algorithm reallocateApps()
# Input: A set of service composed Applications A = {A1, A2, . . . , An}
# Input: A recency period threshold P expressed in some time unit
# Input: A set of all available Servers I
# Input: SLA objectives O
# Input: A threshold of minimum values for the selected SLAs T
# 1 servicesList ← joinAll(A .services);
# 2 filteredList ← f ilter(s ∈ servicesList, s.isNotMigrating());
# 3 filteredList ← f ilter(s ∈ f ilteredList, s.notRecentlyMigrated(P));
# 4 filteredList ← f ilter(s ∈ f ilteredList, s.decreasingSLA(T )); XXX: Delay em termos de distância geográfica
# 5 for service ∈ f ilteredList do
# 6     allocateService(service, I , O);
# 7 end

# Algorithm 2: Service Allocation algorithm allocateService()
# Input: A Service S
# Input: A set of all available Servers I
# Input: SLA objectives O
# 1 selectedServer ← selectServerCandidate(S , I , O);
# 2 selectedServer.allocate(S );

# Algorithm 3: Server candidates selection algorithm selectServerCandidate()
# Input: A Service S
# Input: A set of all available Servers I
# Input: SLA objectives O
# Output: A selected Server candidate C suitable for S
# 1 distance_total ← calcDistance(S.users, servers);
# 4 C ← bestFitObjective(candidateServerGroups. first, O); XXX: função objetivo: minimizar o somatorio da area de cobertura + custo de provisionamento
# 5 return C ;

# minimizar o somatorio da distancia total de todos os serviços,


def stopping_criterion(model: Model):
    provisioned_services = sum(1 for service in espy.Service.all() if service.server is not None)
    return provisioned_services == espy.Service.count() and model.schedule.steps > 1200
