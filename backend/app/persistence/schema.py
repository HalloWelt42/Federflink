"""SQLite-Schema - alle Tabellen und Indizes als ein SQL-String.

Konventionen:
- TEXT fuer Zeitstempel im ISO-8601-Format
- INTEGER fuer Booleans (0/1)
- Fremdschluessel mit explizitem ON DELETE-Verhalten

Inhalt der Datenbank (alles lokal, verlaesst den Projektordner nie):
- settings          zentrale, im UI aenderbare Betriebseinstellungen
- woerter           persoenliches Woerterbuch (Lernen Stufe 1)
- ngramme           N-Gramm-Haeufigkeiten (Lernen Stufe 1)
- kontext_passagen  eingebettete Passagen fuer den Umfeld-Kontext (Lernen Stufe 2)
- profile           benutzerdefinierte Schreibprofile (ergaenzen die eingebauten)
- lern_ereignisse   Telemetrie: Annahme/Ablehnung je Engine (Admin-Transparenz)
"""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS woerter (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wort TEXT NOT NULL,
    profil_id TEXT NOT NULL DEFAULT 'standard',
    haeufigkeit INTEGER NOT NULL DEFAULT 1,
    quelle TEXT NOT NULL DEFAULT 'gelernt',   -- gelernt | manuell
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (wort, profil_id)
);

CREATE TABLE IF NOT EXISTS ngramme (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profil_id TEXT NOT NULL DEFAULT 'standard',
    n INTEGER NOT NULL,                        -- Ordnung des N-Gramms (2, 3, ...)
    praefix TEXT NOT NULL,                     -- n-1 vorangehende Woerter, klein, leer-getrennt
    wort TEXT NOT NULL,                        -- vorhergesagtes Folgewort
    haeufigkeit INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL,
    UNIQUE (profil_id, n, praefix, wort)
);

CREATE TABLE IF NOT EXISTS kontext_passagen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profil_id TEXT NOT NULL DEFAULT 'standard',
    text TEXT NOT NULL,
    embedding BLOB,                            -- float32-Vektor, siehe kontext_speicher
    dim INTEGER NOT NULL DEFAULT 0,
    modell TEXT NOT NULL DEFAULT '',
    host TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS profile (
    id TEXT PRIMARY KEY,                       -- z. B. 'email-de'
    name TEXT NOT NULL,
    sprache TEXT NOT NULL DEFAULT 'de',
    beschreibung TEXT NOT NULL DEFAULT '',
    stil_prompt TEXT NOT NULL DEFAULT '',      -- System-Hinweis fuer die LLM-Ergaenzung
    host_muster TEXT NOT NULL DEFAULT '[]',    -- JSON-Liste von Host-Mustern -> dieses Profil
    aktiv INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lern_ereignisse (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engine TEXT NOT NULL DEFAULT '',
    art TEXT NOT NULL DEFAULT 'uebernahme',    -- uebernahme | ablehnung
    profil_id TEXT NOT NULL DEFAULT 'standard',
    host TEXT NOT NULL DEFAULT '',
    teil_uebernahme INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_woerter_profil ON woerter(profil_id);
CREATE INDEX IF NOT EXISTS idx_ngramme_lookup ON ngramme(profil_id, n, praefix);
CREATE INDEX IF NOT EXISTS idx_kontext_profil ON kontext_passagen(profil_id);
CREATE INDEX IF NOT EXISTS idx_lern_created ON lern_ereignisse(created_at);
CREATE INDEX IF NOT EXISTS idx_lern_engine ON lern_ereignisse(engine);
"""


# Migrationen fuer bereits existierende Datenbanken.
# Tupel: (tabellenname, spaltenname, SQL zum Anlegen).
MIGRATIONS: tuple[tuple[str, str, str], ...] = ()
