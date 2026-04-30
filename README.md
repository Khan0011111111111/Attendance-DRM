# 🎓 Student Attendance Viewer — Streamlit Edition

A free, zero-infrastructure student attendance portal built with Python + Streamlit.  
**No server, no database, no credit card.** Deploys in minutes on Streamlit Community Cloud.

---

## How it works

- **User accounts** are stored in a "Users" tab in your Google Spreadsheet (auto-created on first signup), with bcrypt-hashed passwords.
- **Attendance data** is fetched live from your other sheet tabs (e.g. "U", "P") every time a student opens their dashboard.
- **Hosting** is free on [Streamlit Community Cloud](https://streamlit.io/cloud).

---

## Spreadsheet setup

Your spreadsheet needs one or more attendance sheets with this layout:

| Class No. | Registration No | Student Name | Week 01 | Week 02 | … | Week 14 | Attendance (%) |
|---|---|---|---|---|---|---|---|
| 1 | 22PWCIV5790 | Ali Hassan | 2P | 2A | … | L | 85% |

- `2P` = Present &nbsp; `2A` = Absent &nbsp; `L` = Leave
- The first row must be the header row.
- You can have multiple tabs — the app searches all of them.
- A **"Users"** tab will be created automatically when the first student signs up. Do not delete it.

---

## Setup steps

### 1. Enable Google Sheets API & create a service account

1. Go to [Google Cloud Console](https://console.cloud.google.com) → create/select a project.
2. **APIs & Services → Library** → search **Google Sheets API** → Enable.
3. **APIs & Services → Credentials → Create Credentials → Service Account**.
4. Give it a name (e.g. `attendance-reader`) → Done.
5. Click the account → **Keys → Add Key → JSON** → download the file.

### 2. Share the spreadsheet

1. Open your Google Spreadsheet → **Share**.
2. Paste the service account email (from the JSON key, looks like `name@project.iam.gserviceaccount.com`).
3. Give it **Editor** access (needed to create the Users tab on first signup).

### 3. Configure secrets (local development)

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Open `.streamlit/secrets.toml` and fill in:
- `GOOGLE_SHEET_ID` — from your sheet URL
- `[gcp_service_account]` — copy values from the downloaded JSON key file

### 4. Install dependencies & run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

App opens at `http://localhost:8501`.

---

## Deploy to Streamlit Community Cloud (free)

1. **Push this folder to a GitHub repository** (public or private).
2. Go to [share.streamlit.io](https://share.streamlit.io) → Sign in with GitHub → **New app**.
3. Select your repo, branch, and set **Main file path** to `app.py`.
4. Click **Advanced settings → Secrets** and paste the contents of your `secrets.toml` file.
5. Click **Deploy** — your app gets a free public URL instantly.

> **Important:** Never commit `.streamlit/secrets.toml` — it's in `.gitignore`. Always paste secrets through the Streamlit Cloud dashboard.

---

## File structure

```
attendance-streamlit/
├── app.py                          # Main Streamlit app (UI + routing)
├── sheets.py                       # Google Sheets logic (auth + attendance)
├── requirements.txt
├── .gitignore
└── .streamlit/
    └── secrets.toml.example        # Template — copy to secrets.toml locally
```

---

## Security

| Concern | How it's handled |
|---|---|
| Passwords | bcrypt-hashed with 12 rounds, stored in Google Sheets |
| Data isolation | Attendance fetched using reg. number from the session, never from user input |
| Secrets | Stored in Streamlit secrets (never in code or git) |
| Other students' data | Impossible to access — the server looks up reg. number from the authenticated session |

---

## Troubleshooting

**"Worksheet not found" or "Users sheet missing"**  
The Users sheet is auto-created on first signup. Make sure the service account has Editor (not just Viewer) access.

**"Registration number not found"**  
Check that the reg. number entered at signup exactly matches what's in the sheet (case-insensitive, no extra spaces).

**App is slow on first load**  
Streamlit Community Cloud free apps spin down after inactivity. The first visit after a period of inactivity takes ~10–15 seconds to wake up. Subsequent visits are instant.
