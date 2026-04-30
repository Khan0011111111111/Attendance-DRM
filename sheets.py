# sheets.py — Google Sheets helper
# Handles both user accounts (stored in a "Users" sheet)
# and attendance data (stored in subject sheets like "U", "P", etc.)

# ADD this line:
import hashlib  # add this at the top with other imports

def _prepare_password(password: str) -> bytes:
    """Hash password with SHA-256 first to bypass bcrypt's 72-byte limit."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest().encode("utf-8")

def create_user(email: str, password: str, reg_no: str):
    email  = email.strip().lower()
    reg_no = reg_no.strip().upper()

    if email_exists(email):
        raise ValueError("This email is already registered.")
    if reg_no_exists(reg_no):
        raise ValueError("This registration number is already registered.")

    password_hash = bcrypt.hashpw(
        _prepare_password(password), bcrypt.gensalt(rounds=12)
    ).decode("utf-8")

    spreadsheet = get_spreadsheet()
    ws = _get_or_create_users_sheet(spreadsheet)
    ws.append_row([email, password_hash, reg_no])


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(_prepare_password(plain), hashed.encode("utf-8"))
# ADD this line:
from passlib.hash import bcrypt
import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

# ── Constants ────────────────────────────────────────────────────────────────

# The tab that stores registered users
USERS_SHEET_NAME = "Users"

# Users sheet columns (1-indexed for gspread)
COL_EMAIL    = 1
COL_HASH     = 2
COL_REG_NO   = 3

# Scopes needed: read+write for user management, read for attendance
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

# ── Auth ─────────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def get_client():
    """
    Build and cache a gspread client using service account credentials
    stored in Streamlit secrets. The client is reused across all calls.
    """
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES,
    )
    return gspread.authorize(creds)


def get_spreadsheet():
    """Open the spreadsheet by ID from Streamlit secrets."""
    client = get_client()
    return client.open_by_key(st.secrets["GOOGLE_SHEET_ID"])


# ── Users sheet helpers ───────────────────────────────────────────────────────

def _get_or_create_users_sheet(spreadsheet):
    """
    Return the Users worksheet, creating it (with a header row) if it
    doesn't exist yet. This runs automatically on first signup.
    """
    try:
        return spreadsheet.worksheet(USERS_SHEET_NAME)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(
            title=USERS_SHEET_NAME, rows=500, cols=3
        )
        ws.append_row(["Email", "PasswordHash", "RegistrationNo"])
        return ws


def find_user_by_email(email: str) -> dict | None:
    """
    Look up a user by email address.
    Returns a dict with keys: email, password_hash, registration_no
    or None if not found.
    """
    email = email.strip().lower()
    spreadsheet = get_spreadsheet()
    ws = _get_or_create_users_sheet(spreadsheet)
    records = ws.get_all_records()          # list of dicts (header row as keys)

    for row in records:
        if row.get("Email", "").strip().lower() == email:
            return {
                "email": row["Email"],
                "password_hash": row["PasswordHash"],
                "registration_no": row["RegistrationNo"],
            }
    return None


def email_exists(email: str) -> bool:
    return find_user_by_email(email) is not None


def reg_no_exists(reg_no: str) -> bool:
    """Check whether a registration number is already registered."""
    reg_no = reg_no.strip().upper()
    spreadsheet = get_spreadsheet()
    ws = _get_or_create_users_sheet(spreadsheet)
    records = ws.get_all_records()
    for row in records:
        if row.get("RegistrationNo", "").strip().upper() == reg_no:
            return True
    return False


def create_user(email: str, password: str, reg_no: str):
    email  = email.strip().lower()
    reg_no = reg_no.strip().upper()

    if email_exists(email):
        raise ValueError("This email is already registered.")
    if reg_no_exists(reg_no):
        raise ValueError("This registration number is already registered.")

    # passlib syntax (replaces bcrypt.hashpw)
    password_hash = bcrypt.hash(password)

    spreadsheet = get_spreadsheet()
    ws = _get_or_create_users_sheet(spreadsheet)
    ws.append_row([email, password_hash, reg_no])


def verify_password(plain: str, hashed: str) -> bool:
    # passlib syntax (replaces bcrypt.checkpw)
    return bcrypt.verify(plain, hashed)


# ── Attendance helpers ────────────────────────────────────────────────────────

def _parse_status(raw: str) -> tuple[str, str, str]:
    """
    Map a raw cell value to (emoji, label, css_class).
    2P → Present, 2A → Absent, L → Leave, anything else → Unknown.
    """
    v = (raw or "").strip().upper()
    if v == "2P": return "🟢", "Present", "present"
    if v == "2A": return "🔴", "Absent",  "absent"
    if v == "L":  return "🟡", "Leave",   "leave"
    return "⬜", "—", "unknown"


def fetch_attendance(reg_no: str) -> dict | None:
    """
    Search every sheet (except Users) for the student's registration number.
    Returns a dict with name, weeks list, attendancePct, sheetName,
    or None if not found.
    """
    reg_no = reg_no.strip().upper()
    spreadsheet = get_spreadsheet()

    for ws in spreadsheet.worksheets():
        if ws.title == USERS_SHEET_NAME:
            continue                        # skip the users sheet

        rows = ws.get_all_values()          # list of lists
        if len(rows) < 2:
            continue

        header = rows[0]

        # Find week columns dynamically by header name
        week_indices = [
            i for i, h in enumerate(header)
            if h.strip().lower().startswith("week")
        ]
        week_labels = [header[i].strip() for i in week_indices]

        # Find the Attendance (%) column
        att_col = next(
            (i for i, h in enumerate(header) if "attendance" in h.lower()),
            None,
        )

        # Search rows for this student
        for row in rows[1:]:
            row_reg = (row[1] if len(row) > 1 else "").strip().upper()
            if row_reg != reg_no:
                continue

            weeks = []
            for idx, label in zip(week_indices, week_labels):
                raw = row[idx].strip() if idx < len(row) else ""
                emoji, status, css = _parse_status(raw)
                weeks.append({
                    "label":  label,
                    "raw":    raw,
                    "emoji":  emoji,
                    "status": status,
                    "css":    css,
                })

            att_pct = (
                row[att_col].strip() if att_col is not None and att_col < len(row)
                else "N/A"
            )

            return {
                "name":           (row[2] if len(row) > 2 else "").strip(),
                "registration_no": row_reg,
                "weeks":          weeks,
                "attendance_pct": att_pct,
                "sheet_name":     ws.title,
            }

    return None     # not found in any sheet
