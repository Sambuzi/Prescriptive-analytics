from collections import defaultdict
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from statsmodels.tsa.holtwinters import ExponentialSmoothing


INPUT_FILE = Path("serie_covid_new_per_idserie_feb_mar_apr_2020_ricostruiti.csv")
FORECAST_FILE = Path("previsioni_ultimi_3_mesi_per_serie.csv")
METRICS_FILE = Path("metriche_previsioni_ultimi_3_mesi.csv")
PLOT_FILE = Path("plot_serie_covid") / "previsioni_ultimi_3_mesi_52_serie.png"
TEST_MONTHS = 3
SEASONAL_PERIODS = 12


def clean_value(row, wanted_key):
    for key, value in row.items():
        if key.strip() == wanted_key:
            return value.strip()
    raise KeyError(wanted_key)


def read_series(path):
    grouped = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            idserie = int(clean_value(row, "idserie"))
            grouped[idserie].append(
                {
                    "idserie": idserie,
                    "month": clean_value(row, "month"),
                    "periodo": int(clean_value(row, "periodo")),
                    "val": float(clean_value(row, "val")),
                }
            )

    for rows in grouped.values():
        rows.sort(key=lambda item: item["periodo"])

    return dict(sorted(grouped.items()))


def seasonal_naive_forecast(train_values, steps):
    return [train_values[-SEASONAL_PERIODS + i] for i in range(steps)]


def forecast_series(rows):
    train_rows = rows[:-TEST_MONTHS]
    test_rows = rows[-TEST_MONTHS:]
    train_values = [row["val"] for row in train_rows]

    try:
        model = ExponentialSmoothing(
            train_values,
            trend="add",
            seasonal="add",
            seasonal_periods=SEASONAL_PERIODS,
            initialization_method="estimated",
        )
        fitted = model.fit(optimized=True)
        predictions = [round(value, 2) for value in fitted.forecast(TEST_MONTHS)]
        model_name = "holt_winters_additive"
    except Exception:
        predictions = [round(value, 2) for value in seasonal_naive_forecast(train_values, TEST_MONTHS)]
        model_name = "seasonal_naive"

    forecast_rows = []
    for test_row, prediction in zip(test_rows, predictions):
        actual = test_row["val"]
        error = round(actual - prediction, 2)
        abs_error = round(abs(error), 2)
        ape = round(abs_error / actual * 100, 2) if actual != 0 else ""

        forecast_rows.append(
            {
                "idserie": test_row["idserie"],
                "month": test_row["month"],
                "periodo": test_row["periodo"],
                "actual": actual,
                "forecast": prediction,
                "error": error,
                "abs_error": abs_error,
                "ape_percent": ape,
                "model": model_name,
            }
        )

    return forecast_rows


def write_forecasts(rows):
    fieldnames = [
        "idserie",
        "month",
        "periodo",
        "actual",
        "forecast",
        "error",
        "abs_error",
        "ape_percent",
        "model",
    ]
    with FORECAST_FILE.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_metrics(forecast_rows):
    metrics = []
    grouped = defaultdict(list)
    for row in forecast_rows:
        grouped[row["idserie"]].append(row)

    for idserie, rows in sorted(grouped.items()):
        mae = sum(row["abs_error"] for row in rows) / len(rows)
        mape_values = [row["ape_percent"] for row in rows if row["ape_percent"] != ""]
        mape = sum(mape_values) / len(mape_values) if mape_values else ""
        metrics.append(
            {
                "idserie": idserie,
                "mae": round(mae, 2),
                "mape_percent": round(mape, 2) if mape != "" else "",
                "model": rows[0]["model"],
            }
        )

    with METRICS_FILE.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["idserie", "mae", "mape_percent", "model"])
        writer.writeheader()
        writer.writerows(metrics)

    return metrics


def plot_forecasts(series, forecast_rows):
    PLOT_FILE.parent.mkdir(exist_ok=True)
    forecast_by_series = defaultdict(list)
    for row in forecast_rows:
        forecast_by_series[row["idserie"]].append(row)

    fig, ax = plt.subplots(figsize=(15, 8))

    for idserie, rows in series.items():
        months = [row["month"] for row in rows]
        values = [row["val"] for row in rows]
        test_months = [row["month"] for row in forecast_by_series[idserie]]
        predictions = [row["forecast"] for row in forecast_by_series[idserie]]

        line = ax.plot(months, values, linewidth=1.0, alpha=0.55)[0]
        ax.plot(test_months, predictions, linestyle="--", linewidth=1.6, color=line.get_color())

    ax.axvspan(len(months) - TEST_MONTHS - 0.5, len(months) - 0.5, color="gold", alpha=0.15)
    ax.set_title("Previsione ultimi 3 mesi per 52 serie")
    ax.set_xlabel("Mese")
    ax.set_ylabel("Valore")
    ax.grid(True, alpha=0.3)
    ax.tick_params(axis="x", rotation=75, labelsize=8)
    fig.tight_layout()
    fig.savefig(PLOT_FILE, dpi=150)
    plt.close(fig)


def main():
    series = read_series(INPUT_FILE)
    if len(series) != 52:
        raise ValueError(f"Trovate {len(series)} serie invece di 52")

    forecast_rows = []
    for rows in series.values():
        forecast_rows.extend(forecast_series(rows))

    metrics = write_metrics(forecast_rows)
    write_forecasts(forecast_rows)
    plot_forecasts(series, forecast_rows)

    overall_mae = sum(row["abs_error"] for row in forecast_rows) / len(forecast_rows)
    overall_mape = sum(row["ape_percent"] for row in forecast_rows) / len(forecast_rows)

    print(f"Serie previste: {len(series)}")
    print(f"Previsioni create: {len(forecast_rows)}")
    print(f"MAE medio: {overall_mae:.2f}")
    print(f"MAPE medio: {overall_mape:.2f}%")
    print(f"File previsioni: {FORECAST_FILE.resolve()}")
    print(f"File metriche: {METRICS_FILE.resolve()}")
    print(f"Plot: {PLOT_FILE.resolve()}")


if __name__ == "__main__":
    main()
