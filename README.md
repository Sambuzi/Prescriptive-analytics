# Prescriptive Analytics

Script Python per preparare, ricostruire, visualizzare e prevedere 52 serie temporali legate ai dati COVID. Il progetto include anche uno script per leggere una matrice delle distanze e stimare un numero di camion a partire dai totali calcolati.

## Contenuto Del Progetto

| File | Descrizione |
| --- | --- |
| `main.py` | Legge il dataset COVID originale, raggruppa le righe per `idserie`, rimuove alcuni mesi del 2020 per i grafici e genera file raggruppati o pivotati. |
| `ricostruisci_mar_apr_may_2020.py` | Ricostruisce i valori di Feb-Mar-Apr 2020 usando la media degli stessi mesi negli anni di riferimento. |
| `plot_serie_interattivo.py` | Disegna tutte le serie ricostruite ed evidenzia il periodo ricostruito del 2020. |
| `prevedi_ultimi_3_mesi.py` | Prevede gli ultimi tre mesi di ogni serie con Holt-Winters; se il modello fallisce usa una previsione stagionale naive. |
| `NumeroCamionMilano.py` | Carica la matrice delle distanze, estrae una sottomatrice 20x20, stampa i totali, stima il numero di camion e mostra una heatmap. |
| `serie_covid_new.csv` | Dataset originale delle serie temporali COVID. |
| `serie_covid_new_per_idserie.csv` | Serie raggruppate per `idserie`. |
| `serie_covid_new_per_idserie_feb_mar_apr_2020_ricostruiti.csv` | Serie raggruppate con valori Feb-Mar-Apr 2020 ricostruiti. |
| `previsioni_ultimi_3_mesi_per_serie.csv` | Output delle previsioni sugli ultimi tre mesi per ogni serie. |
| `metriche_previsioni_ultimi_3_mesi.csv` | Metriche dell'esperimento di previsione sugli ultimi tre mesi. |
| `mat52.csv` | Matrice delle distanze 52x52. |
| `plot_serie_covid/` | Cartella con i grafici generati. |

## Requisiti

Prima di eseguire gli script, installare le dipendenze Python:

```bash
pip install matplotlib numpy statsmodels
```

Oltre a questi pacchetti, il progetto usa solo librerie standard di Python.

## Workflow Consigliato

1. Preparare i file raggruppati e i grafici dal dataset originale:

```bash
python main.py
```

2. Ricostruire i valori anomali del 2020:

```bash
python ricostruisci_mar_apr_may_2020.py
```

3. Visualizzare tutte le serie ricostruite:

```bash
python plot_serie_interattivo.py
```

4. Prevedere gli ultimi tre mesi:

```bash
python prevedi_ultimi_3_mesi.py
```

5. Analizzare la matrice delle distanze e la stima dei camion:

```bash
python NumeroCamionMilano.py
```


