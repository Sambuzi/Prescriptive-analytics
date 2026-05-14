import numpy as np
from pandas import DataFrame

from goto import goto


# >>> DA MIGLIORARE SCAMBI FRA ELEMENTI DI UNA STESSA ROUTE <<<<<<<<<<<<<<
def delta_cost(routes, k, k1, i, j, d):
    deltak = 0
    deltak1 = 0
    if (k != k1):
        # inserisco i prima di j in k1
        deltak1 -= d[routes[k1][j - 1], routes[k1][j]]
        deltak1 += d[routes[k1][j - 1], routes[k][i]] + d[routes[k][i], routes[k1][j]]
        # tolgo i da k
        deltak -= d[routes[k][i - 1], routes[k][i]]
        deltak -= d[routes[k][i], routes[k][i + 1]]
        deltak += d[routes[k][i - 1], routes[k][i + 1]]
    elif (k == k1 and (j - i) != 1):
        deltak -= (d[routes[k][i - 1], routes[k][i]] + d[routes[k][i], routes[k][i + 1]] +
                   d[routes[k][j - 1], routes[k][j]])
        deltak += d[routes[k][i - 1], routes[k][i + 1]] + d[routes[k][j - 1], routes[k][i]] + d[
            routes[k][i], routes[k][j]]

    delta = deltak1 + deltak
    return delta, deltak, deltak1


# prende il nodo dalla pos i della route k e lo mette prima della pos j della route k1
def delta_swap(routes, k, k1, i, j):
    node = routes[k].pop(i)
    if (k != k1 or i > j):
        routes[k1].insert(j, node)
    else:
        routes[k1].insert(j - 1, node)  # ne avevo tolto uno prima
    return


@goto
def local_search(routes, requests, cap, d):
    routes = [route[:] for route in routes]
    loads = np.zeros(len(routes))
    rcosts = np.zeros(len(routes))
    # ricostruisce carichi e costi della soluzione iniziale
    for k in range(len(routes)):
        for i in range(1, len(routes[k])):
            loads[k] += requests[routes[k][i]]
            rcosts[k] += d[routes[k][i - 1]][routes[k][i]]

    cont = 0
    label.repeat
    for k in range(len(routes)):
        for i in range(1, len(routes[k]) - 1):  # elemento da spostare
            node = routes[k][i]
            for k1 in range(len(routes)):
                for j in range(1, len(routes[k1])):  # riposiziono prima di j in k1
                    if (k != k1 or abs(i - j) > 0):  # se route diverse o nodi diversi stessa route
                        if (k == k1 or loads[k1] + requests[node] <= cap):  # TODO: spostamenti stessa route
                            cont += 1
                            if (cont > 1000):
                                goto.end
                            delta, deltak, deltak1 = delta_cost(routes, k, k1, i, j, d)
                            if delta < -0.001:
                                # print(f"{cont}) scambio {i} - {j} variazione {delta}")
                                delta_swap(routes, k, k1, i, j)
                                loads[k] -= requests[node]
                                loads[k1] += requests[node]
                                rcosts[k] += deltak  # deltak è negativo
                                rcosts[k1] += deltak1
                                # print(f"{cont}) scambio {routes[k]}, {routes[k1]}, delta {delta}")
                                goto.repeat
                    if (j == len(routes[k1])):
                        print("boh")
    label.end
    return routes


def copy_routes(routes):
    return [route[:] for route in routes]


def perturb_routes(routes, requests, cap, rng, moves=3):
    perturbed = copy_routes(routes)

    for _ in range(moves):
        non_empty_routes = [
            route_index
            for route_index, route in enumerate(perturbed)
            if len(route) > 2
        ]
        if len(non_empty_routes) < 2:
            break

        loads = np.array([
            sum(requests[node] for node in route if node != DISTANZE_DEPOSITI_INDEX)
            for route in perturbed
        ])

        if rng.random() < 0.5:
            from_route_index = rng.choice(non_empty_routes)
            from_position = rng.integers(1, len(perturbed[from_route_index]) - 1)
            node = perturbed[from_route_index][from_position]

            feasible_targets = [
                route_index
                for route_index in range(len(perturbed))
                if route_index == from_route_index or loads[route_index] + requests[node] <= cap
            ]
            to_route_index = rng.choice(feasible_targets)
            to_position = rng.integers(1, len(perturbed[to_route_index]))

            moved_node = perturbed[from_route_index].pop(from_position)
            if from_route_index == to_route_index and to_position > from_position:
                to_position -= 1
            perturbed[to_route_index].insert(to_position, moved_node)
        else:
            first_route_index, second_route_index = rng.choice(non_empty_routes, size=2, replace=False)
            first_position = rng.integers(1, len(perturbed[first_route_index]) - 1)
            second_position = rng.integers(1, len(perturbed[second_route_index]) - 1)

            first_node = perturbed[first_route_index][first_position]
            second_node = perturbed[second_route_index][second_position]
            first_load = loads[first_route_index] - requests[first_node] + requests[second_node]
            second_load = loads[second_route_index] - requests[second_node] + requests[first_node]

            if first_load <= cap and second_load <= cap:
                perturbed[first_route_index][first_position] = second_node
                perturbed[second_route_index][second_position] = first_node

    return perturbed


def iteratedLocalSearch(routes, requests, cap, d: np.ndarray, iterations, alpha):
    rng = np.random.default_rng(7)

    current = local_search(copy_routes(routes), requests, cap, d)
    current_cost = compute_cost(current, d)
    best = copy_routes(current)
    best_cost = current_cost

    for _ in range(iterations):
        perturbed_routes = perturb_routes(current, requests, cap, rng, moves=max(1, int(alpha)))

        random_matrix = 1 + (alpha / 10) * rng.random(size=d.shape)
        np.fill_diagonal(random_matrix, 1)
        perturbed_distances = d * random_matrix

        candidate = local_search(perturbed_routes, requests, cap, perturbed_distances)
        candidate = local_search(candidate, requests, cap, d)
        candidate_cost = compute_cost(candidate, d)

        if candidate_cost <= current_cost:
            current = copy_routes(candidate)
            current_cost = candidate_cost

        if candidate_cost < best_cost:
            best = copy_routes(candidate)
            best_cost = candidate_cost

    return best

DISTANZE_DEPOSITI_INDEX = 20

DISTANZE_CLIENTI_DEPOSITO_INDEX = 21
def compute_cost(routes, d):
    total = 0
    for route in routes:
        for i in range(len(route) - 1):
            total += d[route[i], route[i + 1]]
    return total

# tra le colonne della matrice
# guardare quanto fa la somma => somma totale
# somma totale * 1.3 / 25

def find_min_index_in_row(dist: DataFrame, visited, i):
    min_cost = 999999
    min_index = -1
    for row in range(len(dist.iloc[i, :].values)):
        x = 0
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


import pandas as pd
import matplotlib.pyplot as plt

if __name__ == "__main__":
    df = pd.read_csv("fileCSV/mat52.csv", header=None, skipinitialspace=True)
    scatter = pd.read_csv(
        "fileCSV/customers_scatter.csv",
        sep=";",
        decimal=",",
        skipinitialspace=True,
    )
    scatter.columns = scatter.columns.str.strip()

    distanze_depositi_df = df.iloc[:DISTANZE_DEPOSITI_INDEX + 1, :DISTANZE_DEPOSITI_INDEX + 1]
    distanze_matrix = distanze_depositi_df.to_numpy().copy()
    np.fill_diagonal(distanze_matrix, 0)
    scatter = scatter.iloc[:DISTANZE_DEPOSITI_INDEX + 1].copy()

    predizioni = pd.read_csv('predizioni.csv')
    richieste_array = []
    domanda_totale = 0
    for i in range(DISTANZE_DEPOSITI_INDEX + 1):
        domanda_totale += (predizioni[str(i)] / 5)
        num = 0
        num += predizioni[str(i)][0]
        richieste_array.append(num)

    richieste_array[DISTANZE_DEPOSITI_INDEX] = 0
    domanda_totale = np.ceil(domanda_totale)

    def plot_solution(title, routes):
        plt.figure()
        plt.title(title)
        depot = scatter.iloc[DISTANZE_DEPOSITI_INDEX]
        customers = scatter.drop(scatter.index[DISTANZE_DEPOSITI_INDEX])

        plt.scatter(
            x=customers["x"],
            y=customers["y"],
            color="lightgray",
            edgecolors="black",
            s=70,
            label="Clienti",
            zorder=2,
        )
        plt.scatter(
            x=[depot["x"]],
            y=[depot["y"]],
            color="red",
            marker="s",
            edgecolors="black",
            s=130,
            label="Deposito",
            zorder=4,
        )

        colors = plt.get_cmap("tab10", len(routes))
        for truck_index, route in enumerate(routes):
            if len(route) <= 2:
                continue

            route_points = scatter.iloc[route]
            plt.plot(
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
            plt.annotate(
                int(row["node_id"]),
                (row["x"], row["y"]),
                textcoords="offset points",
                xytext=(4, 4),
                fontsize=8,
            )

        plt.xlabel("x")
        plt.ylabel("y")
        plt.grid(True, alpha=0.25)
        plt.legend(loc="center left", bbox_to_anchor=(1.02, 0.5))
        plt.tight_layout()


    print(scatter.iloc[:,:].values[0]) # [ 1.    43.008 60.738]

    sols, _ = initial_solution(distanze_depositi_df, richieste_array, 5, 100)

    print(sols)
    print(f"initial cost = {compute_cost(sols, distanze_matrix)}")
    plot_solution("Initial", sols)

    routes = local_search(
        sols,
        np.array(richieste_array),
        100, distanze_matrix
        )

    print(routes)
    print(f"local search cost = {compute_cost(routes, distanze_matrix)}")
    plot_solution("Local Search", routes)

    iterated_routes = iteratedLocalSearch(
        sols,
        np.array(richieste_array),
        100, distanze_matrix,
        200,
        3
        )

    print(iterated_routes)
    print(f"iterated local search cost = {compute_cost(iterated_routes, distanze_matrix)}")
    plot_solution("Iterated Local Search", iterated_routes)

    plt.show(block=True)
