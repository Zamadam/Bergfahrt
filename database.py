import sqlite3
import bcrypt # Für Admin-Passwort beim Setup
import os
import sys

# --- Konfiguration ---
DATABASE_NAME = 'mitfahr.db'
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin' # WICHTIG: Im echten Einsatz ein sichereres Passwort verwenden!

# --- Pfadermittlung für die Datenbankdatei ---
def _get_resource_path(relative_path=""):
    """
    Gibt den absoluten Pfad zu einer Ressource zurück.
    Für Streamlit-Apps wird der Pfad relativ zum Skript-Verzeichnis bestimmt.
    """
    base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)

# Der tatsächliche absolute Pfad zur Datenbankdatei
DB_PATH = os.path.join(_get_resource_path(), DATABASE_NAME)


# --- Datenbank-Manager-Klasse ---
class DBManager:
    def __init__(self):
        pass # Die Verbindung wird pro Abfrage geöffnet und geschlossen

    def execute_query(self, query, params=()):
        """Führt eine Schreib-/Lese-Abfrage aus und committet Änderungen."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row # Für den Zugriff auf Spaltennamen
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.fetchall() # Gibt Ergebnisse bei SELECT-Abfragen zurück
        except sqlite3.Error as e:
            # In Streamlit-Apps ist es besser, Fehler über st.error anzuzeigen
            # oder sie zu protokollieren, anstatt direkt zu printen oder zu raisen,
            # da dies die App zum Absturz bringen könnte.
            # print(f"Datenbankfehler bei Ausführung von '{query}': {e}")
            raise # Fehler weitergeben, damit main.py darauf reagieren kann

    def fetch_one(self, query, params=()):
        """Führt eine Abfrage aus und gibt die erste Zeile zurück."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row # Für den Zugriff auf Spaltennamen
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchone()
        except sqlite3.Error as e:
            # print(f"Datenbankfehler bei fetch_one von '{query}': {e}")
            return None

# --- Datenbank-Setup-Funktion ---
def setup_db():
    """
    Initialisiert die Datenbanktabellen (users, fahrten, buchungen) und fügt
    den Standard-Admin-Benutzer hinzu, falls sie nicht existieren.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Erstelle die users-Tabelle
            create_users_table_query = '''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                vorname TEXT NOT NULL,
                name TEXT NOT NULL,
                station TEXT,
                email TEXT NOT NULL,
                telefon TEXT,
                is_admin INTEGER DEFAULT 0
            );
            '''
            cursor.execute(create_users_table_query)

            # Erstelle die fahrten-Tabelle
            create_fahrten_table_query = '''
            CREATE TABLE IF NOT EXISTS fahrten (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                anbieter_id INTEGER NOT NULL,
                startort TEXT NOT NULL,
                zielort TEXT NOT NULL,
                datum TEXT NOT NULL, -- Format TT.MM.JJJJ
                uhrzeit TEXT NOT NULL, -- Format HH:MM
                freie_plaetze INTEGER NOT NULL,
                beschreibung TEXT,
                FOREIGN KEY (anbieter_id) REFERENCES users(id)
            );
            '''
            cursor.execute(create_fahrten_table_query)

            # Erstelle die buchungen-Tabelle
            create_buchungen_table_query = '''
            CREATE TABLE IF NOT EXISTS buchungen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nutzer_id INTEGER NOT NULL,
                fahrt_id INTEGER NOT NULL,
                buchungsdatum TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (nutzer_id) REFERENCES users(id),
                FOREIGN KEY (fahrt_id) REFERENCES fahrten(id),
                UNIQUE(nutzer_id, fahrt_id)
            );
            '''
            cursor.execute(create_buchungen_table_query)

            # Überprüfe und füge den Standard-Admin-Benutzer hinzu
            admin_exists = cursor.execute("SELECT id FROM users WHERE username = ?", (ADMIN_USERNAME,)).fetchone()
            if not admin_exists:
                hashed_password = bcrypt.hashpw(ADMIN_PASSWORD.encode(), bcrypt.gensalt())
                cursor.execute("INSERT INTO users (username, password, vorname, name, station, email, telefon, is_admin) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                            (ADMIN_USERNAME, hashed_password, 'System', 'Admin', 'Zentrale', 'admin@example.com', '0123456789', 1))
            conn.commit()

    except sqlite3.Error as e:
        # print(f"Fehler beim Initialisieren der Datenbank: {e}")
        raise # Fehler weitergeben, damit Streamlit darauf reagieren kann

# Removed the __main__ block as Streamlit handles app execution