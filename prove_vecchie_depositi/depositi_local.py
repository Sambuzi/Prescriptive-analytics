import random
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from prove_vecchie_depositi.depositi import DISTANZE_DEPOSITI_INDEX, initial_solution


DISTANZE_DEPOSITI_INDEX = 20
N_TRUCKS = 10
TRUCK_CAPACITY = 50


def route_cost(route, d):
   cost = 0
   for i in range(len(route) - 1):
      cost += d[route[i], route[i + 1]]
   return cost


def solution_cost(routes, d):
   return sum(route_cost(route, d) for route in routes)


def load_requests(predictions_path, nodes_count, depot):
   predizioni = pd.read_csv(predictions_path)
   requests = []
   for i in range(nodes_count):
      requests.append(float(predizioni[str(i)][0]))
   requests[depot] = 0
   return requests


def plot_routes(scatter, routes):
   max_route_node = max(max(route) for route in routes)
   scatter = scatter.iloc[:max_route_node + 1].copy()

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

   ax.set_title("Rotte local search dei camion")
   ax.set_xlabel("x")
   ax.set_ylabel("y")
   ax.grid(True, alpha=0.25)
   ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5))
   fig.tight_layout()

   plt.show(block=True)

# >>> DA MIGLIORARE SCAMBI FRA ELEMENTI DI UNA STESSA ROUTE <<<<<<<<<<<<<<
def delta_cost(routes, k, k1, i, j, d):
   deltak  = 0
   deltak1 = 0
   if(k != k1):
      # inserisco i prima di j in k1
      deltak1 -= d[routes[k1][j-1],routes[k1][j]]
      deltak1 += d[routes[k1][j-1],routes[k][i]] + d[routes[k][i],routes[k1][j]]
      # tolgo i da k
      deltak -= d[routes[k][i-1],routes[k][i]]
      deltak -= d[routes[k][i],routes[k][i+1]]
      deltak += d[routes[k][i-1],routes[k][i+1]]
   elif(k == k1 and (j-i)!=1):
      deltak -= (d[routes[k][i-1],routes[k][i]] + d[routes[k][i],routes[k][i+1]] +
                 d[routes[k][j-1],routes[k][j]])
      deltak += d[routes[k][i-1],routes[k][i+1]] + d[routes[k][j-1],routes[k][i]] + d[routes[k][i],routes[k][j]]

   delta = deltak1 + deltak
   return delta, deltak, deltak1

# prende il nodo dalla pos i della route k e lo mette prima della pos j della route k1
def delta_swap(routes, k, k1, i, j):
   node = routes[k].pop(i)
   if(k!=k1 or i>j): routes[k1].insert(j, node)
   else: routes[k1].insert(j-1, node) # ne avevo tolto uno prima
   return

def local_search(routes, requests, cap, d):
   loads  = np.zeros(len(routes))
   rcosts = np.zeros(len(routes))
   # ricostruisce carichi e costi della soluzione iniziale
   for k in range(len(routes)):
      for i in range(1,len(routes[k])):
         loads[k]  += requests[routes[k][i]]
         rcosts[k] += d[routes[k][i-1]][routes[k][i]]
   
   cont = 0
   restart = True
   while restart:
      restart = False
      for k in range(len(routes)):
         for i in range(1,len(routes[k])-1): # elemento da spostare
            node = routes[k][i]
            for k1 in range(len(routes)):
               for j in range(1,len(routes[k1])): # riposiziono prima di j in k1
                  if(k!=k1 or abs(i-j)>0): # se route diverse o nodi diversi stessa route
                     if(k == k1 or loads[k1]+requests[node] <= cap): # TODO: spostamenti stessa route
                        cont +=1
                        if (cont > 1000):
                           return routes
                        delta, deltak, deltak1 = delta_cost(routes, k, k1, i, j, d)
                        if delta < -0.001:
                           #print(f"{cont}) scambio {i} - {j} variazione {delta}")
                           delta_swap(routes, k, k1, i, j)
                           loads[k]  -= requests[node]
                           loads[k1] += requests[node]
                           rcosts[k] += deltak   # deltak è negativo
                           rcosts[k1]+= deltak1
                           #print(f"{cont}) scambio {routes[k]}, {routes[k1]}, delta {delta}")
                           restart = True
                           break
                  if (j == len(routes[k1])):
                     print("boh")
               if restart:
                  break
            if restart:
               break
         if restart:
            break
   return routes


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
   d = distanze_depositi_df.to_numpy()
   np.fill_diagonal(d, 0)

   requests = load_requests("predizioni.csv", nodes_count, DISTANZE_DEPOSITI_INDEX)
   routes, _ = initial_solution(
      distanze_depositi_df,
      requests,
      N_TRUCKS,
      TRUCK_CAPACITY,
   )

   initial_cost = solution_cost(routes, d)
   improved_routes = local_search(routes, requests, TRUCK_CAPACITY, d)
   improved_cost = solution_cost(improved_routes, d)

   print(f"Costo iniziale: {initial_cost}")
   print(f"Costo dopo local search: {improved_cost}")
   print("Rotte dopo local search:")
   print(improved_routes)

   plot_routes(scatter, improved_routes)
