# sheets.py — Google Sheets helper
# Handles both user accounts (stored in a "Users" sheet)
# and attendance data (stored in subject sheets like "U", "P", etc.)

import hashlib
import os
import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

# ── Constants ─────────────────────────────────────────────────────────────────

USERS_SHEET_NAME = "Users"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

# ── Auth ──────────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def get_client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES,
    )
    return gspread.authorize(creds)


def get_spreadsheet():
    client = get_client()
    return client.open_by_key(st.secrets["GOOGLE_SHEET_ID"])


# ── Password helpers (no external packages) ───────────────────────────────────

def _hash_password(password: str, salt: str = None) -> str:
    """Hash password using PBKDF2-SHA256 — built into Python, no size limits."""
    if salt is None:
        salt = os.urandom(32).hex()
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=260000,
    ).hex()
    return f"{salt}${key}"


def verify_password(plain: str, stored: str) -> bool:
    try:
        salt, _ = stored.split("$")
        return _hash_password(plain, salt) == stored
    except Exception:
        return False


# ── Users sheet helpers ───────────────────────────────────────────────────────

def _get_or_create_users_sheet(spreadsheet):
    try:
        return spreadsheet.worksheet(USERS_SHEET_NAME)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(
            title=USERS_SHEET_NAME, rows=500, cols=3
        )
        ws.append_row(["Email", "PasswordHash", "RegistrationNo"])
        return ws


def find_user_by_email(email: str) -> dict | None:
    email = email.strip().lower()
    spreadsheet = get_spreadsheet()
    ws = _get_or_create_users_sheet(spreadsheet)
    records = ws.get_all_records()

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

    password_hash = _hash_password(password)

    spreadsheet = get_spreadsheet()
    ws = _get_or_create_users_sheet(spreadsheet)
    ws.append_row([email, password_hash, reg_no])


# ── Attendance helpers ────────────────────────────────────────────────────────

def _parse_status(raw: str) -> tuple[str, str, str]:
    v = (raw or "").strip().upper()
    if v == "2P": return "🟢", "Present", "present"
    if v == "2A": return "🔴", "Absent",  "absent"
    if v == "L":  return "🟡", "Leave",   "leave"
    return "⬜", "—", "unknown"


def fetch_attendance(reg_no: str) -> dict | None:
    reg_no = reg_no.strip().upper()
    spreadsheet = get_spreadsheet()

    for ws in spreadsheet.worksheets():
        if ws.title == USERS_SHEET_NAME:
            continue

        rows = ws.get_all_values()
        if len(rows) < 2:
            continue

        header = rows[0]

        week_indices = [
            i for i, h in enumerate(header)
            if h.strip().lower().startswith("week")
        ]
        week_labels = [header[i].strip() for i in week_indices]

        att_col = next(
            (i for i, h in enumerate(header) if "attendance" in h.lower()),
            None,
        )

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
                row[att_col].strip()
                if att_col is not None and att_col < len(row)
                else "N/A"
            )

            return {
                "name":            (row[2] if len(row) > 2 else "").strip(),
                "registration_no": row_reg,
                "weeks":           weeks,
                "attendance_pct":  att_pct,
                "sheet_name":      ws.title,
            }

    return None
