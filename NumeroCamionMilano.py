
from pathlib import Path
from math import ceil

import matplotlib.pyplot as plt
import numpy as np


INPUT_FILE = Path("mat52.csv")
N_SERIE = 20
NUMERI_CAMION = list(range(N_SERIE))


def main():
    matrice_distanze = np.loadtxt(INPUT_FILE, delimiter=",")

    if matrice_distanze.shape[0] < N_SERIE or matrice_distanze.shape[1] < N_SERIE:
        raise ValueError(
            f"La matrice ha dimensione {matrice_distanze.shape}, non basta per estrarre {N_SERIE}x{N_SERIE}"
        )

    matrice_21 = matrice_distanze[:N_SERIE, :N_SERIE]

    print(f"Matrice originale: {matrice_distanze.shape[0]} x {matrice_distanze.shape[1]}")
    print(f"Sottomatrice usata: {N_SERIE} x {N_SERIE}")
    print(f"Numeri camion usati: {NUMERI_CAMION}")
    print(matrice_21.astype(int))

    somme_colonne = matrice_21.sum(axis=0)
    somma_totale = somme_colonne.sum()
    numero_camion = somma_totale * 1.3 / 25
    numero_camion_intero = ceil(numero_camion)

    matrice_senza_diagonale = matrice_21.copy()
    np.fill_diagonal(matrice_senza_diagonale, 0)
    somme_colonne_senza_diagonale = matrice_senza_diagonale.sum(axis=0)
    somma_totale_senza_diagonale = somme_colonne_senza_diagonale.sum()
    numero_camion_senza_diagonale = somma_totale_senza_diagonale * 1.3 / 25
    numero_camion_senza_diagonale_intero = ceil(numero_camion_senza_diagonale)

    print("\nSomma per colonna, con diagonale:")
    for camion, somma in zip(NUMERI_CAMION, somme_colonne):
        print(f"Camion {camion}: {somma:.0f}")

    print(f"\nSomma totale colonne: {somma_totale:.0f}")
    print(f"Numero camion = somma totale * 1.3 / 25 = {numero_camion:.2f}")
    print(f"Numero camion arrotondato per eccesso: {numero_camion_intero}")

    print("\nSomma per colonna, senza diagonale:")
    for camion, somma in zip(NUMERI_CAMION, somme_colonne_senza_diagonale):
        print(f"Camion {camion}: {somma:.0f}")

    print(f"\nSomma totale colonne senza diagonale: {somma_totale_senza_diagonale:.0f}")
    print(
        "Numero camion senza diagonale = "
        f"somma totale senza diagonale * 1.3 / 25 = {numero_camion_senza_diagonale:.2f}"
    )
    print(f"Numero camion senza diagonale arrotondato per eccesso: {numero_camion_senza_diagonale_intero}")

    matrice_plot = matrice_21.astype(float).copy()
    np.fill_diagonal(matrice_plot, np.nan)

    fig, ax = plt.subplots(figsize=(9, 8))
    image = ax.imshow(matrice_plot, cmap="viridis")

    ax.set_title(f"Matrice delle distanze {N_SERIE} x {N_SERIE}")
    ax.set_xlabel("Camion")
    ax.set_ylabel("Camion")
    ax.set_xticks(range(N_SERIE))
    ax.set_yticks(range(N_SERIE))
    ax.set_xticklabels(NUMERI_CAMION)
    ax.set_yticklabels(NUMERI_CAMION)

    for row in range(N_SERIE):
        for col in range(N_SERIE):
            if row != col:
                ax.text(
                    col,
                    row,
                    f"{int(matrice_21[row, col])}",
                    ha="center",
                    va="center",
                    fontsize=6,
                    color="white" if matrice_plot[row, col] > np.nanmean(matrice_plot) else "black",
                )

    fig.colorbar(image, ax=ax, label="Distanza")
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
