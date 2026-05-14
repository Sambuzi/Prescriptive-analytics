import random
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from depositi import DISTANZE_DEPOSITI_INDEX, initial_solution


N_TRUCKS = 10
TRUCK_CAPACITY = 50
ILS_ITERATIONS = 200
PERTURBATION_MOVES = 3
RANDOM_SEED = 7


def build_distance_matrix(dist):
    d = dist.to_numpy().copy()
    np.fill_diagonal(d, 0)
    return d


def route_cost(route, d):
    return sum(d[route[i], route[i + 1]] for i in range(len(route) - 1))


def solution_cost(routes, d):
    return sum(route_cost(route, d) for route in routes)


def route_load(route, requests, depot=DISTANZE_DEPOSITI_INDEX):
    return sum(requests[node] for node in route if node != depot)


def solution_loads(routes, requests):
    return [route_load(route, requests) for route in routes]


def load_requests(predictions_path, nodes_count, depot):
    predizioni = pd.read_csv(predictions_path)
    requests = [float(predizioni[str(i)][0]) for i in range(nodes_count)]
    requests[depot] = 0
    return requests


def two_opt_route(route, d):
    best_route = route[:]
    best_cost = route_cost(best_route, d)
    improved = True

    while improved:
        improved = False
        for i in range(1, len(best_route) - 2):
            for j in range(i + 1, len(best_route) - 1):
                candidate = best_route[:i] + list(reversed(best_route[i : j + 1])) + best_route[j + 1 :]
                candidate_cost = route_cost(candidate, d)
                if candidate_cost < best_cost:
                    best_route = candidate
                    best_cost = candidate_cost
                    improved = True
                    break
            if improved:
                break

    return best_route


def local_search(routes, requests, cap, d):
    routes = [route[:] for route in routes]

    for route_index, route in enumerate(routes):
        routes[route_index] = two_opt_route(route, d)

    best_cost = solution_cost(routes, d)
    improved = True

    while improved:
        improved = False
        loads = solution_loads(routes, requests)

        for from_route_index, from_route in enumerate(routes):
            for from_position in range(1, len(from_route) - 1):
                customer = from_route[from_position]
                customer_demand = requests[customer]

                for to_route_index, to_route in enumerate(routes):
                    if (
                        from_route_index != to_route_index
                        and loads[to_route_index] + customer_demand > cap
                    ):
                        continue

                    for to_position in range(1, len(to_route)):
                        if from_route_index == to_route_index and (
                            to_position == from_position or to_position == from_position + 1
                        ):
                            continue

                        candidate = [route[:] for route in routes]
                        moved = candidate[from_route_index].pop(from_position)
                        insert_position = to_position
                        if from_route_index == to_route_index and to_position > from_position:
                            insert_position -= 1
                        candidate[to_route_index].insert(insert_position, moved)

                        candidate_cost = solution_cost(candidate, d)
                        if candidate_cost < best_cost:
                            routes = candidate
                            best_cost = candidate_cost
                            improved = True
                            break
                    if improved:
                        break
                if improved:
                    break
            if improved:
                break

        if improved:
            continue

        loads = solution_loads(routes, requests)
        for first_route_index in range(len(routes)):
            for second_route_index in range(first_route_index + 1, len(routes)):
                first_route = routes[first_route_index]
                second_route = routes[second_route_index]

                for first_position in range(1, len(first_route) - 1):
                    for second_position in range(1, len(second_route) - 1):
                        first_customer = first_route[first_position]
                        second_customer = second_route[second_position]

                        first_load = loads[first_route_index] - requests[first_customer] + requests[second_customer]
                        second_load = loads[second_route_index] - requests[second_customer] + requests[first_customer]
                        if first_load > cap or second_load > cap:
                            continue

                        candidate = [route[:] for route in routes]
                        candidate[first_route_index][first_position] = second_customer
                        candidate[second_route_index][second_position] = first_customer

                        candidate_cost = solution_cost(candidate, d)
                        if candidate_cost < best_cost:
                            routes = candidate
                            best_cost = candidate_cost
                            improved = True
                            break
                    if improved:
                        break
                if improved:
                    break
            if improved:
                break

    for route_index, route in enumerate(routes):
        routes[route_index] = two_opt_route(route, d)

    return routes


def non_empty_route_indexes(routes):
    return [index for index, route in enumerate(routes) if len(route) > 2]


def perturb_solution(routes, requests, cap, rng, moves=PERTURBATION_MOVES):
    perturbed = [route[:] for route in routes]

    for _ in range(moves):
        loads = solution_loads(perturbed, requests)
        route_indexes = non_empty_route_indexes(perturbed)
        if len(route_indexes) < 2:
            break

        if rng.random() < 0.5:
            from_route_index = rng.choice(route_indexes)
            movable_positions = list(range(1, len(perturbed[from_route_index]) - 1))
            from_position = rng.choice(movable_positions)
            customer = perturbed[from_route_index][from_position]

            feasible_targets = [
                index
                for index in range(len(perturbed))
                if index == from_route_index or loads[index] + requests[customer] <= cap
            ]
            to_route_index = rng.choice(feasible_targets)
            to_position = rng.randint(1, len(perturbed[to_route_index]) - 1)

            moved = perturbed[from_route_index].pop(from_position)
            if from_route_index == to_route_index and to_position > from_position:
                to_position -= 1
            perturbed[to_route_index].insert(to_position, moved)
        else:
            first_route_index, second_route_index = rng.sample(route_indexes, 2)
            first_position = rng.randint(1, len(perturbed[first_route_index]) - 2)
            second_position = rng.randint(1, len(perturbed[second_route_index]) - 2)

            first_customer = perturbed[first_route_index][first_position]
            second_customer = perturbed[second_route_index][second_position]
            first_load = loads[first_route_index] - requests[first_customer] + requests[second_customer]
            second_load = loads[second_route_index] - requests[second_customer] + requests[first_customer]

            if first_load <= cap and second_load <= cap:
                perturbed[first_route_index][first_position] = second_customer
                perturbed[second_route_index][second_position] = first_customer

    return perturbed

# iteration local functions 
def iterated_local_search(initial_routes, requests, cap, d, iterations=ILS_ITERATIONS, seed=RANDOM_SEED):
    rng = random.Random(seed)
    current = local_search(initial_routes, requests, cap, d)
    current_cost = solution_cost(current, d)
    best = [route[:] for route in current]
    best_cost = current_cost
    history = [best_cost]

    for _ in range(iterations):
        candidate = perturb_solution(current, requests, cap, rng)
        candidate = local_search(candidate, requests, cap, d)
        candidate_cost = solution_cost(candidate, d)

        if candidate_cost <= current_cost:
            current = candidate
            current_cost = candidate_cost

        if candidate_cost < best_cost:
            best = [route[:] for route in candidate]
            best_cost = candidate_cost

        history.append(best_cost)

    return best, best_cost, history

# plot function
def plot_routes(scatter, routes):
    max_route_node = max(max(route) for route in routes)
    scatter = scatter.iloc[: max_route_node + 1].copy()

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

    ax.set_title("Rotte Iterated Local Search dei camion")
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
    d = build_distance_matrix(distanze_depositi_df)
    requests = load_requests("predizioni.csv", nodes_count, DISTANZE_DEPOSITI_INDEX)

    initial_routes, _ = initial_solution(
        distanze_depositi_df,
        requests,
        N_TRUCKS,
        TRUCK_CAPACITY,
    )
    initial_cost = solution_cost(initial_routes, d)

    local_routes = local_search(initial_routes, requests, TRUCK_CAPACITY, d)
    local_cost = solution_cost(local_routes, d)

    best_routes, best_cost, history = iterated_local_search(
        initial_routes,
        requests,
        TRUCK_CAPACITY,
        d,
        iterations=ILS_ITERATIONS,
        seed=RANDOM_SEED,
    )

    print(f"Costo iniziale: {initial_cost}")
    print(f"Costo local search: {local_cost}")
    print(f"Costo iterated local search: {best_cost}")
    print(f"Miglioramenti trovati: {len(set(history)) - 1}")
    print("Rotte Iterated Local Search:")
    print(best_routes)

    plot_routes(scatter, best_routes)
