import streamlit as st
import sqlite3
import bcrypt
import datetime
import os
from PIL import Image # Pillow wird weiterhin zum Laden von Bildern verwendet, ImageTk wird nicht benötigt
import database
import utils

# --- Streamlit App Setup ---

# Initialisiere Session-State-Variablen, falls sie noch nicht existieren
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_page' not in st.session_state:
    st.session_state.current_page = "landing"
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = database.DBManager()

# Stelle sicher, dass die Datenbank beim App-Start eingerichtet ist
database.setup_db()

# --- Ressourcenpfad für Bilder (vereinfacht für Streamlit) ---
def _get_resource_path(relative_path=""):
    """
    Gibt den absoluten Pfad zu einer Ressource zurück, relativ zum Skriptverzeichnis.
    Für Streamlit-Apps befinden sich Dateien typischerweise im selben Verzeichnis oder einem bekannten Unterordner.
    """
    base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)

# Lade das Logo-Bild einmal
logo_image_path = _get_resource_path('logo.png')
try:
    if os.path.exists(logo_image_path):
        logo_img = Image.open(logo_image_path)
        # Grösse bei Bedarf für die Anzeige in Streamlit anpassen
        # logo_img = logo_img.resize((100, 100), Image.Resampling.LANCZOS)
    else:
        logo_img = None
        st.warning(f"Logo-Bild nicht gefunden unter: {logo_image_path}")
except Exception as e:
    logo_img = None
    st.error(f"Fehler beim Laden von logo.png: {e}")

# --- Navigationsfunktionen ---
def navigate_to(page):
    st.session_state.current_page = page
    st.rerun() # Erzwinge eine Neuausführung, um die neue Seite anzuzeigen

def logout():
    st.session_state.logged_in = False
    st.session_state.current_user = None
    navigate_to("landing")

# --- Ansichten (Streamlit-Seiten) ---

def show_landing():
    st.title("Willkommen in Priminsberg Fahrt")
    if logo_img:
        st.image(logo_img, width=150) # Logo anzeigen
    
    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Anmelden", key="btn_login_landing"):
            navigate_to("login")
    with col2:
        if st.button("Registrieren", key="btn_register_landing"):
            navigate_to("register")

def show_login():
    st.title("Login")
    username = st.text_input("Benutzername:", key="login_username")
    password = st.text_input("Passwort:", type="password", key="login_password")
    
    st.markdown("Passwort vergessen? Bitte support kontaktieren.<br>Tel.: +41 78 313 6920 - Email: zamzam2204@yahoo.de", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Anmelden", key="btn_do_login"):
            user = st.session_state.db_manager.fetch_one("SELECT * FROM users WHERE username = ?", (username,))
            if user and bcrypt.checkpw(password.encode(), user['password']):
                st.session_state.current_user = user
                st.session_state.logged_in = True
                if user['is_admin'] == 1:
                    navigate_to("admin_menu")
                else:
                    navigate_to("profile")
            else:
                st.error("Login fehlgeschlagen!")
    with col2:
        if st.button("Zurück", key="btn_back_login"):
            navigate_to("landing")

def show_register():
    st.title("Registrierung")
    username = st.text_input("Benutzername:", key="reg_username")
    password = st.text_input("Passwort:", type="password", key="reg_password")
    vorname = st.text_input("Vorname:", key="reg_vorname")
    name = st.text_input("Name:", key="reg_name")
    station = st.text_input("Station:", key="reg_station")
    email = st.text_input("E-Mail:", key="reg_email")
    telefon = st.text_input("Telefon:", key="reg_telefon")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Registrieren", key="btn_do_register"):
            if not all([username, password, vorname, name, email]):
                st.error("Bitte füllen Sie alle erforderlichen Felder (Benutzername, Passwort, Vorname, Name, E-Mail) aus!")
                return

            if not utils.validate_email(email):
                st.error("Ungültige E-Mail-Adresse. Sie muss '@' und '.' enthalten und darf keine leeren Teile haben (z.B. 'test@example.com').")
                return

            # FIX: 'vals' was not defined. Use 'password' directly.
            pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            try:
                st.session_state.db_manager.execute_query("INSERT INTO users (username, password, vorname, name, station, email, telefon, is_admin) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                                     (username, pw_hash, vorname, name, station if station else None, email, telefon if telefon else None, 0))
                user_id = st.session_state.db_manager.fetch_one("SELECT id FROM users WHERE username = ?", (username,))['id']
                st.session_state.current_user = st.session_state.db_manager.fetch_one("SELECT * FROM users WHERE id=?", (user_id,))
                st.session_state.logged_in = True
                st.success("Registrierung abgeschlossen!")
                navigate_to("profile")
            except sqlite3.IntegrityError:
                st.error("Benutzername existiert bereits!")
    with col2:
        if st.button("Zurück", key="btn_back_register"):
            navigate_to("landing")

def show_profile():
    user = st.session_state.current_user
    if not user:
        st.warning("Nicht angemeldet. Bitte melden Sie sich an.")
        navigate_to("landing")
        return

    st.title("Benutzer-Menü & Profil")
    st.subheader("Ihr Profil:")
    st.write(f"**Benutzername:** {user['username']}")
    st.write(f"**Vorname:** {user['vorname']}")
    st.write(f"**Name:** {user['name']}")
    st.write(f"**Station:** {user['station'] if user['station'] is not None else 'Nicht angegeben'}")
    st.write(f"**Telefon:** {user['telefon'] if user['telefon'] is not None else 'Nicht angegeben'}")
    st.write(f"**E-Mail:** {user['email']}")

    st.subheader("Optionen:")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Fahrten anzeigen", key="btn_show_fahrten_anzeigen"):
            navigate_to("fahrten_anzeigen")
        if st.button("Fahrt anbieten", key="btn_show_fahrt_anbieten"):
            navigate_to("fahrt_anbieten")
        if st.button("Meine Fahrten", key="btn_show_meine_fahrten"):
            navigate_to("meine_fahrten")
    with col2:
        if st.button("Profil bearbeiten", key="btn_show_profil_bearbeiten"):
            navigate_to("profil_bearbeiten")
        if st.button("Passwort ändern", key="btn_show_change_password"):
            navigate_to("change_password")
        if st.button("Abmelden", key="btn_logout"):
            logout()

def show_admin_menu():
    user = st.session_state.current_user
    if not user or user['is_admin'] != 1:
        st.error("Zugriff verweigert. Sie sind kein Administrator.")
        logout()
        return

    st.title("Admin-Menü")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Alle Benutzer anzeigen", key="btn_show_all_users"):
            navigate_to("all_users")
        if st.button("Nutzerprofil löschen", key="btn_show_delete_user_prompt"):
            navigate_to("delete_user_prompt")
    with col2:
        if st.button("Profil bearbeiten", key="btn_admin_profil_bearbeiten"):
            navigate_to("profil_bearbeiten")
        if st.button("Passwort ändern", key="btn_admin_change_password"):
            navigate_to("change_password")
        if st.button("Abmelden", key="btn_admin_logout"):
            logout()

def show_all_users():
    user = st.session_state.current_user
    if not user or user['is_admin'] != 1:
        st.error("Zugriff verweigert.")
        logout()
        return

    st.title("Alle registrierten Benutzer")
    users = st.session_state.db_manager.execute_query("SELECT id, username, vorname, name, email, telefon, is_admin FROM users ORDER BY username")

    if not users:
        st.info("(Keine Benutzer gefunden.)")
    else:
        for user_data in users:
            st.markdown(f"**ID:** {user_data['id']} | **Benutzername:** {user_data['username']} | **Name:** {user_data['vorname']} {user_data['name']} | **E-Mail:** {user_data['email']} | **Tel:** {user_data['telefon'] if user_data['telefon'] else 'N/A'} | **Admin:** {'Ja' if user_data['is_admin'] else 'Nein'}")
            st.markdown("---") # Trennlinie

    back_command_page = "admin_menu" if st.session_state.current_user and st.session_state.current_user['is_admin'] == 1 else "profile"
    if st.button("Zurück", key="btn_back_all_users"):
        navigate_to(back_command_page)

def show_delete_user_prompt():
    user = st.session_state.current_user
    if not user or user['is_admin'] != 1:
        st.error("Zugriff verweigert.")
        logout()
        return

    st.title("Nutzerprofil löschen")
    target_username = st.text_input("Benutzername des zu löschenden Nutzers:", key="delete_username_input")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Benutzer löschen", key="btn_delete_user_action"):
            if not target_username:
                st.error("Bitte einen Benutzernamen eingeben.")
                return

            if target_username == "admin":
                st.error("Der Admin-Benutzer kann nicht gelöscht werden!")
                return

            # Streamlit hat keine direkte messagebox.askyesno, simuliere dies mit Session State
            if st.session_state.get('confirm_delete', False) == False:
                st.session_state.confirm_delete = True
                st.warning(f"Möchten Sie den Benutzer '{target_username}' wirklich löschen? Alle zugehörigen Fahrten und Buchungen werden ebenfalls gelöscht.")
                st.button("Ja, Benutzer löschen", key="confirm_delete_btn")
                st.button("Nein, Abbrechen", key="cancel_delete_btn")
                return
            
            if st.session_state.get('confirm_delete_btn_clicked', False):
                user_to_delete = st.session_state.db_manager.fetch_one("SELECT id FROM users WHERE username = ?", (target_username,))

                if user_to_delete:
                    user_id = user_to_delete['id']
                    st.session_state.db_manager.execute_query("DELETE FROM fahrten WHERE anbieter_id = ?", (user_id,))
                    st.session_state.db_manager.execute_query("DELETE FROM buchungen WHERE nutzer_id = ?", (user_id,))
                    st.session_state.db_manager.execute_query("DELETE FROM buchungen WHERE fahrt_id IN (SELECT id FROM fahrten WHERE anbieter_id = ?)", (user_id,))
                    st.session_state.db_manager.execute_query("DELETE FROM users WHERE id = ?", (user_id,))
                    st.success(f"Benutzer '{target_username}' und alle zugehörigen Daten wurden gelöscht.")
                else:
                    st.error(f"Benutzer '{target_username}' nicht gefunden.")
                st.session_state.confirm_delete = False # Bestätigung zurücksetzen
                st.session_state.confirm_delete_btn_clicked = False
                navigate_to("admin_menu")
            elif st.session_state.get('cancel_delete_btn_clicked', False):
                st.session_state.confirm_delete = False
                st.session_state.cancel_delete_btn_clicked = False
                navigate_to("admin_menu")
    with col2:
        if st.button("Zurück zum Admin-Menü", key="btn_back_delete_user"):
            st.session_state.confirm_delete = False # Bestätigung zurücksetzen
            navigate_to("admin_menu")

    # Bestätigungs-Buttons behandeln
    if st.session_state.get('confirm_delete', False):
        if st.button("Ja, Benutzer löschen", key="confirm_delete_btn_actual"):
            st.session_state.confirm_delete_btn_clicked = True
            st.rerun() # Neuausführung auslösen, um die Löschlogik auszuführen
        if st.button("Nein, Abbrechen", key="cancel_delete_btn_actual"):
            st.session_state.cancel_delete_btn_clicked = True
            st.rerun() # Neuausführung auslösen, um die Abbruchlogik auszuführen


def show_change_password():
    user = st.session_state.current_user
    if not user:
        st.warning("Nicht angemeldet.")
        navigate_to("landing")
        return

    st.title("Passwort ändern")
    old_pw = st.text_input("Altes Passwort:", type="password", key="old_pw")
    new_pw = st.text_input("Neues Passwort:", type="password", key="new_pw")
    confirm_new_pw = st.text_input("Neues Passwort wiederholen:", type="password", key="confirm_new_pw")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Passwort ändern", key="btn_do_change_password"):
            if not old_pw or not new_pw or not confirm_new_pw:
                st.error("Bitte alle Felder ausfüllen.")
                return

            if new_pw != confirm_new_pw:
                st.error("Neue Passwörter stimmen nicht überein.")
                return

            if not new_pw:
                st.error("Neues Passwort darf nicht leer sein.")
                return

            stored_hash = st.session_state.db_manager.fetch_one("SELECT password FROM users WHERE id = ?", (user['id'],))['password']

            if bcrypt.checkpw(old_pw.encode(), stored_hash):
                new_pw_hash = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt())
                st.session_state.db_manager.execute_query("UPDATE users SET password = ? WHERE id = ?", (new_pw_hash, user['id']))
                st.success("Passwort erfolgreich geändert!")
                if user['is_admin'] == 1:
                    navigate_to("admin_menu")
                else:
                    navigate_to("profile")
            else:
                st.error("Altes Passwort ist falsch.")
    with col2:
        back_command_page = "admin_menu" if user['is_admin'] == 1 else "profile"
        if st.button("Zurück", key="btn_back_change_password"):
            navigate_to(back_command_page)

def show_fahrten_anzeigen():
    user = st.session_state.current_user
    if not user:
        st.warning("Nicht angemeldet.")
        navigate_to("landing")
        return

    st.title("Verfügbare Fahrten")

    # Datum- und zeitbasierte Löschung für vergangene Fahrten
    st.session_state.db_manager.execute_query("""
        DELETE FROM fahrten
        WHERE (substr(datum,7,4)||substr(datum,4,2)||substr(datum,1,2) || ' ' || uhrzeit) < strftime('%Y%m%d %H:%M','now', 'localtime')
    """)

    rows = st.session_state.db_manager.execute_query('''
        SELECT f.id, u.username, f.startort, f.zielort, f.datum, f.uhrzeit, f.freie_plaetze,
                       u.vorname, u.name, u.email, u.telefon, f.beschreibung
        FROM fahrten f
        JOIN users u ON f.anbieter_id=u.id
        WHERE f.freie_plaetze > 0
          AND (substr(f.datum,7,4)||substr(f.datum,4,2)||substr(f.datum,1,2) || ' ' || f.uhrzeit) >= strftime('%Y%m%d %H:%M','now', 'localtime')
          AND f.anbieter_id != ?
          AND f.id NOT IN (SELECT fahrt_id FROM buchungen WHERE nutzer_id=?)
        ORDER BY substr(f.datum,7,4)||substr(f.datum,4,2)||substr(f.datum,1,2) ASC, time(f.uhrzeit) ASC
    ''', (user['id'], user['id']))
    
    st.session_state.fahrten_liste = rows # Speichere für die Detailansicht

    if not rows:
        st.info("(Keine buchbaren Fahrten gefunden.)")
    else:
        for idx, r in enumerate(rows):
            btntext = f"{r['startort']} → {r['zielort']}, {r['datum']} {r['uhrzeit']}, Anbieter:{r['username']}, Plätze:{r['freie_plaetze']}"
            if st.button(btntext, key=f"fahrt_btn_{r['id']}"):
                st.session_state.selected_fahrt_idx = idx
                navigate_to("fahrt_detail")
            st.markdown("---") # Trennlinie

    back_command_page = "admin_menu" if user['is_admin'] == 1 else "profile"
    if st.button("Zurück", key="btn_back_fahrten_anzeigen"):
        navigate_to(back_command_page)

def show_fahrt_detail():
    user = st.session_state.current_user
    if not user:
        st.warning("Nicht angemeldet.")
        navigate_to("landing")
        return
    
    if 'selected_fahrt_idx' not in st.session_state or st.session_state.selected_fahrt_idx is None:
        st.warning("Keine Fahrt ausgewählt.")
        navigate_to("fahrten_anzeigen")
        return

    idx = st.session_state.selected_fahrt_idx
    row = st.session_state.fahrten_liste[idx]
    fahrt_id = row['id']

    st.title("Fahrtdetails")
    st.subheader("Strecke & Zeit:")
    st.write(f"**Strecke:** {row['startort']} → {row['zielort']}")
    st.write(f"**Datum:** {row['datum']}")
    st.write(f"**Uhrzeit:** {row['uhrzeit']}")
    st.write(f"**Freie Plätze:** {row['freie_plaetze']}")
    st.write(f"**Beschreibung:** {row['beschreibung'] if row['beschreibung'] else 'Keine Angabe'}")

    st.subheader("Fahrerinformationen:")
    st.write(f"**Fahrer:** {row['vorname']} {row['name']}")
    st.write(f"**Benutzername:** {row['username']}")
    st.write(f"**E-Mail:** {row['email']}")
    st.write(f"**Telefon:** {row['telefon']}")

    st.subheader("Mitfahrer:")
    mitfahrer = st.session_state.db_manager.execute_query('''SELECT u.vorname, u.name, u.username, u.email, u.telefon
                                   FROM buchungen b
                                     JOIN users u ON b.nutzer_id = u.id
                                   WHERE b.fahrt_id=?
                                ''', (fahrt_id,))
    if not mitfahrer:
        st.info("Noch keine Mitfahrer.")
    else:
        for m in mitfahrer:
            st.write(f"- {m['vorname']} {m['name']} ({m['username']}) Tel:{m['telefon']}")

    if row['freie_plaetze'] > 0:
        if st.button("Fahrt buchen", key="btn_buchen_fahrt_detail"):
            frei_now = st.session_state.db_manager.fetch_one("SELECT freie_plaetze FROM fahrten WHERE id=?", (fahrt_id,))
            if not frei_now or frei_now['freie_plaetze'] <= 0:
                st.error("Diese Fahrt ist nicht mehr buchbar!")
                navigate_to("fahrten_anzeigen")
                return
            
            bereits_gebucht = st.session_state.db_manager.fetch_one("SELECT id FROM buchungen WHERE nutzer_id=? AND fahrt_id=?", (user['id'], fahrt_id))
            if bereits_gebucht:
                st.info("Sie haben diese Fahrt bereits gebucht.")
                return

            st.session_state.db_manager.execute_query("INSERT INTO buchungen (nutzer_id, fahrt_id) VALUES (?, ?)",
                                                     (user['id'], fahrt_id))
            st.session_state.db_manager.execute_query("UPDATE fahrten SET freie_plaetze=freie_plaetze-1 WHERE id=?", (fahrt_id,))
            st.success("Fahrt erfolgreich gebucht!")
            navigate_to("fahrten_anzeigen")
    else:
        st.warning("Keine Plätze mehr frei.")

    if st.button("Zurück zur Fahrtenliste", key="btn_back_fahrt_detail"):
        navigate_to("fahrten_anzeigen")

def show_fahrt_anbieten():
    user = st.session_state.current_user
    if not user:
        st.warning("Nicht angemeldet.")
        navigate_to("landing")
        return

    st.title("Fahrt anbieten")
    startort = st.text_input("Startort:", key="fahrt_anbieten_startort")
    zielort = st.text_input("Zielort:", key="fahrt_anbieten_zielort")
    
    # Datum mit Kalender
    datum_obj = st.date_input("Datum:", value=datetime.date.today(), key="fahrt_anbieten_datum")
    
    # Uhrzeit mit Dropdown
    time_options = utils.generate_time_options()
    current_time = datetime.datetime.now()
    # Runden auf die nächste 10-Minuten-Marke
    current_minute_rounded = (current_time.minute // 10) * 10
    if current_time.minute % 10 != 0:
        current_minute_rounded += 10
        if current_minute_rounded >= 60:
            current_minute_rounded = 0
            current_time += datetime.timedelta(hours=1)
    
    initial_time_str = f"{current_time.hour:02d}:{current_minute_rounded:02d}"

    initial_time_index = 0
    if initial_time_str in time_options:
        initial_time_index = time_options.index(initial_time_str)
    
    uhrzeit = st.selectbox("Uhrzeit:", options=time_options, index=initial_time_index, key="fahrt_anbieten_uhrzeit")
    
    freie_plaetze = st.number_input("Freie Plätze (Zahl):", min_value=1, value=1, step=1, key="fahrt_anbieten_plaetze")
    beschreibung = st.text_area("Beschreibung (optional):", key="fahrt_anbieten_beschreibung")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Fahrt speichern", key="btn_fahrt_anbieten_save"):
            # Datum-Objekt in String für Validierung und DB-Speicherung umwandeln
            datum_str = datum_obj.strftime("%d.%m.%Y")

            if not all([startort, zielort, datum_str, uhrzeit, freie_plaetze]):
                st.error("Alle Pflichtfelder ausfüllen!")
                return

            if not utils.validate_date(datum_str):
                st.error("Datum muss im Format TT.MM.JJJJ sein und ein gültiges Datum darstellen!")
                return
            if not utils.validate_time(uhrzeit):
                st.error("Uhrzeit muss im Format HH:MM sein und eine gültige Uhrzeit darstellen (00:00-23:59)!")
                return

            try:
                dt_obj = datetime.datetime.strptime(datum_str + " " + uhrzeit, "%d.%m.%Y %H:%M")
                if dt_obj < datetime.datetime.now():
                    st.error("Fahrt kann nicht in der Vergangenheit liegen!")
                    return
            except ValueError:
                st.error("Ungültiges Datum oder Uhrzeit-Format nach Validierung (interner Fehler).")
                return

            try:
                freie_plaetze_int = int(freie_plaetze)
                if not freie_plaetze_int > 0:
                    st.error("Freie Plätze muss eine positive Zahl sein!")
                    return
            except Exception:
                st.error("Freie Plätze muss eine positive Zahl sein!")
                return

            st.session_state.db_manager.execute_query("INSERT INTO fahrten (anbieter_id, startort, zielort, datum, uhrzeit, freie_plaetze, beschreibung) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                                     (user['id'], startort, zielort, datum_str, uhrzeit, freie_plaetze_int, beschreibung if beschreibung else None))
            st.success("Fahrt angelegt!")
            navigate_to("profile")
    with col2:
        back_command_page = "admin_menu" if user['is_admin'] == 1 else "profile"
        if st.button("Zurück", key="btn_fahrt_anbieten_back"):
            navigate_to(back_command_page)

def show_meine_fahrten():
    user = st.session_state.current_user
    if not user:
        st.warning("Nicht angemeldet.")
        navigate_to("landing")
        return

    st.title("Meine Fahrten")

    st.subheader("Gebuchte Fahrten")
    st.session_state.db_manager.execute_query("""
        DELETE FROM buchungen
        WHERE fahrt_id IN (
            SELECT id FROM fahrten
            WHERE (substr(datum,7,4)||substr(datum,4,2)||substr(datum,1,2) || ' ' || uhrzeit) < strftime('%Y%m%d %H:%M','now', 'localtime')
        )
    """)

    gebuchte = st.session_state.db_manager.execute_query(
            """SELECT f.id, u.username, f.startort, f.zielort, f.datum, f.uhrzeit, f.freie_plaetze,
                            f.anbieter_id, b.id AS buchungs_id, u.vorname, u.name, u.telefon, f.beschreibung
               FROM buchungen b
               JOIN fahrten f on b.fahrt_id = f.id
               JOIN users u on f.anbieter_id = u.id
               WHERE b.nutzer_id=? AND (substr(f.datum,7,4)||substr(f.datum,4,2)||substr(f.datum,1,2) || ' ' || f.uhrzeit) >= strftime('%Y%m%d %H:%M','now', 'localtime')
               ORDER BY substr(f.datum,7,4)||substr(f.datum,4,2)||substr(f.datum,1,2), f.uhrzeit""",
            (user['id'],))
    
    if not gebuchte:
        st.info("Sie haben keine buchbaren Fahrten gebucht.")
    else:
        for f in gebuchte:
            fahrttext = f"{f['startort']} → {f['zielort']}, {f['datum']} {f['uhrzeit']}, Fahrer: {f['vorname']} {f['name']} ({f['username']}) Tel:{f['telefon']}"
            if f['beschreibung']:
                fahrttext += f" | Beschreibung: {f['beschreibung']}"
            
            col_fahrt, col_button = st.columns([0.7, 0.3])
            with col_fahrt:
                st.write(fahrttext)
            with col_button:
                if st.button("Buchung stornieren", key=f"storno_btn_{f['buchungs_id']}"):
                    r = st.session_state.db_manager.fetch_one("SELECT fahrt_id FROM buchungen WHERE id=?", (f['buchungs_id'],))
                    if r:
                        fahrtid = r['fahrt_id']
                        st.session_state.db_manager.execute_query("UPDATE fahrten SET freie_plaetze=freie_plaetze+1 WHERE id=?", (fahrtid,))
                    st.session_state.db_manager.execute_query("DELETE FROM buchungen WHERE id=?", (f['buchungs_id'],))
                    st.success("Buchung wurde storniert!")
                    navigate_to("meine_fahrten") # Seite aktualisieren

    st.subheader("Angebotene Fahrten")
    angebotene = st.session_state.db_manager.execute_query(
            "SELECT id, startort, zielort, datum, uhrzeit, freie_plaetze, beschreibung FROM fahrten WHERE anbieter_id=? ORDER BY substr(datum,7,4)||substr(datum,4,2)||substr(datum,1,2), uhrzeit",
            (user['id'],))
    
    if not angebotene:
        st.info("Sie haben keine eigenen Fahrten angeboten.")
    else:
        for f in angebotene:
            fahrttext = f"{f['startort']} → {f['zielort']}, {f['datum']} {f['uhrzeit']}, Plätze:{f['freie_plaetze']}"
            if f['beschreibung']:
                fahrttext += f" | Beschreibung: {f['beschreibung']}"
            
            col_fahrt, col_edit, col_delete = st.columns([0.6, 0.2, 0.2])
            with col_fahrt:
                st.write(fahrttext)
            with col_edit:
                if st.button("Bearbeiten", key=f"edit_btn_{f['id']}"):
                    st.session_state.edit_fahrt_id = f['id']
                    navigate_to("edit_fahrt")
            with col_delete:
                if st.button("Löschen", key=f"delete_btn_{f['id']}"):
                    # messagebox.askyesno simulieren
                    if st.session_state.get(f'confirm_delete_fahrt_{f["id"]}', False) == False:
                        st.session_state[f'confirm_delete_fahrt_{f["id"]}'] = True
                        st.warning("Wirklich diese Fahrt komplett löschen? Alle zugehörigen Buchungen werden ebenfalls gelöscht.")
                        st.button("Ja, Fahrt löschen", key=f"confirm_delete_fahrt_yes_{f['id']}")
                        st.button("Nein, Abbrechen", key=f"confirm_delete_fahrt_no_{f['id']}")
                        return
                    
                    if st.session_state.get(f'confirm_delete_fahrt_yes_{f["id"]}_clicked', False):
                        st.session_state.db_manager.execute_query("DELETE FROM fahrten WHERE id=?", (f['id'],))
                        st.session_state.db_manager.execute_query("DELETE FROM buchungen WHERE fahrt_id=?", (f['id'],))
                        st.success("Fahrt wurde gelöscht!")
                        st.session_state[f'confirm_delete_fahrt_{f["id"]}'] = False
                        st.session_state[f'confirm_delete_fahrt_yes_{f["id"]}_clicked'] = False
                        navigate_to("meine_fahrten")
                    elif st.session_state.get(f'confirm_delete_fahrt_no_{f["id"]}_clicked', False):
                        st.session_state[f'confirm_delete_fahrt_{f["id"]}'] = False
                        st.session_state[f'confirm_delete_fahrt_no_{f["id"]}_clicked'] = False
                        navigate_to("meine_fahrten")
            
            # Bestätigungs-Buttons für Löschen behandeln
            if st.session_state.get(f'confirm_delete_fahrt_{f["id"]}', False):
                if st.button("Ja, Fahrt löschen", key=f"confirm_delete_fahrt_yes_actual_{f['id']}"):
                    st.session_state[f'confirm_delete_fahrt_yes_{f["id"]}_clicked'] = True
                    st.rerun()
                if st.button("Nein, Abbrechen", key=f"confirm_delete_fahrt_no_actual_{f['id']}"):
                    st.session_state[f'confirm_delete_fahrt_no_{f["id"]}_clicked'] = True
                    st.rerun()


    back_command_page = "admin_menu" if user['is_admin'] == 1 else "profile"
    if st.button("Zurück", key="btn_back_meine_fahrten"):
        navigate_to(back_command_page)

def edit_fahrt():
    user = st.session_state.current_user
    if not user:
        st.warning("Nicht angemeldet.")
        navigate_to("landing")
        return

    fahrt_id = st.session_state.get('edit_fahrt_id')
    if not fahrt_id:
        st.error("Keine Fahrt zum Bearbeiten ausgewählt.")
        navigate_to("meine_fahrten")
        return

    r = st.session_state.db_manager.fetch_one("SELECT startort, zielort, datum, uhrzeit, freie_plaetze, beschreibung FROM fahrten WHERE id=?", (fahrt_id,))
    if not r:
        st.error("Fahrt existiert nicht mehr!")
        navigate_to("meine_fahrten")
        return

    st.title("Fahrt bearbeiten")
    
    startort = st.text_input("Startort:", value=r['startort'], key="edit_fahrt_startort")
    zielort = st.text_input("Zielort:", value=r['zielort'], key="edit_fahrt_zielort")
    
    # Datum mit Kalender (initialer Wert aus DB-Daten)
    initial_date = datetime.datetime.strptime(r['datum'], "%d.%m.%Y").date()
    datum_obj = st.date_input("Datum:", value=initial_date, key="edit_fahrt_datum")
    
    # Uhrzeit mit Dropdown (initialer Wert aus DB-Daten)
    time_options = utils.generate_time_options()
    initial_time_index = time_options.index(r['uhrzeit']) if r['uhrzeit'] in time_options else 0
    uhrzeit = st.selectbox("Uhrzeit:", options=time_options, index=initial_time_index, key="edit_fahrt_uhrzeit")
    
    freie_plaetze = st.number_input("Freie Plätze (Zahl):", min_value=1, value=r['freie_plaetze'], step=1, key="edit_fahrt_plaetze")
    beschreibung = st.text_area("Beschreibung (optional):", value=r['beschreibung'] if r['beschreibung'] else "", key="edit_fahrt_beschreibung")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Speichern", key="btn_edit_fahrt_save"):
            # Datum-Objekt in String für Validierung und DB-Speicherung umwandeln
            datum_str = datum_obj.strftime("%d.%m.%Y")

            if not all([startort, zielort, datum_str, uhrzeit, freie_plaetze]):
                st.error("Alle Pflichtfelder ausfüllen!")
                return

            if not utils.validate_date(datum_str):
                st.error("Datum muss im Format TT.MM.JJJJ sein und ein gültiges Datum darstellen!")
                return
            if not utils.validate_time(uhrzeit):
                st.error("Uhrzeit muss im Format HH:MM sein und eine gültige Uhrzeit darstellen (00:00-23:59)!")
                return
            try:
                dt_obj = datetime.datetime.strptime(datum_str + " " + uhrzeit, "%d.%m.%Y %H:%M")
                if dt_obj < datetime.datetime.now():
                    st.error("Fahrt kann nicht in der Vergangenheit liegen!")
                    return
            except ValueError:
                st.error("Ungültiges Datum oder Uhrzeit-Format nach Validierung (interner Fehler).")
                return

            try:
                freie_plaetze_int = int(freie_plaetze)
                if not freie_plaetze_int > 0:
                    st.error("Freie Plätze muss Zahl >0 sein!")
                    return
            except:
                st.error("Freie Plätze muss Zahl >0 sein!")
                return
            
            st.session_state.db_manager.execute_query("UPDATE fahrten SET startort=?, zielort=?, datum=?, uhrzeit=?, freie_plaetze=?, beschreibung=? WHERE id=?",
                                                     (startort, zielort, datum_str, uhrzeit, freie_plaetze_int, beschreibung if beschreibung else None, fahrt_id))
            st.success("Fahrt aktualisiert!")
            navigate_to("meine_fahrten")
    with col2:
        back_command_page = "admin_menu" if user['is_admin'] == 1 else "profile"
        if st.button("Abbrechen", key="btn_edit_fahrt_cancel"):
            navigate_to(back_command_page)

def show_profil_bearbeiten():
    user = st.session_state.current_user
    if not user:
        st.warning("Nicht angemeldet.")
        navigate_to("landing")
        return

    st.title("Profil bearbeiten")
    
    # Werte aus current_user vorab füllen
    vorname = st.text_input("Vorname:", value=user['vorname'], key="edit_vorname")
    name = st.text_input("Name:", value=user['name'], key="edit_name")
    station = st.text_input("Station:", value=user['station'] if user['station'] is not None else "", key="edit_station")
    telefon = st.text_input("Telefon:", value=user['telefon'] if user['telefon'] is not None else "", key="edit_telefon")
    email = st.text_input("E-Mail:", value=user['email'], key="edit_email")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Speichern", key="btn_profil_bearbeiten_save"):
            if not all([vorname, name, email]):
                st.error("Vorname, Name und E-Mail dürfen nicht leer sein!")
                return

            if not utils.validate_email(email):
                st.error("Ungültige E-Mail-Adresse. Sie muss '@' und '.' enthalten und darf keine leeren Teile haben (z.B. 'test@example.com').")
                return

            st.session_state.db_manager.execute_query("UPDATE users SET vorname=?, name=?, station=?, telefon=?, email=? WHERE id=?",
                                                     (vorname, name, station if station else None, telefon if telefon else None, email, user['id']))
            
            # Aktuellen Benutzer im Session State mit den neuesten Daten aus der DB aktualisieren
            st.session_state.current_user = st.session_state.db_manager.fetch_one("SELECT * FROM users WHERE id=?", (user['id'],))
            st.success("Profil aktualisiert!")
            navigate_to("profile") # Nach dem Speichern zum Profil zurückkehren
    with col2:
        back_command_page = "admin_menu" if user['is_admin'] == 1 else "profile"
        if st.button("Zurück", key="btn_profil_bearbeiten_back"):
            navigate_to(back_command_page)


# --- Haupt-App-Logik (Router) ---
if st.session_state.logged_in:
    if st.session_state.current_page == "profile":
        show_profile()
    elif st.session_state.current_page == "admin_menu":
        show_admin_menu()
    elif st.session_state.current_page == "all_users":
        show_all_users()
    elif st.session_state.current_page == "delete_user_prompt":
        show_delete_user_prompt()
    elif st.session_state.current_page == "change_password":
        show_change_password()
    elif st.session_state.current_page == "fahrten_anzeigen":
        show_fahrten_anzeigen()
    elif st.session_state.current_page == "fahrt_detail":
        show_fahrt_detail()
    elif st.session_state.current_page == "fahrt_anbieten":
        show_fahrt_anbieten()
    elif st.session_state.current_page == "meine_fahrten":
        show_meine_fahrten()
    elif st.session_state.current_page == "edit_fahrt":
        edit_fahrt()
    elif st.session_state.current_page == "profil_bearbeiten":
        show_profil_bearbeiten()
    else: # Standard, wenn angemeldet, aber Seite unbekannt
        if st.session_state.current_user['is_admin'] == 1:
            show_admin_menu()
        else:
            show_profile()
else: # Nicht angemeldet
    if st.session_state.current_page == "register":
        show_register()
    elif st.session_state.current_page == "login": # Hinzugefügt, um die Login-Seite korrekt anzuzeigen
        show_login()
    else: # Standard für nicht angemeldet
        show_landing()
