# app.py — Student Attendance Viewer (Streamlit)
# Run with: streamlit run app.py

import streamlit as st
from sheets import (
    find_user_by_email,
    create_user,
    verify_password,
    fetch_attendance,
)

# ── Page config (must be first Streamlit call) ────────────────────────────────

st.set_page_config(
    page_title="Attendance Portal",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* ── Import fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Root variables ── */
:root {
  --navy:      #0d1b2a;
  --gold:      #c9a84c;
  --cream:     #f5f0e8;
  --green:     #1e8449;
  --red:       #c0392b;
  --amber:     #d68910;
  --muted:     #5a6478;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem !important; max-width: 780px !important; }

/* ── Auth card wrapper ── */
.auth-wrap {
  background: white;
  border-radius: 16px;
  padding: 2.5rem 2rem;
  box-shadow: 0 8px 40px rgba(13,27,42,0.13);
  border-top: 3px solid var(--gold);
  margin-bottom: 1rem;
}

/* ── Headings ── */
.portal-title {
  font-family: 'Playfair Display', serif;
  font-size: 1.7rem;
  color: var(--navy);
  margin: 0 0 0.15rem;
  text-align: center;
}
.portal-sub {
  font-size: 0.8rem;
  color: var(--muted);
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 1.5rem;
}

/* ── Student card ── */
.student-card {
  background: var(--navy);
  border-radius: 12px;
  padding: 1.4rem 1.6rem;
  color: white;
  margin-bottom: 1.2rem;
  border-left: 4px solid var(--gold);
}
.student-card h2 {
  font-family: 'Playfair Display', serif;
  font-size: 1.4rem;
  margin: 0 0 0.2rem;
  color: white;
}
.student-card p {
  font-size: 0.8rem;
  color: rgba(255,255,255,0.5);
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* ── Stat cards row ── */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
  margin-bottom: 1.4rem;
}
.stat-box {
  background: white;
  border-radius: 10px;
  padding: 0.9rem 0.75rem;
  text-align: center;
  box-shadow: 0 2px 12px rgba(0,0,0,0.07);
  border: 1px solid #eee;
}
.stat-box .val {
  font-family: 'Playfair Display', serif;
  font-size: 1.6rem;
  font-weight: 700;
  line-height: 1;
  color: var(--navy);
}
.stat-box .lbl {
  font-size: 0.7rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-top: 0.2rem;
}
.val-good { color: var(--green) !important; }
.val-warn { color: var(--amber) !important; }
.val-bad  { color: var(--red)   !important; }

/* ── Table ── */
.att-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0,0,0,0.07);
}
.att-table thead tr { background: var(--navy); }
.att-table thead th {
  color: var(--gold);
  padding: 0.7rem 1rem;
  text-align: left;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  font-weight: 600;
}
.att-table tbody tr { border-bottom: 1px solid #f0ebe0; }
.att-table tbody tr:last-child { border-bottom: none; }
.att-table tbody tr:hover { background: #faf7f2; }
.att-table tbody td { padding: 0.65rem 1rem; vertical-align: middle; }
.att-table .week-col { color: var(--muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em; }

/* ── Status pills ── */
.pill {
  display: inline-block;
  padding: 0.28rem 0.8rem;
  border-radius: 20px;
  font-size: 0.78rem;
  font-weight: 600;
}
.pill-present { background: rgba(30,132,73,0.1);  color: var(--green); border: 1px solid rgba(30,132,73,0.2); }
.pill-absent  { background: rgba(192,57,43,0.08); color: var(--red);   border: 1px solid rgba(192,57,43,0.2); }
.pill-leave   { background: rgba(214,137,16,0.1); color: var(--amber); border: 1px solid rgba(214,137,16,0.2); }
.pill-unknown { background: #f5f5f5; color: #bbb; border: 1px solid #eee; }

/* ── Section header ── */
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}
.section-head h3 {
  font-family: 'Playfair Display', serif;
  font-size: 1rem;
  color: var(--navy);
  margin: 0;
}
.badge {
  font-size: 0.72rem;
  padding: 0.2rem 0.6rem;
  background: #f5f0e8;
  border: 1px solid rgba(201,168,76,0.3);
  border-radius: 20px;
  color: var(--muted);
}

/* ── Updated notice ── */
.updated {
  text-align: right;
  font-size: 0.72rem;
  color: #bbb;
  margin-top: 0.5rem;
}

/* ── Top nav ── */
.topnav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--navy);
  padding: 0.75rem 1.25rem;
  border-radius: 10px;
  margin-bottom: 1.5rem;
}
.topnav-brand {
  font-family: 'Playfair Display', serif;
  color: white;
  font-size: 1rem;
}
.topnav-email {
  font-size: 0.78rem;
  color: rgba(255,255,255,0.5);
}
</style>
""", unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────────

if "logged_in"   not in st.session_state: st.session_state.logged_in   = False
if "user"        not in st.session_state: st.session_state.user        = None
if "page"        not in st.session_state: st.session_state.page        = "login"
if "auth_msg"    not in st.session_state: st.session_state.auth_msg    = ("", "")


# ── Helper: show a coloured message ──────────────────────────────────────────

def set_msg(text, kind="error"):
    """kind: 'error' | 'success'"""
    st.session_state.auth_msg = (text, kind)


def show_msg():
    msg, kind = st.session_state.auth_msg
    if msg:
        if kind == "success":
            st.success(msg)
        else:
            st.error(msg)
        st.session_state.auth_msg = ("", "")


# ── Pages ─────────────────────────────────────────────────────────────────────

def page_login():
    st.markdown("""
    <div class="auth-wrap">
      <p class="portal-title">🎓 Attendance Portal</p>
      <p class="portal-sub">Student Login</p>
    </div>
    """, unsafe_allow_html=True)

    show_msg()

    with st.form("login_form"):
        email    = st.text_input("Email Address", placeholder="you@university.edu")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Sign In", use_container_width=True)

    if submitted:
        if not email or not password:
            set_msg("Please enter your email and password.")
            st.rerun()

        with st.spinner("Checking credentials…"):
            user = find_user_by_email(email)

        if user is None or not verify_password(password, user["password_hash"]):
            set_msg("Invalid email or password.")
            st.rerun()

        # Success — store user in session
        st.session_state.logged_in = True
        st.session_state.user      = user
        st.session_state.page      = "dashboard"
        st.rerun()

    st.markdown("---")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.caption("Don't have an account?")
    with col2:
        if st.button("Sign Up →", use_container_width=True):
            st.session_state.page = "signup"
            st.rerun()


def page_signup():
    st.markdown("""
    <div class="auth-wrap">
      <p class="portal-title">🎓 Attendance Portal</p>
      <p class="portal-sub">Create Student Account</p>
    </div>
    """, unsafe_allow_html=True)

    show_msg()

    with st.form("signup_form"):
        email    = st.text_input("Email Address", placeholder="you@university.edu")
        reg_no   = st.text_input("Registration Number", placeholder="e.g. 22PWCIV5790")
        password = st.text_input("Password (min 6 chars)", type="password")
        confirm  = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button("Create Account", use_container_width=True)

    if submitted:
        # Validate fields
        if not all([email, reg_no, password, confirm]):
            set_msg("All fields are required.")
            st.rerun()
        if len(password) < 6:
            set_msg("Password must be at least 6 characters.")
            st.rerun()
        if password != confirm:
            set_msg("Passwords do not match.")
            st.rerun()

        with st.spinner("Creating your account…"):
            try:
                create_user(email, password, reg_no)
                set_msg("Account created! Please log in.", "success")
                st.session_state.page = "login"
                st.rerun()
            except ValueError as e:
                set_msg(str(e))
                st.rerun()

    st.markdown("---")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.caption("Already have an account?")
    with col2:
        if st.button("← Sign In", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()


def page_dashboard():
    user = st.session_state.user

    # ── Top nav ──────────────────────────────────────────────────────────────
    col_brand, col_logout = st.columns([4, 1])
    with col_brand:
        st.markdown(f"""
        <div class="topnav">
          <span class="topnav-brand">🎓 Attendance Portal</span>
          <span class="topnav-email">{user['email']}</span>
        </div>
        """, unsafe_allow_html=True)
    with col_logout:
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user      = None
            st.session_state.page      = "login"
            st.rerun()

    # ── Fetch live attendance data ────────────────────────────────────────────
    with st.spinner("Fetching your attendance from the register…"):
        data = fetch_attendance(user["registration_no"])

    if data is None:
        st.error(
            f"Your registration number **{user['registration_no']}** was not found "
            "in any attendance sheet. Please contact your administrator."
        )
        return

    # ── Student card ──────────────────────────────────────────────────────────
    initial = data["name"][0].upper() if data["name"] else "?"
    st.markdown(f"""
    <div class="student-card">
      <h2>{initial} &nbsp; {data['name']}</h2>
      <p>{data['registration_no']} &nbsp;·&nbsp; Sheet: {data['sheet_name']}</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Stats ─────────────────────────────────────────────────────────────────
    weeks   = data["weeks"]
    present = sum(1 for w in weeks if w["css"] == "present")
    absent  = sum(1 for w in weeks if w["css"] == "absent")
    leave   = sum(1 for w in weeks if w["css"] == "leave")
    pct_raw = data["attendance_pct"]

    # Colour the percentage
    try:
        pct_num = float(str(pct_raw).replace("%", "").strip())
        pct_cls = "val-good" if pct_num >= 85 else ("val-warn" if pct_num >= 75 else "val-bad")
    except ValueError:
        pct_cls = ""

    st.markdown(f"""
    <div class="stats-row">
      <div class="stat-box">
        <div class="val {pct_cls}">{pct_raw}</div>
        <div class="lbl">📊 Attendance</div>
      </div>
      <div class="stat-box">
        <div class="val val-good">{present}</div>
        <div class="lbl">🟢 Present</div>
      </div>
      <div class="stat-box">
        <div class="val val-bad">{absent}</div>
        <div class="lbl">🔴 Absent</div>
      </div>
      <div class="stat-box">
        <div class="val val-warn">{leave}</div>
        <div class="lbl">🟡 Leave</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Weekly table ──────────────────────────────────────────────────────────
    st.markdown("""
    <div class="section-head">
      <h3>Weekly Attendance Record</h3>
    </div>
    """, unsafe_allow_html=True)

    if not weeks:
        st.info("No weekly data found in the sheet.")
    else:
        rows_html = ""
        for w in weeks:
            pill_cls = f"pill-{w['css']}"
            rows_html += f"""
            <tr>
              <td class="week-col">{w['label']}</td>
              <td><span class="pill {pill_cls}">{w['emoji']} {w['status']}</span></td>
              <td style="font-family:monospace;font-size:0.8rem;color:#aaa;">{w['raw'] or '—'}</td>
            </tr>"""

        st.markdown(f"""
        <table class="att-table">
          <thead>
            <tr>
              <th>Week</th>
              <th>Status</th>
              <th>Code</th>
            </tr>
          </thead>
          <tbody>
            {rows_html}
          </tbody>
        </table>
        """, unsafe_allow_html=True)

    # ── Last updated notice ───────────────────────────────────────────────────
    from datetime import datetime
    now = datetime.now().strftime("%d %b %Y, %I:%M %p")
    st.markdown(f'<p class="updated">Last fetched: {now}</p>', unsafe_allow_html=True)

    # Refresh button
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Refresh Attendance", use_container_width=False):
        st.rerun()


# ── Router ────────────────────────────────────────────────────────────────────

if st.session_state.logged_in:
    page_dashboard()
elif st.session_state.page == "signup":
    page_signup()
else:
    page_login()
