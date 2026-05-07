import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


INPUT_FILE = Path("customers_scatter.CSV")
OUTPUT_FILE = Path("customers_scatter_plot.png")


def parse_decimal(value):
    return float(value.strip().replace(",", "."))


def read_customers(path):
    customers = []
    with path.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=";")
        reader.fieldnames = [field.strip() for field in reader.fieldnames]

        for row in reader:
            cleaned = {key.strip(): value for key, value in row.items()}
            customers.append(
                {
                    "node_id": int(cleaned["node_id"].strip()),
                    "x": parse_decimal(cleaned["x"]),
                    "y": parse_decimal(cleaned["y"]),
                }
            )

    return customers


def plot_customers(customers, output_path):
    x_values = [customer["x"] for customer in customers]
    y_values = [customer["y"] for customer in customers]

    fig, ax = plt.subplots(figsize=(9, 7))
    ax.scatter(
        x_values,
        y_values,
        s=85,
        color="#2563eb",
        edgecolor="#0f172a",
        linewidth=0.8,
        alpha=0.9,
    )

    for customer in customers:
        ax.annotate(
            str(customer["node_id"]),
            (customer["x"], customer["y"]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
            color="#111827",
        )

    ax.set_title("Distribuzione clienti", fontsize=16, pad=14)
    ax.set_xlabel("Coordinata X")
    ax.set_ylabel("Coordinata Y")
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.45)
    ax.set_axisbelow(True)

    padding = 5
    ax.set_xlim(min(x_values) - padding, max(x_values) + padding)
    ax.set_ylim(min(y_values) - padding, max(y_values) + padding)

    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def main():
    customers = read_customers(INPUT_FILE)
    plot_customers(customers, OUTPUT_FILE)
    print(f"Creato {OUTPUT_FILE} con {len(customers)} clienti.")


if __name__ == "__main__":
    main()
