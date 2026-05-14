import numpy as np
from pandas import DataFrame

DISTANZE_DEPOSITI_INDEX=20

DISTANZE_CLIENTI_DEPOSITO_INDEX=21

# tra le colonne della matrice
# guardare quanto fa la somma => somma totale
# somma totale * 1.3 / 25

def find_min_index_in_row(dist: DataFrame, visited, i):
    min_cost = 999999
    min_index = -1
    for row in range(len(dist.iloc[i,:].values)):
        x = 0
        if dist.iloc[i,:].values[row] < min_cost and not visited[row]:
            min_cost = dist.iloc[i,:].values[row]
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

            if j == -1 or (load + demands[j]  > cap):
                break

            visited[j] = True
            routes[k].append(j)
            load += demands[j]           # Bug 1 fixed: scalar, not demands[j][0]
            cost += dist.iloc[i, j]      # Bug 2 fixed: accumulate edge cost directly
            i = j

        # Add return-to-depot cost
        cost += dist.iloc[i, 20]
        routes[k].append(20)

    return routes, cost
import pandas as pd
import matplotlib.pyplot as plt
if __name__ == "__main__":
    df = pd.read_csv('fileCSV/mat52.csv', header=None, skipinitialspace=True)
    scatter = pd.read_csv(
        'fileCSV/customers_scatter.csv',
        sep=';',
        decimal=',',
        skipinitialspace=True,
    )
    scatter.columns = scatter.columns.str.strip()

    distanze_depositi_df = df.iloc[:DISTANZE_DEPOSITI_INDEX + 1 , :DISTANZE_DEPOSITI_INDEX + 1]

    predizioni = pd.read_csv('predizioni.csv')
    richieste_array = []
    sum = 0
    for i in range(DISTANZE_DEPOSITI_INDEX + 1):
        sum += (predizioni[str(i)] / 5)
        num = 0
        num += predizioni[str(i)][0]
        richieste_array.append(num)


    sum = np.ceil(sum)

    print(type(richieste_array[0]))

    sol, _ = initial_solution(distanze_depositi_df, richieste_array, 10, 50)

    print(sol)

    fig, ax = plt.subplots(figsize=(10, 8))
    depot = scatter.iloc[DISTANZE_DEPOSITI_INDEX]
    customers = scatter.drop(scatter.index[DISTANZE_DEPOSITI_INDEX])
    colors = plt.get_cmap('tab10', len(sol))

    ax.scatter(
        x=customers['x'],
        y=customers['y'],
        color='lightgray',
        edgecolors='black',
        s=70,
        label='Clienti',
        zorder=2,
    )
    ax.scatter(
        x=[depot['x']],
        y=[depot['y']],
        color='red',
        marker='s',
        edgecolors='black',
        s=130,
        label='Deposito',
        zorder=4,
    )

    for truck_index, route in enumerate(sol):
        if len(route) <= 2:
            continue

        route_points = scatter.iloc[route]
        ax.plot(
            route_points['x'],
            route_points['y'],
            color=colors(truck_index),
            linewidth=2,
            marker='o',
            markersize=5,
            label=f'Camion {truck_index + 1}',
            zorder=3,
        )

    for _, row in scatter.iterrows():
        ax.annotate(
            int(row['node_id']),
            (row['x'], row['y']),
            textcoords='offset points',
            xytext=(4, 4),
            fontsize=8,
        )

    ax.set_title('Rotte iniziali dei camion')
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.grid(True, alpha=0.25)
    ax.legend(loc='center left', bbox_to_anchor=(1.02, 0.5))
    fig.tight_layout()

    plt.show(block=True)

