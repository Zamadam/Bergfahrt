import re
import datetime

# Globale Konstanten (Farben sind für Streamlit weniger direkt anwendbar,
# können aber für Markdown-Styling oder benutzerdefiniertes CSS verwendet werden,
# hier nur als Referenz beibehalten)
BACKGROUND = "#FFFFA5"
FOCUS_BG = "#FFD580"
STD_ENTRY = {"background": "#FFFFFF"} # Not directly used by Streamlit inputs

# Button colors are typically not directly styled this way in Streamlit
# unless custom CSS is applied. Keeping for reference.
BTN_COLORS = [
    ("#0C6170", "#FFFFFF"),
    ("#2c9237", "#FFFFFF"),
    ("#B44724", "#FFFFFF"),
    ("#FFC600", "#000000"),
    ("#FF6E40", "#FFFFFF"),
    ("#1d1c27", "#FFFFFF"),
    ("#A38560", "#FFFFFF"),
    ("#654E92", "#FFFFFF"),
    ("#C70039", "#FFFFFF"),
    ("#63C5DA", "#000000"),
]

# Removed Tkinter-specific functions like set_entry_focus and clear_frame_widgets
# as Streamlit handles UI rendering differently.

def format_date_entry(date_str):
    """
    Formats a date string to TT.MM.JJJJ.
    This function is more of a helper for input formatting logic,
    Streamlit text_inputs don't have direct keyRelease events for live formatting.
    """
    val = date_str.replace('.', '')
    val = ''.join([c for c in val if c.isdigit()])[:8]
    parts = []
    if len(val) >= 2:
        parts.append(val[:2])
        val = val[2:]
    if len(val) >= 2:
        parts.append(val[:2])
        val = val[2:]
    if len(val):
        parts.append(val)
    return ".".join(parts)

def validate_date(date_str):
    """
    Validiert, ob ein String ein gültiges Datum im Format TT.MM.JJJJ ist.
    """
    try:
        datetime.datetime.strptime(date_str, "%d.%m.%Y")
        return True
    except ValueError:
        return False

def validate_time(time_str):
    """
    Validiert, ob ein String eine gültige Uhrzeit im Format HH:MM ist.
    """
    try:
        hour, minute = map(int, time_str.split(':'))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return True
        return False
    except ValueError:
        return False

def validate_email(email):
    """
    Validiert eine E-Mail-Adresse mit einem regulären Ausdruck.
    """
    return re.fullmatch(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email)

def generate_time_options():
    """
    Generiert eine Liste von Uhrzeit-Strings in 10-Minuten-Schritten (HH:MM).
    """
    times = []
    for h in range(24):
        for m in range(0, 60, 10): # Changed from [0, 30] to range(0, 60, 10)
            times.append(f"{h:02d}:{m:02d}")
    return times

# Removed button color cycling logic as it's not directly applicable to Streamlit's default buttons.
# If custom CSS is used, this logic could be re-implemented.
# _btn_cycle_counter = 0
# def get_next_btn_color():
#     global _btn_cycle_counter
#     color = BTN_COLORS[_btn_cycle_counter % len(BTN_COLORS)]
#     _btn_cycle_counter += 1
#     return color

# def reset_btn_color_cycle():
#     global _btn_cycle_counter
#     _btn_cycle_counter = 0