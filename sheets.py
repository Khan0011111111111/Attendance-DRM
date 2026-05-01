import hashlib
import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

USERS_SHEET_NAME = "Users"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

@st.cache_resource(show_spinner=False)
def get_client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES)
    return gspread.authorize(creds)

def get_spreadsheet():
    return get_client().open_by_key(st.secrets["GOOGLE_SHEET_ID"])

def _hash_password(password: str, salt: str = None) -> str:
    if salt is None:
        salt = os.urandom(32).hex()
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations=260000).hex()
    return f"{salt}${key}"

def verify_password(plain: str, stored: str) -> bool:
    try:
        salt, _ = stored.split("$")
        return _hash_password(plain, salt) == stored
    except Exception:
        return False

def send_verification_email(to_email: str, code: str):
    from_email = st.secrets["EMAIL_USER"]
    app_password = st.secrets["EMAIL_APP_PASSWORD"]
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your Attendance Portal Verification Code"
    msg["From"] = from_email
    msg["To"] = to_email
    html_body = f"""
    <html><body style="font-family:Arial,sans-serif;background:#f5f0e8;padding:2rem;">
      <div style="max-width:480px;margin:0 auto;background:white;border-radius:12px;
                  padding:2rem;border-top:4px solid #c9a84c;">
        <h2 style="color:#0d1b2a;">🎓 Attendance Portal</h2>
        <p style="color:#5a6478;">Your verification code is:</p>
        <div style="background:#0d1b2a;border-radius:10px;padding:1.25rem;text-align:center;">
          <span style="font-size:2.2rem;font-weight:700;letter-spacing:0.3em;color:#c9a84c;">{code}</span>
        </div>
        <p style="color:#aaa;font-size:0.8rem;margin-top:1rem;">Expires in 10 minutes. If you didn't request this, ignore it.</p>
      </div>
    </body></html>"""
    msg.attach(MIMEText(html_body, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(from_email, app_password)
        server.sendmail(from_email, to_email, msg.as_string())

def _get_or_create_users_sheet(spreadsheet):
    try:
        ws = spreadsheet.worksheet(USERS_SHEET_NAME)
        headers = ws.row_values(1)
        if len(headers) < 5:
            ws.resize(rows=ws.row_count, cols=5)
            if len(headers) < 4:
                ws.update_cell(1, 4, "Verified")
            if len(headers) < 5:
                ws.update_cell(1, 5, "VerifyCode")
        return ws
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=USERS_SHEET_NAME, rows=500, cols=5)
        ws.append_row(["Email", "PasswordHash", "RegistrationNo", "Verified", "VerifyCode"])
        return ws

def find_user_by_email(email: str):
    email = email.strip().lower()
    spreadsheet = get_spreadsheet()
    ws = _get_or_create_users_sheet(spreadsheet)
    records = ws.get_all_records()
    for row in records:
        if row.get("Email", "").strip().lower() == email:
            return {
                "email": row.get("Email", ""),
                "password_hash": row.get("PasswordHash", ""),
                "registration_no": row.get("RegistrationNo", ""),
                "verified": str(row.get("Verified", "")).strip().upper() == "TRUE",
                "verify_code": str(row.get("VerifyCode", "")).strip(),
            }
    return None

def email_exists(email: str) -> bool:
    return find_user_by_email(email) is not None

def reg_no_exists(reg_no: str) -> bool:
    reg_no = reg_no.strip().upper()
    spreadsheet = get_spreadsheet()
    ws = _get_or_create_users_sheet(spreadsheet)
    for row in ws.get_all_records():
        if row.get("RegistrationNo", "").strip().upper() == reg_no:
            return True
    return False

def _find_user_row(ws, email: str):
    email = email.strip().lower()
    for i, row in enumerate(ws.get_all_values()[1:], start=2):
        if (row[0] if row else "").strip().lower() == email:
            return i
    return None

def create_user(email: str, password: str, reg_no: str) -> str:
    email = email.strip().lower()
    reg_no = reg_no.strip().upper()
    if email_exists(email):
        raise ValueError("This email is already registered.")
    if reg_no_exists(reg_no):
        raise ValueError("This registration number is already registered.")
    password_hash = _hash_password(password)
    code = str(random.randint(100000, 999999))
    spreadsheet = get_spreadsheet()
    ws = _get_or_create_users_sheet(spreadsheet)
    ws.append_row([email, password_hash, reg_no, "FALSE", code])
    return code

def verify_user_code(email: str, code: str) -> bool:
    email = email.strip().lower()
    spreadsheet = get_spreadsheet()
    ws = _get_or_create_users_sheet(spreadsheet)
    row_idx = _find_user_row(ws, email)
    if row_idx is None:
        return False
    row = ws.row_values(row_idx)
    stored_code = (row[4] if len(row) > 4 else "").strip()
    if stored_code != code.strip():
        return False
    ws.update_cell(row_idx, 4, "TRUE")
    ws.update_cell(row_idx, 5, "")
    return True

def resend_verification_code(email: str) -> str:
    email = email.strip().lower()
    spreadsheet = get_spreadsheet()
    ws = _get_or_create_users_sheet(spreadsheet)
    row_idx = _find_user_row(ws, email)
    if row_idx is None:
        raise ValueError("Email not found.")
    code = str(random.randint(100000, 999999))
    ws.update_cell(row_idx, 5, code)
    return code

def _parse_status(raw: str):
    v = (raw or "").strip().upper()
    if v == "2P": return "🟢", "Present", "present"
    if v == "2A": return "🔴", "Absent", "absent"
    if v == "L": return "🟡", "Leave", "leave"
    return "⬜", "—", "unknown"

def fetch_attendance(reg_no: str):
    reg_no = reg_no.strip().upper()
    spreadsheet = get_spreadsheet()
    for ws in spreadsheet.worksheets():
        if ws.title == USERS_SHEET_NAME:
            continue
        rows = ws.get_all_values()
        if len(rows) < 2:
            continue
        header = rows[0]
        week_indices = [i for i, h in enumerate(header) if h.strip().lower().startswith("week")]
        week_labels = [header[i].strip() for i in week_indices]
        att_col = next((i for i, h in enumerate(header) if "attendance" in h.lower()), None)
        for row in rows[1:]:
            row_reg = (row[1] if len(row) > 1 else "").strip().upper()
            if row_reg != reg_no:
                continue
            weeks = []
            for idx, label in zip(week_indices, week_labels):
                raw = row[idx].strip() if idx < len(row) else ""
                emoji, status, css = _parse_status(raw)
                weeks.append({"label": label, "raw": raw, "emoji": emoji, "status": status, "css": css})
            att_pct = row[att_col].strip() if att_col is not None and att_col < len(row) else "N/A"
            return {
                "name": (row[2] if len(row) > 2 else "").strip(),
                "registration_no": row_reg,
                "weeks": weeks,
                "attendance_pct": att_pct,
                "sheet_name": ws.title,
            }
    return None
