import re
import math
import spacy
from live_log import emit
from RegexAlgorithm.keywords_weights import TOKEN_WEIGHTS
from collections import Counter
from RegexAlgorithm.regex_patterns import (
    DATE_RE, REL_TIME_RE,
    CASE_PATTERNS, CASE_REQUIREMENTS,
    DAL_AL_RE, TRA_E_RE, SINGOLA_RE,
)
DATE_RANGE_LABELS = {
    DAL_AL_RE: "DAL_AL",
    TRA_E_RE:  "TRA_E",
    SINGOLA_RE: "SINGOLA",
}

nlp = spacy.load("it_core_news_sm")  # modello spaCy italiano

# ————————————————————————————————————————————————————————————
# Calcolo probabilità METADATA/CONTENUTO
BIAS = -1.2  # bias leggermente negativo

def sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))

def prob_metadata(text: str) -> float:
    score = BIAS

    if DATE_RE.search(text):
        score += 1.2
    if REL_TIME_RE.search(text):
        score += 0.9

    doc = nlp(text.lower())
    score += 0.6 * sum(1 for ent in doc.ents if ent.label_ == "DATE")

    for tok in doc:
        score += TOKEN_WEIGHTS.get(tok.lemma_, 0)

    return sigmoid(score)


# ————————————————————————————————————————————————————————————
# Funzioni di pulizia d'output

def clean_author_match(matched_text: str) -> str | None:
    """
    Dato un frammento di testo matchato da FIND_BY_AUTHOR,
    restituisce il nome dell'autore se riconosciuto da SpaCy, altrimenti None.
    """
    doc = nlp(matched_text)

    # 1. Cerca entità di tipo PERSON
    #for ent in doc.ents:
    #    if ent.label_ == "PER":
    #        return ent.text.strip()

    # 2. Se non ci sono entità, prova a ricostruire un possibile nome manualmente
    name_tokens = []
    for token in doc:
        emit(f"TOKEN: '{token.text}' | POS: {token.pos_} | TAG: {token.tag_} | ENT: {token.ent_type_}", "thinking")
        if (token.pos_ in {"PROPN"} or token.ent_type_ in {"PER"}) and not token.is_stop:
            name_tokens.append(token.text)

    if name_tokens:
        return " ".join(name_tokens)

    return None

def _dedup_date_frags(date_buf):
    """
    Rimuove i frammenti di data duplicati, preferendo quelli che contengono un anno ({4}).

    date_buf: lista di tuple (label, frammento_data)
    ritorna: lista filtrata di tuple (label, frammento_data)
    """
    # Pattern per riconoscere un anno a 4 cifre
    year_re = re.compile(r"\b\d{4}\b")

    # Separa frammenti con anno e senza anno
    with_year = [(lbl, frag) for lbl, frag in date_buf if year_re.search(frag)]
    without_year = [(lbl, frag) for lbl, frag in date_buf if not year_re.search(frag)]

    # Se esistono frammenti con anno, lavoriamo solo su quelli; altrimenti sugli altri
    to_process = with_year if with_year else without_year

    # Ordiniamo per lunghezza del frammento (decrescente) così i più completi vengono tenuti prima
    to_process_sorted = sorted(to_process, key=lambda x: len(x[1]), reverse=True)

    # Dedup: manteniamo un frammento solo se non è sottostringa di uno già incluso
    result = []
    for lbl, frag in to_process_sorted:
        if not any(frag in existing_frag for _, existing_frag in result):
            result.append((lbl, frag))

    return result

def clean_about_topic(raw_text: str) -> str:
    """
    Pulisce l'output di tipo ABOUT_TOPIC eliminando rumore testuale
    e mantenendo solo le componenti potenzialmente utili come prompt (NOUN, PROPN, ADJ).
    """
    doc = nlp(raw_text)
    tokens = [tok.text for tok in doc if tok.pos_ in {"NOUN", "PROPN", "ADJ"} and not tok.is_stop]
    return " ".join(tokens)

# ————————————————————————————————————————————————————————————
# Individuazione casi d'uso

def scan_cases(text: str) -> tuple[Counter, list[tuple[str, str, str]]]:
    """
    Ritorna:
      counts  – Counter {case: occorrenze}
      matches – [(case, label, frammento)], dove label è
                "DAL_AL" | "TRA_E" | "SINGOLA" oppure "" per gli altri casi.
    """
    counts   = Counter()
    matches  : list[tuple[str, str, str]] = []
    date_buf : list[tuple[str, str]] = []   # [(label, frag)]

    for case, patterns in CASE_PATTERNS.items():
        for pat in patterns:
            for m in re.finditer(pat, text, re.IGNORECASE | re.VERBOSE):
                output = m.group(0).strip()
                label = ""

                if case == "FIND_BY_AUTHOR":
                    emit("before AUTHOR: " + output, "thinking")
                    output = clean_author_match(output)
                    if not output:
                        continue

                if case == "FILTER_BY_DATE_RANGE":
                    label = DATE_RANGE_LABELS.get(pat, "")
                    date_buf.append((label, output))
                    continue                 # dedup dopo

                if case == "WORD_NUMBER" and not output:
                    continue  # salta i match a lunghezza zero

                if case == "ABOUT_TOPIC":
                    emit("before TOPIC: " + output, "thinking")
                    output = clean_about_topic(output)

                if case == "SEARCH_BY_KEYWORD":
                    output = m.group('term').strip()

                counts[case] += 1
                matches.append((case, label, output))

    # —— deduplica date-range e aggiunge label corrispondente ——
    for lbl, output in _dedup_date_frags(date_buf):
        counts["FILTER_BY_DATE_RANGE"] += 1
        matches.append(("FILTER_BY_DATE_RANGE", lbl, output))

    return counts, matches

# ————————————————————————————————————————————————————————————
def analizza_query(text: str, soglia: float = 0.5) -> str:
    #print("received request: " + text)
    #cases = detect_cases(text)
    counts, matches = scan_cases(text)
    cases = list(counts)  # solo le chiavi, come prima

    #print("stepped out")

    # 1) Casi che obbligano METADATA
    #if any(CASE_REQUIREMENTS.get(c) == "METADATA" for c in cases):
    #    metodo = "METADATA"

    # 2) Casi che obbligano solo CONTENUTO
    #elif cases and all(CASE_REQUIREMENTS.get(c) == "CONTENUTO"
    #                   for c in cases if CASE_REQUIREMENTS.get(c)):
    #    metodo = "CONTENUTO"

    # 3) Fallback probabilistico
    #else:
    #    metodo = "METADATA" if prob_metadata(text) >= soglia else "CONTENUTO"

    if counts:
        formatted = ", ".join(
            f"{c} x{counts[c]}" if counts[c] > 1 else c
            for c in counts
        )
    else:
        formatted = None

    # ——— Output ———
    output = ""
    #output += f"Metodo scelto: {metodo}\n"
    #output += f"Casi rilevati: {formatted or 'nessuno'}\n"
    emit(f"Casi rilevati: {formatted or 'nessuno'}", "html")
    #print(f"Metodo scelto: {metodo}")
    #print(f"Casi rilevati: {formatted or 'nessuno'}")

    if formatted:
        for case, label, frag in matches:
            if label:
                #output += f" ↳  {case} [{label}]: \"{frag}\"\n"
                emit(f" ↳  {case} [{label}]: \"{frag}\"", "html")
                #print(f" ↳  {case} [{label}]: \"{frag}\"")
            else:
                #output += f" ↳  {case}: \"{frag}\"\n"
                emit(f" ↳  {case}: \"{frag}\"", "html")
                #print(f" ↳  {case}: \"{frag}\"")

    # Avviso di incoerenza (opzionale)
    #incoerenti = [
    #    c for c in cases
    #    if CASE_REQUIREMENTS.get(c) and CASE_REQUIREMENTS[c] != metodo
    #]
    #if incoerenti:
    #    obbl = CASE_REQUIREMENTS[incoerenti[0]]
    #    print(f"⚠️  Attenzione: i casi {incoerenti} richiedono {obbl} "
    #          f"ma il metodo individuato è {metodo}")

    #returned_information(output)

    return output

# ————————————————————————————————————————————————————————————
if __name__ == "__main__":
    while True:
        try:
            query = input("Scrivi la tua richiesta di ricerca:\n")
            output = analizza_query(query)
            print(output)
        except KeyboardInterrupt:
            print("Fermato il programma.")
            break
