from collections import defaultdict
import csv
from pathlib import Path


INPUT_FILE = Path("serie_covid_new_per_idserie.csv")
OUTPUT_FILE = Path("serie_covid_new_per_idserie_feb_mar_apr_2020_ricostruiti.csv")
MONTHS_TO_REBUILD = {"Feb", "Mar", "Apr"}
REFERENCE_YEARS = {"19", "21", "22"}
TARGET_YEAR = "20"


def month_part(month_label):
    return month_label.split("-")[0]


def year_part(month_label):
    return month_label.split("-")[1]


def read_rows(path):
    with path.open(newline="", encoding="utf-8") as csvfile:
        return list(csv.DictReader(csvfile))


def rebuild_values(rows):
    reference_values = defaultdict(list)

    for row in rows:
        month = row["month"]
        month_name = month_part(month)
        year = year_part(month)

        if month_name in MONTHS_TO_REBUILD and year in REFERENCE_YEARS:
            key = (row["idserie"], month_name)
            reference_values[key].append(float(row["val"]))

    rebuilt_rows = []
    for row in rows:
        rebuilt_row = dict(row)
        month = row["month"]
        month_name = month_part(month)
        year = year_part(month)

        if month_name in MONTHS_TO_REBUILD and year == TARGET_YEAR:
            key = (row["idserie"], month_name)
            values = reference_values[key]
            if not values:
                raise ValueError(f"Nessun riferimento trovato per serie {row['idserie']} {month_name}")

            rebuilt_row["val_originale"] = row["val"]
            rebuilt_row["val"] = round(sum(values) / len(values), 2)
            rebuilt_row["ricostruito"] = "1"
        else:
            rebuilt_row["val_originale"] = row["val"]
            rebuilt_row["ricostruito"] = "0"

        rebuilt_rows.append(rebuilt_row)

    return rebuilt_rows


def write_rows(path, rows):
    fieldnames = ["idserie", "month", "periodo", "val", "val_originale", "ricostruito"]
    with path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    rows = read_rows(INPUT_FILE)
    rebuilt_rows = rebuild_values(rows)
    write_rows(OUTPUT_FILE, rebuilt_rows)

    rebuilt_count = sum(1 for row in rebuilt_rows if row["ricostruito"] == "1")
    print(f"Valori ricostruiti: {rebuilt_count}")
    print(f"File creato: {OUTPUT_FILE.resolve()}")


if __name__ == "__main__":
    main()
