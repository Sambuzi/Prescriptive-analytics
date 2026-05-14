import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pandas import DataFrame

try:
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2
except ImportError:
    pywrapcp = None
    routing_enums_pb2 = None


DISTANZE_DEPOSITI_INDEX = 20
DISTANZE_CLIENTI_DEPOSITO_INDEX = 21
DEMAND_SCALE = 1000


def find_min_index_in_row(dist: DataFrame, visited, i):
    min_cost = 999999
    min_index = -1
    for row in range(len(dist.iloc[i, :].values)):
        if dist.iloc[i, :].values[row] < min_cost and not visited[row]:
            min_cost = dist.iloc[i, :].values[row]
            min_index = row

    return min_index


def initial_solution(dist: DataFrame, demands, ntrucks, cap):
    cost = 0
    visited = np.zeros(len(demands), dtype=bool)
    visited[20] = True  # depot
    routes = [[20] for _ in range(ntrucks)]

    for k in range(ntrucks):
        i = 20
        load = 0

        while True:
            j = find_min_index_in_row(dist, visited, i)

            if j == -1 or (load + demands[j] > cap):
                break

            visited[j] = True
            routes[k].append(j)
            load += demands[j]
            cost += dist.iloc[i, j]
            i = j

        cost += dist.iloc[i, 20]
        routes[k].append(20)

    return routes, cost


def solve_optimized_solution(dist: DataFrame, demands, ntrucks, cap, depot=20, time_limit_seconds=30):
    if pywrapcp is None or routing_enums_pb2 is None:
        raise ImportError(
            "OR-Tools non e' installato. Installa la dipendenza con: "
            "pip install ortools"
        )

    distance_matrix = np.rint(dist.to_numpy()).astype(np.int64)
    np.fill_diagonal(distance_matrix, 0)

    scaled_demands = [int(round(float(value) * DEMAND_SCALE)) for value in demands]
    scaled_demands[depot] = 0
    scaled_capacity = int(round(float(cap) * DEMAND_SCALE))

    total_demand = sum(scaled_demands)
    total_capacity = ntrucks * scaled_capacity
    if total_demand > total_capacity:
        raise ValueError(
            f"Domanda totale {total_demand / DEMAND_SCALE:.2f} superiore alla "
            f"capacita totale {total_capacity / DEMAND_SCALE:.2f}."
        )

    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), ntrucks, depot)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(distance_matrix[from_node][to_node])

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return scaled_demands[from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,
        [scaled_capacity] * ntrucks,
        True,
        "Capacity",
    )

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.FromSeconds(time_limit_seconds)

    solution = routing.SolveWithParameters(search_parameters)
    if solution is None:
        raise RuntimeError("Nessuna soluzione trovata da OR-Tools.")

    routes = []
    for vehicle_id in range(ntrucks):
        index = routing.Start(vehicle_id)
        route = []
        while not routing.IsEnd(index):
            route.append(manager.IndexToNode(index))
            index = solution.Value(routing.NextVar(index))
        route.append(manager.IndexToNode(index))
        routes.append(route)

    return routes, solution.ObjectiveValue()


def load_demands(predictions_path, nodes_count):
    predizioni = pd.read_csv(predictions_path)
    richieste_array = []

    for i in range(nodes_count):
        richieste_array.append(float(predizioni[str(i)][0]))

    return richieste_array


def plot_routes(scatter, routes):
    fig, ax = plt.subplots(figsize=(10, 8))
    depot = scatter.iloc[DISTANZE_DEPOSITI_INDEX]
    customers = scatter.drop(scatter.index[DISTANZE_DEPOSITI_INDEX])
    colors = plt.get_cmap("tab10", len(routes))

    ax.scatter(
        x=customers["x"],
        y=customers["y"],
        color="lightgray",
        edgecolors="black",
        s=70,
        label="Clienti",
        zorder=2,
    )
    ax.scatter(
        x=[depot["x"]],
        y=[depot["y"]],
        color="red",
        marker="s",
        edgecolors="black",
        s=130,
        label="Deposito",
        zorder=4,
    )

    for truck_index, route in enumerate(routes):
        if len(route) <= 2:
            continue

        route_points = scatter.iloc[route]
        ax.plot(
            route_points["x"],
            route_points["y"],
            color=colors(truck_index),
            linewidth=2,
            marker="o",
            markersize=5,
            label=f"Camion {truck_index + 1}",
            zorder=3,
        )

    for _, row in scatter.iterrows():
        ax.annotate(
            int(row["node_id"]),
            (row["x"], row["y"]),
            textcoords="offset points",
            xytext=(4, 4),
            fontsize=8,
        )

    ax.set_title("Rotte ottimizzate dei camion")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5))
    fig.tight_layout()

    plt.show(block=True)


if __name__ == "__main__":
    df = pd.read_csv("fileCSV/mat52.csv", header=None, skipinitialspace=True)
    scatter = pd.read_csv(
        "fileCSV/customers_scatter.csv",
        sep=";",
        decimal=",",
        skipinitialspace=True,
    )
    scatter.columns = scatter.columns.str.strip()

    nodes_count = DISTANZE_DEPOSITI_INDEX + 1
    distanze_depositi_df = df.iloc[:nodes_count, :nodes_count]
    richieste_array = load_demands("predizioni.csv", nodes_count)

    greedy_routes, greedy_cost = initial_solution(distanze_depositi_df, richieste_array, 10, 50)
    optimized_routes, optimized_cost = solve_optimized_solution(
        distanze_depositi_df,
        richieste_array,
        ntrucks=10,
        cap=50,
        depot=DISTANZE_DEPOSITI_INDEX,
        time_limit_seconds=30,
    )

    print(f"Costo soluzione greedy: {greedy_cost}")
    print(f"Costo soluzione ottimizzata: {optimized_cost}")
    print("Rotte ottimizzate:")
    print(optimized_routes)

    plot_routes(scatter, optimized_routes)
