from collections import defaultdict
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from statsmodels.tsa.holtwinters import ExponentialSmoothing


INPUT_FILE = Path("serie_covid_new_per_idserie_feb_mar_apr_2020_ricostruiti.csv")
FORECAST_FILE = Path("previsioni_ott_nov_dic_per_annata.csv")
METRICS_FILE = Path("metriche_previsioni_ott_nov_dic_per_annata.csv")
PLOT_FILE = Path("plot_serie_covid") / "previsioni_ott_nov_dic_per_annata_52_serie.png"
TRAIN_MONTHS = {"Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"}
TEST_MONTHS = {"Oct", "Nov", "Dec"}


def clean_value(row, wanted_key):
    for key, value in row.items():
        if key.strip() == wanted_key:
            return value.strip()
    raise KeyError(wanted_key)


def split_month(month_label):
    month_name, year = month_label.split("-")
    return month_name, year


def read_rows(path):
    rows = []
    with path.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            month_label = clean_value(row, "month")
            month_name, year = split_month(month_label)
            rows.append(
                {
                    "idserie": int(clean_value(row, "idserie")),
                    "month": month_label,
                    "month_name": month_name,
                    "year": year,
                    "periodo": int(clean_value(row, "periodo")),
                    "val": float(clean_value(row, "val")),
                }
            )

    rows.sort(key=lambda item: (item["idserie"], item["periodo"]))
    return rows


def group_rows(rows):
    by_series = defaultdict(list)
    by_series_year = defaultdict(list)

    for row in rows:
        by_series[row["idserie"]].append(row)
        by_series_year[(row["idserie"], row["year"])].append(row)

    for grouped_rows in by_series.values():
        grouped_rows.sort(key=lambda item: item["periodo"])
    for grouped_rows in by_series_year.values():
        grouped_rows.sort(key=lambda item: item["periodo"])

    return dict(sorted(by_series.items())), dict(sorted(by_series_year.items()))


def forecast_year(rows):
    train_rows = [row for row in rows if row["month_name"] in TRAIN_MONTHS]
    test_rows = [row for row in rows if row["month_name"] in TEST_MONTHS]
    train_values = [row["val"] for row in train_rows]

    if len(train_rows) != 9 or len(test_rows) != 3:
        raise ValueError("Ogni annata deve avere 9 mesi di train e 3 mesi di test")

    try:
        model = ExponentialSmoothing(
            train_values,
            trend="add",
            seasonal=None,
            initialization_method="estimated",
        )
        fitted = model.fit(optimized=True)
        predictions = [round(value, 2) for value in fitted.forecast(3)]
        model_name = "holt_linear_trend"
    except Exception:
        last_value = train_values[-1]
        predictions = [round(last_value, 2)] * 3
        model_name = "last_value"

    forecast_rows = []
    for test_row, prediction in zip(test_rows, predictions):
        actual = test_row["val"]
        error = round(actual - prediction, 2)
        abs_error = round(abs(error), 2)
        ape = round(abs_error / actual * 100, 2) if actual else ""
        forecast_rows.append(
            {
                "idserie": test_row["idserie"],
                "year": f"20{test_row['year']}",
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
        "year",
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
        grouped[(row["idserie"], row["year"])].append(row)

    for (idserie, year), rows in sorted(grouped.items()):
        mae = sum(row["abs_error"] for row in rows) / len(rows)
        mape_values = [row["ape_percent"] for row in rows if row["ape_percent"] != ""]
        mape = sum(mape_values) / len(mape_values) if mape_values else ""
        metrics.append(
            {
                "idserie": idserie,
                "year": year,
                "mae": round(mae, 2),
                "mape_percent": round(mape, 2) if mape != "" else "",
                "model": rows[0]["model"],
            }
        )

    with METRICS_FILE.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["idserie", "year", "mae", "mape_percent", "model"])
        writer.writeheader()
        writer.writerows(metrics)

    return metrics


def plot_forecasts(series, forecast_rows):
    PLOT_FILE.parent.mkdir(exist_ok=True)
    forecast_by_series = defaultdict(list)
    for row in forecast_rows:
        forecast_by_series[row["idserie"]].append(row)

    fig, ax = plt.subplots(figsize=(16, 8))

    reference_months = []
    for rows in series.values():
        reference_months = [row["month"] for row in rows]
        break

    test_positions = [
        index
        for index, month in enumerate(reference_months)
        if split_month(month)[0] in TEST_MONTHS
    ]

    for idserie, rows in series.items():
        months = [row["month"] for row in rows]
        values = [row["val"] for row in rows]
        line = ax.plot(months, values, linewidth=1.0, alpha=0.45)[0]

        forecasts = sorted(forecast_by_series[idserie], key=lambda item: item["periodo"])
        by_year = defaultdict(list)
        for forecast in forecasts:
            by_year[forecast["year"]].append(forecast)

        for year_rows in by_year.values():
            test_months = [row["month"] for row in year_rows]
            predictions = [row["forecast"] for row in year_rows]
            ax.plot(test_months, predictions, linestyle="--", linewidth=1.6, color=line.get_color())

    for start in range(0, len(test_positions), 3):
        chunk = test_positions[start : start + 3]
        ax.axvspan(min(chunk) - 0.5, max(chunk) + 0.5, color="gold", alpha=0.08)

    ax.set_title("Previsioni Oct-Nov-Dec per ogni annata sulle 52 serie")
    ax.set_xlabel("Mese")
    ax.set_ylabel("Valore")
    ax.grid(True, alpha=0.3)
    ax.tick_params(axis="x", rotation=75, labelsize=8)
    fig.tight_layout()
    fig.savefig(PLOT_FILE, dpi=150)
    plt.close(fig)


def main():
    rows = read_rows(INPUT_FILE)
    series, series_years = group_rows(rows)
    if len(series) != 52:
        raise ValueError(f"Trovate {len(series)} serie invece di 52")

    forecast_rows = []
    for rows_for_year in series_years.values():
        forecast_rows.extend(forecast_year(rows_for_year))

    write_forecasts(forecast_rows)
    metrics = write_metrics(forecast_rows)
    plot_forecasts(series, forecast_rows)

    overall_mae = sum(row["abs_error"] for row in forecast_rows) / len(forecast_rows)
    overall_mape = sum(row["ape_percent"] for row in forecast_rows) / len(forecast_rows)

    print(f"Serie previste: {len(series)}")
    print(f"Annate previste: {len(metrics)}")
    print(f"Previsioni create: {len(forecast_rows)}")
    print(f"MAE medio: {overall_mae:.2f}")
    print(f"MAPE medio: {overall_mape:.2f}%")
    print(f"File previsioni: {FORECAST_FILE.resolve()}")
    print(f"File metriche: {METRICS_FILE.resolve()}")
    print(f"Plot: {PLOT_FILE.resolve()}")


if __name__ == "__main__":
    main()
