# keywords_weights.py
TOKEN_WEIGHTS = {
    # —— METADATA forti ——
    "file": 2.0,
    "metadata": 1.5,
    "autore": 1.2,
    "data": 1.5,
    "titolo": 0.9,
    "formato": 1.2,
    "nome": 0.7,
    "dimensione": 0.8,
    "estensione": 0.8,
    "path": 1.9,

    # —— Verbi/azioni su file ——
    "caricare": 1.6,
    "caricato": 1.6,
    "caricati": 1.6,
    "inserire": 1.2,
    "inserito": 1.2,
    "uploadare": 3.0,
    "uploadato": 3.0,
    "creare": 1.0,
    "creato": 1.0,
    "modificare": 1.0,
    "modificato": 1.0,
    "pubblicare": 1.4,
    "pubblicato": 1.4,
    "pubblicati": 1.4,
    "pubblicata": 1.4,
    "aggiornare": 2.0,
    "aggiornati": 2.0,
    "aggiornato": 2.0,

    # —— Indicatori temporali relativi ——
    "poco": 0.5,
    "fa": 0.4,
    "recentemente": 0.7,
    "oggi": 0.5,
    "ieri": 0.5,
    "ultima": 0.8,
    "ultimi": 0.8,
    "ultime": 0.8,
    "ultimo": 0.8,

    # —— Indicatori di autore ——
    "scrivere": 1.5,  # lemma di «scritti», «scritto», «scritta»…
    "scritto": 1.5,
    "scritti": 1.5,
    "firmare": 1.4,
    "firmato": 1.4,
    "firmati": 1.4,
    "redigere": 1.3,
    "redatto": 1.3,
    "tema": 0.6,
    "argomento": 0.6,
}
