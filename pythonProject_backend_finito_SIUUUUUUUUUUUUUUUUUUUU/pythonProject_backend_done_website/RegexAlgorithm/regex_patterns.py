import re

# ————————————————————————————————————————————————————————————
# Regex di base per date assolute e riferimenti temporali relativi

DATE_RE = re.compile(
    r"(\b\d{1,2}\s*(?:gen|feb|mar|apr|mag|giu|lug|ago|set|ott|nov|dic)\w*\b"
    r"|\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)",
    flags=re.IGNORECASE,
)
REL_TIME_RE = re.compile(
    r"\b(poco\s+fa|recentemente|appena|ieri|oggi|ultim[ioa]\s+"
    r"(?:settimana|mese|giorni?|ore))\b",
    flags=re.IGNORECASE,
)

# ————————————————————————————————————————————————————————————
# Pattern in analisi grammaticale

ART_DET     = r"(?:il|la|lo|l[’']|i|gli|le)"
PREP_ART    = r"(?:del|della|dello|dei|degli|delle|al|alla|allo|ai|agli|alle|dal|dalla|dallo|dai|dagli|dalle|nel|nella|nello|nei|negli|nelle|sul|sulla|sullo|sui|sugli|sulle)"
PREP_SEM    = r"(?:a|ad|al|alla|all'|ai|agli|alle|da|di|in|con|su|per|tra|fra)"
ART_INDET   = r"(?:un|una|uno)"
PRON        = r"(?:io|tu|egli|lui|lei|noi|voi|essi|loro|mi|ti|ci|vi|lo|la|li|le|ne|si)"

# ————————————————————————————————————————————————————————————
# Dizionario di regex per i casi d’uso
MONTHS = (
    r"(?:gen(?:naio)?|feb(?:braio)?|mar(?:zo)?|apr(?:ile)?|mag(?:gio)?|"
    r"giu(?:gno)?|lug(?:lio)?|ago(?:sto)?|set(?:tembre)?|ott(?:obre)?|"
    r"nov(?:embre)?|dic(?:embre)?)"
)

DATE_TOKEN = rf"""
    (?:
        \d{{1,2}}\s*{MONTHS}\s*\d{{4}}                        # 12 maggio 2023
      | \d{{1,2}}\s*{MONTHS}                                  # 12 maggio
      | {MONTHS}\s*\d{{4}}                                    # maggio 2023
      | \d{{1,2}}[\/\-\.\s]\d{{1,2}}(?:[\/\-\.\s]\d{{2,4}})?    # 12-12-2000 & 12/12/2000, anno facoltativo
      | \d{{4}}                                               # 2000
      | {MONTHS}                                              # gennaio
    )
"""

DAL_AL_RE = rf"""
    \b(?:da|dal|dalla)\b\s*         # solo da/dal/dalla
    (?:{ART_DET}\s*)?{DATE_TOKEN}\s+
    \b(?:a|al|alla)\b\s*
    (?:{ART_DET}\s*)?{DATE_TOKEN}\b
"""

TRA_E_RE = rf"""
    \btra\b\s*
    (?:{ART_DET}\s*)?{DATE_TOKEN}\s+
    \be\b\s*
    (?:{ART_DET}\s*)?{DATE_TOKEN}\b
"""

SINGOLA_RE = rf"""
    \b
    (?:prima|dopo|entro(?:\s+fine)?|il|fino(?:\s+a(?:l|lla)?)?|da|dal|dalla|del|di|della)
    \b\s*
    (?:mese\s+di\s+)?                         # opzionale: 'mese di'
    (?:data\s+)?                                 # opzionale: 'data'
    (?:{ART_DET}\s*)?                         # articoli opzionali
    {DATE_TOKEN}\b
"""

# ————————————————————————————————————————————————————————————
# Dizionario di regex per i casi d’uso

UNITS_WORD_RE = r"""
    (?:un[oa]|due|tr[eèé]|quattro|cinque|sei|sette|otto|nove)
"""

# 10-19 hard-coded
TEENS_WORD_RE = r"""
    (?:dieci|undici|dodici|tredici|quattordici|quindici|
       sedici|diciassette|diciotto|diciannove)
"""

# Decine ≥20 con possibili elisioni: venti/ventuno… | trent(a|uno)…
TENS_PREFIX_RE = r"""
    (?:vent|trent|quarant|cinquant|sessant|settant|ottant|novant)
"""
TENS_WORD_RE = rf"""
    (?:{TENS_PREFIX_RE}(?:i|a)?
        (?:\s*|-)?   # spazi o trattino facoltativi fra decine e unità
        {UNITS_WORD_RE}?
    )
"""

HUNDREDS_WORD_RE = rf"""
    (?:
        cento|
        {UNITS_WORD_RE}(?:\s*|-)?cento
    )
"""

THOUSANDS_WORD_RE = rf"""
    (?:
        mille                                                  # 1 000
      | {UNITS_WORD_RE}(?:\s*|-)?mila                          # due-mila
      | {TENS_WORD_RE}(?:\s*|-)?mila                           # quaranta-mila
      | {HUNDREDS_WORD_RE}(?:                                  
            (?:\s*|-)?(?:{TENS_WORD_RE}|{TEENS_WORD_RE}|{UNITS_WORD_RE})?
        )(?:\s*|-)?mila                                        # novecento-cinquanta-mila
    )
"""

# Numeri <1000
SUB_THOUSAND_RE = rf"""
  (?:
    # caso “cento, duecentocinquanta” etc.
    {HUNDREDS_WORD_RE}(?:\s*|-)?(?:{TENS_WORD_RE}|{TEENS_WORD_RE}|{UNITS_WORD_RE})?
  |
    # oppure decine o unità (sempre obbligatorie in questo ramo)
    {TENS_WORD_RE}
  |
    {TEENS_WORD_RE}
  |
    {UNITS_WORD_RE}
  )
"""

# Numeri completi 1-999 999
WORD_NUMBER_RE = rf"""
    (?:
        {THOUSANDS_WORD_RE}(?:\s*|-)?
        {SUB_THOUSAND_RE}             # resto 0-999
      | {SUB_THOUSAND_RE}
    )
"""

# Numeri in cifre da 0 a 999 999 (sei cifre al massimo)
NUMBERS_RE = re.compile(r"\d{1,6}")

# Cifre o parole-numero
NUMBERS_VARIANT_RE = re.compile(
    rf"(?:{NUMBERS_RE.pattern}|{WORD_NUMBER_RE})",
    re.IGNORECASE | re.VERBOSE
)

# ————————————————————————————————————————————————————————————
# Dizionario di regex per i casi d’uso

NOME_REGEX = r"(?:\s*(?:[A-ZÀ-ÖØ-Ýa-zà-öø-ý]+\.?|['’-])\s*){1,5}"

# ————————————————————————————————————————————————————————————
# Pattern principali dell'algoritmo

CASE_PATTERNS = {
    "DATE_TOKEN": [
        DATE_TOKEN,
    ],

    "WORD_NUMBER": [
        rf"\b{WORD_NUMBER_RE}\b",
    ],

    # ——— Ordinamento per data upload ———
    "SORT_UPLOAD_DATE": [
        # Termini inglesi legati all'ordinamento
        r"\bsort(?:ing)?\b",

        # Espressioni relative all'ordine crescente/decrescente
        # "Ordine" e lemmi + 3 parole di contesto + Keyword
        r"""\b
        (?:ordin(?:e|a|are|ati|ament[oi]|azion[ei]))
        (?:\s+\w+){0,3}?
        \s+(?:crescente|decrescente|ascendente|discendente|cronologico\s+inverso|cronologico|inverso)
        \b""",

        # Esempio: “ultimi 5 file”
        r"\bultim[ioaie]*\s+\d*\s*file\b",

        # Espressioni composite e naturali
        r"""(?x)             # verbose
        \b                # qualsiasi testo, poi bordo di parola
        (?:  
            data\s+(?:di\s+)?(?:caricamento|upload|creazione|pubblicazione)
          | dal\s+più\s+(?:recente|vecchio)\s+al\s+più\s+(?:vecchio|recente)
          | dai\s+più\s+(?:recenti|vecchi)\s+ai\s+più\s+(?:vecchi|recenti)
          | più\s+(?:recent[ei]|vecch[io])(?:\s+(?:in\s+cima|prima))?
          | recent[ei]
          | vecch[io]
          | (?:newest|oldest)\s+first
          | most\s+recent
        )\b.*$              # bordo di parola, poi il resto della stringa
        """,

        # Posizionamento
        r"\b(?:sopra|in\s+basso)\b",
    ],

    "LIMIT_RESULTS": [
        rf"""
        \b
        (?:
            (?:primi|prime|top|ultimi|ultime|
             solo|(?:al\s+)?massim[oaie](?:\s+di)?|
             non\s+più\s+di|fino\s+a|esattamente|voglio|mostrami|visualizza)
            \s+
            {NUMBERS_VARIANT_RE.pattern}  # deve essere qui, subito dopo
        )
        (?:\s+(?:file|documenti|risultat[aeio]*|elementi|record|articoli|atti))?
        \b
        """
    ],

    # ——— Ricerca per autore ———
    "FIND_BY_AUTHOR": [
        # Pattern 1 - Keyword + (Simbolo)? + Nome
        r"""\b(?:autore|autrice|author|responsabile(?:\s+progetto)?)\b
            (?:\s*[:=\-–]\s*
                (?!\s*(?:""" + ART_DET + "|" + ART_INDET + "|" + PREP_SEM + "|" + PREP_ART + "|" + PRON + r""")\b)
            )?
        """ + NOME_REGEX,

        # Pattern 2 - Sogg. + (che)? + Verbo + (da)? + Nome (compl. agente)
        r"""
            \b(?:file|document[io]i?|atti|articoli|pdf)?
            (?:\s+che)?\s+
            (?:scrit[toi]|redatt[oi]|firmat[oi]|realizzat[oi]|prodott[oi]|fatt[oi])
            (?:\s+da)?\s*
        """ + NOME_REGEX,

        # Pattern 3 - Sogg. + (Verbo)? + Prep. Semplice + Nome (compl. Specificazione)
        r"""
            \b(?:file|document[io]i?|atti|articoli|pdf)
            (?:\s+(?:archiviat[oi]|intitolat[oi]|registrat[oi]|propriet[aà]|curat[oi]))?
            \s+(?:di|del(?:la)?|d[ei]gli?)\s+
        """ + NOME_REGEX,
    ],

    # ——— Filtri temporali assoluti (date) ———
    "FILTER_BY_DATE_RANGE": [
        DAL_AL_RE,
        TRA_E_RE,
        SINGOLA_RE,
    ],

    # ——— Ricerca nel testo (keyword) ———
    "SEARCH_BY_KEYWORD": [
        # Sinonimi di "keyword" + Keyword.
        r'''\b
        (?:keyword(s?)|termin[ei]|parol[ae]|string[a|(he)])\b # Sinonimi di "keyword"
        [\s:–-]*                                              # eventuale spazio o “:”“–”“-”
        (?P<term>                                             # <<< qui catturiamo il termine
            "(.*?)"                        #   tra doppie virgolette
            | '([^']+)'                      #   tra singole virgolette
            | “([^”]+)”                      #   tra virgolette tipografiche (doppie)
            | ‘([^’]+)’                      #   tra virgolette tipografiche (singole)
            | [^\s"“”‘’]+                    #   o parola semplice non citata
        )
        ''',
    ],

    # ——— Topic / argomento ———
    "ABOUT_TOPIC": [
        rf"""\b(
            parl(?:a|ano|are|ano\s+del) |
            (?:che\s+)?tratt(?:a|ano) |
            riguard(?:a|ano) |
            relativ[aeio]\s+(?:{PREP_SEM}|{PREP_ART}) |
            sul\s+tema\s+(?:{PREP_SEM}|{PREP_ART}) |
            a\s+proposito\s+di |
            a\s+riguard[oa]\s+(?:{PREP_SEM}|{PREP_ART}) |
            inerent[ea]\s+(?:{PREP_SEM}|{PREP_ART}) |
            concernent[ea]\s+(?:{PREP_SEM}|{PREP_ART}) |
            (?:su|sul|sull'|sulla|sulle|sui|sugli)
        )\b
        (?:\s+(?:{PREP_SEM}|{PREP_ART}))?
        (?:\s+(?!(?:{ART_DET}|{ART_INDET}|{PREP_ART}|(?:a|ad|al|alla|ai|agli|da|in|con|per|tra|fra))\b)[^\s.,;!?]+)+
        """,
        # (?:a|ad|al|alla|all'|ai|agli|alle|da|di|in|con|su|per|tra|fra)
        # (?:\s+(?!(?:{ART_DET}|{ART_INDET}|{PREP_ART}|{PREP_SEM})\b)[^\s.,;!?]+)+
        # (?:\s+(?!(?:{ART_DET}|{ART_INDET}|{PREP_ART}|(?:a|ad|al|alla|all'|ai|agli|alle|da|in|con|su|per|tra|fra))\b)[^\s.,;!?]+)+
    ],

    # ——— Filtri temporali relativi ———
    "FILTER_BY_REL_TIME": [
        # 1) “ultimi X unità” (con o senza prefisso “nel/negli/lo/la/questa”)
        r"""\b
           (?:(?:nel(?:la|lo|le|li|l')?|negli?[aeio]?|lo|la|quest[oa])\s+)?
           ultim[ioaie]*\s+(?:\d+|[a-z]+)\s+
           (?:giorni?|settiman[ae]|mesi|anni|ore|minuti|secondi)
           \b""",

        # 2) “X unità fa”
        r"""\b(?:\d+|[a-z]+)\s+
           (?:giorni?|settiman[ae]|mesi|anni|ore|minuti|secondi)\s+fa\b""",

        # 3) formati compatti “3h”, “15min”, “30sec”
        r"\b\d+\s*(?:h|ore|m|min|s|sec)\b",

        # 4) “ieri”, “oggi” e “ieri l’altro” / “l’altro ieri”
        r"""\b(?:ieri(?:\s+l['’]altro)?|l['’]altro\s*ieri|oggi)\b""",

        # 5) “nella / nella scorsa settimana”, “mese scorso”, “anno scorso”
        r"""\b(?:nella|nello|nelle|negli?)\s+scors[oa]\s+
           (?:giorni?|settimana|mesi?|anni|ore|minuti|secondi)\b""",
        r"\b(?:mese|anno|settimana)\s+scors[oa]\b",

        # 6) “da pochi/qualche giorni/settimane/…”
        r"\b(?:pochi|qualche)\s+(?:giorni?|settiman[ae]|mesi|anni|ore|minuti|secondi)\b",

        # 7) “quest’anno”, “quest’anno”, “quest’…” su unità
        r"\bquest[aeio'’]\s*(?:anno|settiman[ae]|mes[ei]|giorn[oi]|or[ae]|minut[oi]|second[oi]|momento|istante)\b",
        r"\bultim[aeio'’]\s*(?:anno|settiman[ae]|mes[ei]|giorn[oi]|or[ae]|minut[oi]|second[oi]|momento|istante)\b",

        # 8) “dell’ultimo anno/settimana/mese/…”
        r"\bdell['’]ultimo\s+(?:anno | settimana | mese | giorno | ora | minuto | secondo)s?\b",
    ],
}

# Requisiti rigidi per alcuni casi
CASE_REQUIREMENTS = {
    "WORD_NUMBER":          None,
    "SORT_UPLOAD_DATE":     "METADATA",
    "LIMIT_RESULTS":        None,
    "FIND_BY_AUTHOR":       "METADATA",
    "FILTER_BY_DATE_RANGE": "METADATA",
    "SEARCH_BY_KEYWORD":    "CONTENUTO",
    "ABOUT_TOPIC":          "CONTENUTO",
    "FILTER_BY_REL_TIME":   "METADATA",
    "DATE_TOKEN":           None,
}