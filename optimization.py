import matplotlib.pyplot
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
import warnings
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tools.sm_exceptions import ConvergenceWarning
from pathlib import Path

INUPUT_FILE = Path(__file__).resolve().parent / "fileCSV" / "serie_covid_new.csv"


def replace_covid_months(group: pd.DataFrame) -> pd.DataFrame:

    COVID_MONTHS = [
        'Feb-20',
        'Mar-20',
        'Apr-20',
    ]

    REPLACING_MONTHS = [
        'Feb-',
        'Mar-',
        'Apr-',
    ]

    for rm, m in zip(REPLACING_MONTHS, COVID_MONTHS):
        mask_reference = group['month'].str.contains(rm) & (group['month'] != m)
        mask_covid     = (group['month'] == m)

        if mask_reference.any() and mask_covid.any():
            mean_val = round(group.loc[mask_reference, 'val'].mean(), 4)
            group.loc[mask_covid, 'val'] = mean_val

    return group


if __name__ == '__main__':

    ID_SERIE = 'idserie'
    df = pd.read_csv(INUPUT_FILE, skipinitialspace=True)
    df.columns = df.columns.str.strip()
    df['val'] = df['val'].astype(float)

    series_groups = [
        (serie_id, group.reset_index(drop=True))
        for serie_id, group in df.groupby(ID_SERIE)
    ]
    series_ids = [serie_id for serie_id, _ in series_groups]
    series_array: list[pd.DataFrame] = [group for _, group in series_groups]

    series_array = [replace_covid_months(s) for s in series_array]

    s = 12
    sarimax_candidates = [
        ((1, 1, 1), (0, 1, 0, s)),
        ((1, 1, 0), (0, 1, 0, s)),
        ((0, 1, 1), (0, 1, 0, s)),
        ((1, 1, 1), (0, 0, 0, 0)),
    ]


    val_size = len(series_array[0].values)
    test_size = 3

    train : list[list[pd.DataFrame]] = []

    for serie in series_array:
        train.append(serie.iloc[:val_size - test_size]['val'])

    exog = []
    for i in range(len(series_array)):
        exog.append(series_array[i].iloc[:val_size-test_size]['val'])

    export = pd.DataFrame()
    fig, ax = matplotlib.pyplot.subplots(figsize=(15, 9))
    color_map = matplotlib.pyplot.get_cmap('nipy_spectral', len(series_array))
    colors = [color_map(i) for i in range(len(series_array))]

    for i,serie in enumerate(train):

        best_result = None
        best_model_config = None

        for order, seasonal_order in sarimax_candidates:
            sarimax_model = SARIMAX(
                serie,
                order=order,
                seasonal_order=seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False,
            )

            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings("error", category=ConvergenceWarning)
                    warnings.filterwarnings(
                        "ignore",
                        message="Too few observations to estimate starting parameters.*",
                        category=UserWarning,
                    )
                    sarimax_model_fitted = sarimax_model.fit(disp=False, maxiter=500)
            except (ConvergenceWarning, ValueError, np.linalg.LinAlgError):
                continue

            if best_result is None or sarimax_model_fitted.aic < best_result.aic:
                best_result = sarimax_model_fitted
                best_model_config = (order, seasonal_order)

        if best_result is None:
            raise RuntimeError(f"Nessun modello SARIMAX converge per la serie {series_ids[i]}.")

        print(f"Serie {series_ids[i]}: order={best_model_config[0]}, seasonal_order={best_model_config[1]}, AIC={best_result.aic:.2f}")
        sarimax_model_fitted = best_result

        n_forecast = test_size
        in_sample = sarimax_model_fitted.fittedvalues
        out_of_sample = sarimax_model_fitted.get_forecast(steps=n_forecast).predicted_mean
        full_forecast = pd.concat([in_sample, out_of_sample])

        ax.plot(full_forecast, linestyle='--', color=colors[i], linewidth=1.4, alpha=0.75)


        export[str(series_ids[i])] = full_forecast[-1:]

    export.to_csv('predizioni.csv')

    for i in range(len(series_array)):
        ax.plot(
            series_array[i].iloc[:val_size-test_size]['val'],
            color=colors[i],
            linewidth=1.6,
            alpha=0.9,
        )

    style_handles = [
        Line2D([0], [0], color='black', linestyle='-', linewidth=2, label='Storico train'),
        Line2D([0], [0], color='black', linestyle='--', linewidth=2, label='Forecast SARIMAX'),
    ]
    series_handles = [
        Line2D([0], [0], color=colors[i], linewidth=2, label=f'Serie {series_ids[i]}')
        for i in range(len(series_array))
    ]

    style_legend = ax.legend(
        handles=style_handles,
        title='Tipo linea',
        loc='upper left',
        frameon=True,
    )
    ax.add_artist(style_legend)
    ax.legend(
        handles=series_handles,
        title='Legenda 52 serie',
        loc='upper center',
        bbox_to_anchor=(0.5, -0.10),
        ncol=8,
        fontsize='small',
        frameon=True,
    )
    ax.set_xlabel('Periodo')
    ax.set_ylabel('Valore')
    ax.set_title('Serie storiche e forecast SARIMAX')
    fig.tight_layout(rect=(0, 0.12, 1, 1))

    matplotlib.pyplot.show(block=True) 
