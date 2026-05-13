# Prescriptive Analytics

Script Python per preparare, ricostruire, visualizzare, prevedere e ottimizzare 52 serie temporali legate ai dati COVID. Il progetto include anche strumenti per leggere una matrice delle distanze, visualizzare i clienti, stimare il numero di camion e costruire rotte iniziali da un deposito.

## Contenuto Del Progetto

| File | Descrizione |
| --- | --- |
| `main.py` | Legge il dataset COVID originale, raggruppa le righe per `idserie`, rimuove alcuni mesi del 2020 per i grafici e genera file raggruppati o pivotati. |
| `ricostruisci_mar_apr_may_2020.py` | Ricostruisce i valori di Feb-Mar-Apr 2020 usando la media degli stessi mesi negli anni di riferimento. |
| `plot_serie_interattivo.py` | Disegna tutte le serie ricostruite ed evidenzia il periodo ricostruito del 2020. |
| `prevedi_ultimi_3_mesi.py` | Prevede gli ultimi tre mesi di ogni serie con Holt-Winters; se il modello fallisce usa una previsione stagionale naive. |
| `optimization.py` | Ricostruisce i mesi COVID, seleziona un modello SARIMAX per ogni serie, genera forecast e salva le predizioni in `predizioni.csv`. |
| `depositi.py` | Costruisce una soluzione iniziale per le rotte dei camion a partire dalla matrice delle distanze, dalle predizioni e dalla posizione dei clienti/deposito. |
| `NumeroCamionMilano.py` | Carica la matrice delle distanze, estrae una sottomatrice 20x20, stampa i totali, stima il numero di camion e mostra una heatmap. |
| `plot_customers_scatter.py` | Legge le coordinate dei clienti e genera uno scatter plot. |
| `predizioni.csv` | Output prodotto da `optimization.py`, usato da `depositi.py` per calcolare le richieste. |
| `fileCSV/serie_covid_new.csv` | Dataset originale delle serie temporali COVID. |
| `fileCSV/serie_covid_new_per_idserie.csv` | Serie raggruppate per `idserie`. |
| `fileCSV/serie_covid_new_per_idserie_feb_mar_apr_2020_ricostruiti.csv` | Serie raggruppate con valori Feb-Mar-Apr 2020 ricostruiti. |
| `fileCSV/previsioni_ultimi_3_mesi_per_serie.csv` | Output delle previsioni sugli ultimi tre mesi per ogni serie. |
| `fileCSV/previsioni_dicembre_primi_20_diviso_5.csv` | Previsioni di dicembre per le prime 20 serie divise per 5. |
| `fileCSV/metriche_previsioni_ultimi_3_mesi.csv` | Metriche dell'esperimento di previsione sugli ultimi tre mesi. |
| `fileCSV/mat52.csv` | Matrice delle distanze 52x52. |
| `fileCSV/customers_scatter.CSV` | Coordinate dei clienti usate per lo scatter plot e per visualizzare le rotte. |
| `plot_serie_covid/` | Cartella con i grafici generati. |

## Requisiti

Prima di eseguire gli script, installare le dipendenze Python:

```bash
pip install matplotlib numpy pandas statsmodels
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

5. Generare le predizioni SARIMAX usate dall'ottimizzazione:

```bash
python optimization.py
```

6. Analizzare la matrice delle distanze e la stima dei camion:

```bash
python NumeroCamionMilano.py
```

7. Visualizzare le coordinate dei clienti:

```bash
python plot_customers_scatter.py
```

8. Costruire e visualizzare le rotte iniziali dei camion:

```bash
python depositi.py
```

