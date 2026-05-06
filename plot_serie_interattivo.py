from collections import defaultdict
import csv
from pathlib import Path

import matplotlib.pyplot as plt


INPUT_FILE = Path("serie_covid_new_per_idserie_feb_mar_apr_2020_ricostruiti.csv")
OUTPUT_DIR = Path("plot_serie_covid")
OUTPUT_FILE = OUTPUT_DIR / "grafico_unico_52_serie_feb_mar_apr_2020_ricostruite.png"
MONTHS_TO_HIGHLIGHT = {"Feb-20", "Mar-20", "Apr-20"}


def clean_key(row, wanted_key):
    for key in row:
        if key.strip() == wanted_key:
            return row[key].strip()
    raise KeyError(wanted_key)


def read_series(path):
    grouped = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            month = clean_key(row, "month")
            idserie = int(clean_key(row, "idserie"))
            grouped[idserie].append(
                {
                    "month": month,
                    "periodo": int(clean_key(row, "periodo")),
                    "val": float(clean_key(row, "val")),
                }
            )

    for rows in grouped.values():
        rows.sort(key=lambda item: item["periodo"])

    return dict(sorted(grouped.items()))


def plot_all_series(grouped):
    OUTPUT_DIR.mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(15, 8))

    reference_months = []
    for rows in grouped.values():
        reference_months = [row["month"] for row in rows]
        break

    for idserie, rows in grouped.items():
        months = [row["month"] for row in rows]
        values = [row["val"] for row in rows]

        ax.plot(months, values, linewidth=1.4, label=f"Serie {idserie:02d}")

    highlighted_positions = [
        index for index, month in enumerate(reference_months) if month in MONTHS_TO_HIGHLIGHT
    ]
    if highlighted_positions:
        ax.axvspan(
            min(highlighted_positions) - 0.5,
            max(highlighted_positions) + 0.5,
            color="gold",
            alpha=0.18,
            label="Mar-Apr-May 2020",
        )

    ax.set_title("52 serie Covid con Feb-Mar-Apr 2020 ricostruiti")
    ax.set_xlabel("Mese")
    ax.set_ylabel("Valore")
    ax.grid(True, alpha=0.3)
    ax.tick_params(axis="x", rotation=75, labelsize=8)
    ax.legend(
        loc="center left",
        bbox_to_anchor=(1.01, 0.5),
        fontsize=7,
        ncol=2,
        frameon=False,
    )
    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=150)
    plt.show()
    


def main():
    grouped = read_series(INPUT_FILE)
    if len(grouped) != 52:
        raise ValueError(f"Trovate {len(grouped)} serie invece di 52")

    plot_all_series(grouped)
    print(f"Plot unico salvato in: {OUTPUT_FILE.resolve()}")


if __name__ == "__main__":
    main()
