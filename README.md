# Prescriptive Analytics

Progetto Python per combinare previsione della domanda e ottimizzazione di rotte.

Il workflow principale parte dalle 52 serie storiche in `fileCSV/serie_covid_new.csv`, ricostruisce i mesi anomali del periodo COVID, genera previsioni con modelli SARIMAX e usa quelle previsioni per costruire e migliorare rotte di consegna da un deposito.

## Struttura

| Percorso | Descrizione |
| --- | --- |
| `optimization.py` | Ricostruisce Feb-Mar-Apr 2020, seleziona un modello SARIMAX per ogni serie e salva le predizioni in `predizioni.csv`. |
| `depositi_final.py` | Script principale per costruire una soluzione iniziale, applicare local search e iterated local search, stampare i costi e visualizzare le rotte. |
| `goto.py` | Modulo locale usato da `depositi_final.py` per la sintassi `goto`. Non e' una dipendenza da installare con `pip`. |
| `predizioni.csv` | Predizioni usate dagli script di routing. Viene generato da `optimization.py`. |
| `fileCSV/serie_covid_new.csv` | Dataset originale delle 52 serie temporali. |
| `fileCSV/mat52.csv` | Matrice delle distanze 52x52. |
| `fileCSV/customers_scatter.CSV` | Coordinate dei clienti e del deposito per gli scatter plot. |
| `fileCSV/serie_covid_new_per_idserie.csv` | Dataset gia' raggruppato per `idserie`. |
| `fileCSV/serie_covid_new_per_idserie_feb_mar_apr_2020_ricostruiti.csv` | Serie con valori COVID ricostruiti. |
| `fileCSV/previsioni_dicembre_primi_20_diviso_5.csv` | Output storico di previsioni su dicembre per le prime 20 serie. |
| `fileCSV/metriche_previsioni_ultimi_3_mesi.csv` | Metriche di un esperimento precedente sugli ultimi tre mesi. |
| `plot_serie_covid/` | Grafici generati e salvati. |
| `prove_vecchie_depositi/` | Versioni precedenti ed esperimenti sulle euristiche di routing. |

## Requisiti

Installare le dipendenze Python:

```bash
pip install matplotlib numpy pandas statsmodels ortools
```

Il progetto e' stato eseguito con Python 3.12. OR-Tools serve solo per `prove_vecchie_depositi/depositi_ottimizzato.py`; il workflow principale funziona con `depositi_final.py`.

## Esecuzione

Eseguire i comandi dalla root del progetto:

```bash
cd "C:\Prescriptive analytics"
```

1. Generare o aggiornare le predizioni:

```bash
python optimization.py
```

Questo comando legge `fileCSV/serie_covid_new.csv` e riscrive `predizioni.csv`.

2. Calcolare e visualizzare le rotte:

```bash
python depositi_final.py
```

Lo script legge `fileCSV/mat52.csv`, `fileCSV/customers_scatter.CSV` e `predizioni.csv`, poi mostra:

- soluzione iniziale greedy;
- soluzione migliorata con local search;
- soluzione migliorata con iterated local search.

## Script Sperimentali

Gli script in `prove_vecchie_depositi/` sono versioni precedenti o alternative:

| File | Descrizione |
| --- | --- |
| `prove_vecchie_depositi/depositi.py` | Costruisce una soluzione iniziale greedy. |
| `prove_vecchie_depositi/depositi_local.py` | Applica una local search alla soluzione iniziale. |
| `prove_vecchie_depositi/depositi_iterated_local.py` | Applica iterated local search con perturbazioni. |
| `prove_vecchie_depositi/depositi_ottimizzato.py` | Confronta soluzione greedy e soluzione ottimizzata con OR-Tools. |

Esempi:

```bash
python prove_vecchie_depositi/depositi.py
python prove_vecchie_depositi/depositi_local.py
python prove_vecchie_depositi/depositi_iterated_local.py
python prove_vecchie_depositi/depositi_ottimizzato.py
```