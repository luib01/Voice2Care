# 🚑 Clinical Data Analysis - Sistema di Analisi Dati Emergenza Ambulanza

Questo progetto nasce per analizzare, visualizzare e valorizzare i dati raccolti durante gli interventi di emergenza sanitaria in Italia. L'obiettivo è fornire strumenti di analisi per migliorare l'efficienza del servizio di ambulanza, individuare criticità, pattern clinici e supportare decisioni data-driven.

## Struttura del progetto

- **cartella_clinica/**: contiene i file JSON delle cartelle cliniche raccolte dagli interventi.
- **output/**: contiene i file CSV generati dalle analisi Spark (es. tempi di intervento, distribuzione per città, ecc).
- **mongo_db/**: dati grezzi del database MongoDB (per backup o ripristino).
- **app.py**: applicazione Streamlit per la visualizzazione interattiva dei dati.
- **Data_lake.ipynb**: notebook per l'analisi dati con PySpark e salvataggio dei risultati.
- **DataBase.ipynb**: notebook per il caricamento dei dati in MongoDB e ispezione del database.
- **LLM_NER.ipynb**: notebook per l'estrazione automatica di dati clinici da testo libero tramite modelli LLM e NER.
- **mongo-spark/**: codice sorgente del connettore Spark-MongoDB (per sviluppo avanzato o personalizzazione).

## Flusso di lavoro

### 1. **Estrazione e caricamento dati**
- Inserisci i file JSON delle cartelle cliniche nella cartella `cartella_clinica/`.
- Esegui il notebook [DataBase.ipynb](DataBase.ipynb) per caricare i dati in MongoDB:
  - La cella principale scansiona la cartella e inserisce i dati nella collezione `cartella_clinica_db.interventi`.

### 2. **Analisi dati con PySpark**
- Esegui il notebook [Data_lake.ipynb](Data_lake.ipynb):
  - Configura Java e Spark come indicato nelle prime celle.
  - Le celle successive eseguono analisi sui dati (tempi di intervento, distribuzione per città, ecc.) e salvano i risultati in `output/` come file CSV.

### 3. **Visualizzazione interattiva**
- Avvia l'applicazione Streamlit per esplorare i dati:
  ```sh
  streamlit run app.py
  ```
- L'app offre due sezioni:
  - **Ambulanze**: analisi geografiche, tempi di intervento, distribuzione oraria, decessi sul posto.
  - **Pazienti**: ricerca pazienti, sintomi più frequenti, farmaci somministrati, analisi per fascia d'età.

### 4. **Estrazione automatica dati clinici da testo**
- Esegui il notebook [LLM_NER.ipynb](LLM_NER.ipynb) per:
  - Trascrivere audio (con Whisper).
  - Estrarre entità cliniche da testo libero tramite modelli LLM (es. Mistral) e NER.
  - Salvare automaticamente i dati strutturati in formato JSON nella cartella `cartelle_cliniche/`.
  - (Opzionale) Generare un PDF compilato della cartella clinica tramite LaTeX.

## Requisiti

- **Python 3.8+**
- **MongoDB** (locale, default su `localhost:27017`)
- **Java 11** (per PySpark)
- **PySpark** e **MongoDB Spark Connector**
- **Streamlit**
- **Altair**, **PyDeck**, **Geopy**, **Pandas**, **Pymongo**
- (Opzionale) **Whisper**, **transformers**, **sounddevice** per LLM_NER.ipynb
- (Opzionale) **pdflatex** per generazione PDF

Installa i pacchetti Python necessari:
```sh
pip install streamlit pandas geopy pydeck altair pymongo pyspark whisper transformers sounddevice
```

## Note operative

- Assicurati che MongoDB sia avviato prima di eseguire i notebook o l'app.
- I file CSV in `output/` vengono sovrascritti ad ogni nuova analisi.
- L'app Streamlit legge i dati da MongoDB e dai file CSV generati da Spark.
- Per la trascrizione audio e l'estrazione automatica, consulta le istruzioni nelle celle di [LLM_NER.ipynb](LLM_NER.ipynb).

## Personalizzazione

- Puoi aggiungere nuovi dati in `cartella_clinica/` e rilanciare il caricamento.
- Puoi modificare le analisi in [Data_lake.ipynb](Data_lake.ipynb) per nuove metriche.
- L'app Streamlit può essere estesa per nuove visualizzazioni o filtri.

## Contatti

Per domande o segnalazioni, apri una issue o contatta il responsabile del