from collections import defaultdict
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


INPUT_FILE = Path("serie_covid_new.csv")
GROUPED_DIR = Path("serie_covid_raggruppate")
GROUPED_FILE = Path("serie_covid_new_per_idserie.csv")
FILTERED_FILE = Path("serie_covid_new_per_idserie_senza_mar_apr_may_2020.csv")
PIVOT_FILE = Path("serie_covid_new_raggruppate.csv")
PLOTS_DIR = Path("plot_serie_covid")
ALL_SERIES_PLOT = PLOTS_DIR / "tutte_le_52_serie.png"
MONTHS_TO_REMOVE = {"Mar-20", "Apr-20", "May-20"}


def clean_row(row):
    return {
        "idserie": int(row["idserie"].strip()),
        "month": row[" month "].strip(),
        "periodo": int(row[" periodo"].strip()),
        "val": int(row[" val"].strip()),
    }


def read_series(path):
    grouped = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for raw_row in reader:
            row = clean_row(raw_row)
            grouped[row["idserie"]].append(row)

    for rows in grouped.values():
        rows.sort(key=lambda item: item["periodo"])

    return dict(sorted(grouped.items()))


def write_grouped_files(grouped):
    GROUPED_DIR.mkdir(exist_ok=True)
    fieldnames = ["idserie", "month", "periodo", "val"]

    for idserie, rows in grouped.items():
        output_path = GROUPED_DIR / f"serie_{idserie:02d}.csv"
        with output_path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


def write_grouped_file(grouped):
    fieldnames = ["idserie", "month", "periodo", "val"]
    with GROUPED_FILE.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for rows in grouped.values():
            writer.writerows(rows)


def write_filtered_file(grouped):
    fieldnames = ["idserie", "month", "periodo", "val"]
    with FILTERED_FILE.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for rows in grouped.values():
            filtered_rows = [row for row in rows if row["month"] not in MONTHS_TO_REMOVE]
            writer.writerows(filtered_rows)


def filtered_grouped(grouped):
    return {
        idserie: [row for row in rows if row["month"] not in MONTHS_TO_REMOVE]
        for idserie, rows in grouped.items()
    }


def write_pivot(grouped):
    periods = {}
    for rows in grouped.values():
        for row in rows:
            periods[row["periodo"]] = row["month"]

    fieldnames = ["periodo", "month"] + [f"serie_{idserie:02d}" for idserie in grouped]
    with PIVOT_FILE.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for periodo in sorted(periods):
            output_row = {"periodo": periodo, "month": periods[periodo]}
            for idserie, rows in grouped.items():
                value_by_period = {row["periodo"]: row["val"] for row in rows}
                output_row[f"serie_{idserie:02d}"] = value_by_period.get(periodo, "")
            writer.writerow(output_row)


def plot_series(grouped):
    PLOTS_DIR.mkdir(exist_ok=True)

    for idserie, rows in grouped.items():
        months = [row["month"] for row in rows]
        values = [row["val"] for row in rows]

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(months, values, marker="o", linewidth=1.8, markersize=3)
        ax.set_title(f"Serie {idserie:02d}")
        ax.set_xlabel("Mese")
        ax.set_ylabel("Valore")
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis="x", rotation=75, labelsize=7)
        fig.tight_layout()
        fig.savefig(PLOTS_DIR / f"serie_{idserie:02d}.png", dpi=150)
        plt.close(fig)

    fig, axes = plt.subplots(13, 4, figsize=(22, 28), sharex=True)
    for ax, (idserie, rows) in zip(axes.ravel(), grouped.items()):
        months = [row["month"] for row in rows]
        values = [row["val"] for row in rows]
        ax.plot(months, values, linewidth=1.1)
        ax.set_title(f"Serie {idserie:02d}", fontsize=8)
        ax.grid(True, alpha=0.25)
        ax.tick_params(axis="both", labelsize=6)

    for ax in axes[-1]:
        ax.tick_params(axis="x", rotation=75)

    fig.suptitle("52 serie Covid senza Mar-20, Apr-20, May-20", fontsize=16)
    fig.tight_layout(rect=(0, 0, 1, 0.99))
    fig.savefig(ALL_SERIES_PLOT, dpi=150)
    plt.close(fig)


def main():
    grouped = read_series(INPUT_FILE)
    if len(grouped) != 52:
        raise ValueError(f"Trovate {len(grouped)} serie invece di 52")

    write_grouped_files(grouped)
    write_grouped_file(grouped)
    write_filtered_file(grouped)
    plot_series(filtered_grouped(grouped))

    print(f"Serie raggruppate: {len(grouped)}")
    print(f"File raggruppato per idserie: {GROUPED_FILE.resolve()}")
    print(f"File senza Mar-20, Apr-20, May-20: {FILTERED_FILE.resolve()}")
    print(f"File separati: {GROUPED_DIR.resolve()}")
    print(f"Plot singoli: {PLOTS_DIR.resolve()}")
    print(f"Plot unico: {ALL_SERIES_PLOT.resolve()}")

    try:
        write_pivot(grouped)
        print(f"File pivot: {PIVOT_FILE.resolve()}")
    except PermissionError:
        print(f"File pivot non aggiornato perche' e' aperto o bloccato: {PIVOT_FILE.resolve()}")


if __name__ == "__main__":
    main()
