# app.py — Student Attendance Viewer (Streamlit)

import streamlit as st
from sheets import (
    find_user_by_email,
    create_user,
    verify_password,
    fetch_attendance,
    verify_user_code,
    resend_verification_code,
    send_verification_email,
)

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Attendance Portal",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
  --navy:  #0d1b2a;
  --gold:  #c9a84c;
  --cream: #f5f0e8;
  --green: #1e8449;
  --red:   #c0392b;
  --amber: #d68910;
  --muted: #5a6478;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem !important; max-width: 780px !important; }

.auth-wrap {
  background: white;
  border-radius: 16px;
  padding: 2.5rem 2rem 1.5rem;
  box-shadow: 0 8px 40px rgba(13,27,42,0.13);
  border-top: 3px solid var(--gold);
  margin-bottom: 1rem;
  text-align: center;
}
.portal-title {
  font-family: 'Playfair Display', serif;
  font-size: 1.7rem;
  color: var(--navy);
  margin: 0 0 0.15rem;
}
.portal-sub {
  font-size: 0.8rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 0;
}

/* Student card */
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
.student-card p { font-size:0.8rem; color:rgba(255,255,255,0.5); margin:0; text-transform:uppercase; letter-spacing:0.05em; }

/* Stats row */
.stats-row { display:grid; grid-template-columns:repeat(4,1fr); gap:0.75rem; margin-bottom:1.4rem; }
.stat-box { background:white; border-radius:10px; padding:0.9rem 0.75rem; text-align:center; box-shadow:0 2px 12px rgba(0,0,0,0.07); border:1px solid #eee; }
.stat-box .val { font-family:'Playfair Display',serif; font-size:1.6rem; font-weight:700; line-height:1; color:var(--navy); }
.stat-box .lbl { font-size:0.7rem; color:var(--muted); text-transform:uppercase; letter-spacing:0.05em; margin-top:0.2rem; }
.val-good { color:var(--green) !important; }
.val-warn { color:var(--amber) !important; }
.val-bad  { color:var(--red)   !important; }

/* Attendance table */
.att-wrap { background:white; border-radius:12px; overflow:hidden; box-shadow:0 2px 12px rgba(0,0,0,0.07); margin-bottom:1rem; }
.att-wrap table { width:100%; border-collapse:collapse; font-size:0.88rem; }
.att-wrap thead tr { background:var(--navy); }
.att-wrap thead th { color:var(--gold); padding:0.75rem 1rem; text-align:left; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.07em; font-weight:600; }
.att-wrap tbody tr { border-bottom:1px solid #f0ebe0; }
.att-wrap tbody tr:last-child { border-bottom:none; }
.att-wrap tbody tr:hover { background:#faf7f2; }
.att-wrap tbody td { padding:0.65rem 1rem; vertical-align:middle; }
.week-col { color:var(--muted); font-size:0.8rem; text-transform:uppercase; letter-spacing:0.04em; font-weight:500; }

/* Pills */
.pill { display:inline-block; padding:0.28rem 0.8rem; border-radius:20px; font-size:0.78rem; font-weight:600; }
.pill-present { background:rgba(30,132,73,0.1);  color:var(--green); border:1px solid rgba(30,132,73,0.2); }
.pill-absent  { background:rgba(192,57,43,0.08); color:var(--red);   border:1px solid rgba(192,57,43,0.2); }
.pill-leave   { background:rgba(214,137,16,0.1); color:var(--amber); border:1px solid rgba(214,137,16,0.2); }
.pill-unknown { background:#f5f5f5; color:#bbb; border:1px solid #eee; }

.code-col { font-family:monospace; font-size:0.8rem; color:#aaa; }

/* Topnav */
.topnav { display:flex; align-items:center; justify-content:space-between; background:var(--navy); padding:0.75rem 1.25rem; border-radius:10px; margin-bottom:1.5rem; }
.topnav-brand { font-family:'Playfair Display',serif; color:white; font-size:1rem; }
.topnav-email { font-size:0.78rem; color:rgba(255,255,255,0.5); }

.updated { text-align:right; font-size:0.72rem; color:#bbb; margin-top:0.4rem; }

/* Verification code box */
.verify-box {
  background: #f8f6f0;
  border: 2px dashed var(--gold);
  border-radius: 12px;
  padding: 1.25rem;
  text-align: center;
  margin: 1rem 0;
  font-size: 0.88rem;
  color: var(--muted);
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────

defaults = {
    "logged_in":       False,
    "user":            None,
    "page":            "login",
    "auth_msg":        ("", ""),
    "pending_email":   "",   # email waiting for verification
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def set_msg(text, kind="error"):
    st.session_state.auth_msg = (text, kind)


def show_msg():
    msg, kind = st.session_state.auth_msg
    if msg:
        if kind == "success": st.success(msg)
        else:                 st.error(msg)
        st.session_state.auth_msg = ("", "")


# ── Login page ────────────────────────────────────────────────────────────────

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

        # Check if verified
        if not user["verified"]:
            st.session_state.pending_email = user["email"]
            set_msg("Please verify your email first. Resending code…", "success")
            with st.spinner("Sending verification code…"):
                try:
                    code = resend_verification_code(user["email"])
                    send_verification_email(user["email"], code)
                except Exception as e:
                    set_msg(f"Could not send verification email: {e}")
            st.session_state.page = "verify"
            st.rerun()

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


# ── Sign-up page ──────────────────────────────────────────────────────────────

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
        if not all([email, reg_no, password, confirm]):
            set_msg("All fields are required.")
            st.rerun()
        if len(password) < 6:
            set_msg("Password must be at least 6 characters.")
            st.rerun()
        if password != confirm:
            set_msg("Passwords do not match.")
            st.rerun()

        with st.spinner("Creating account and sending verification email…"):
            try:
                code = create_user(email, password, reg_no)
                send_verification_email(email.strip().lower(), code)
                st.session_state.pending_email = email.strip().lower()
                set_msg("Account created! Check your email for the verification code.", "success")
                st.session_state.page = "verify"
                st.rerun()
            except ValueError as e:
                set_msg(str(e))
                st.rerun()
            except Exception as e:
                set_msg(f"Error sending verification email: {e}")
                st.rerun()

    st.markdown("---")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.caption("Already have an account?")
    with col2:
        if st.button("← Sign In", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()


# ── Verification page ─────────────────────────────────────────────────────────

def page_verify():
    email = st.session_state.pending_email

    st.markdown("""
    <div class="auth-wrap">
      <p class="portal-title">📧 Verify Your Email</p>
      <p class="portal-sub">Enter the 6-digit code sent to your inbox</p>
    </div>
    """, unsafe_allow_html=True)

    show_msg()

    st.markdown(f"""
    <div class="verify-box">
      A verification code has been sent to<br>
      <strong>{email}</strong><br>
      Check your inbox (and spam folder).
    </div>
    """, unsafe_allow_html=True)

    with st.form("verify_form"):
        code = st.text_input("6-Digit Code", placeholder="123456", max_chars=6)
        submitted = st.form_submit_button("Verify Account", use_container_width=True)

    if submitted:
        if not code or len(code.strip()) != 6:
            set_msg("Please enter the 6-digit code.")
            st.rerun()

        with st.spinner("Verifying…"):
            success = verify_user_code(email, code.strip())

        if success:
            set_msg("Email verified! You can now log in.", "success")
            st.session_state.page = "login"
            st.session_state.pending_email = ""
            st.rerun()
        else:
            set_msg("Incorrect code. Please try again.")
            st.rerun()

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Resend Code", use_container_width=True):
            with st.spinner("Sending new code…"):
                try:
                    code = resend_verification_code(email)
                    send_verification_email(email, code)
                    set_msg("New code sent! Check your email.", "success")
                except Exception as e:
                    set_msg(f"Could not resend: {e}")
            st.rerun()
    with col2:
        if st.button("← Back to Login", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()


# ── Dashboard ─────────────────────────────────────────────────────────────────

def page_dashboard():
    user = st.session_state.user

    # Topnav
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

    # Fetch live data
    with st.spinner("Fetching your attendance…"):
        data = fetch_attendance(user["registration_no"])

    if data is None:
        st.error(
            f"Registration number **{user['registration_no']}** was not found "
            "in any attendance sheet. Contact your administrator."
        )
        return

    # Student card
    initial = data["name"][0].upper() if data["name"] else "?"
    st.markdown(f"""
    <div class="student-card">
      <h2>{initial} &nbsp; {data['name']}</h2>
      <p>{data['registration_no']} &nbsp;·&nbsp; Class: {data['sheet_name']}</p>
    </div>
    """, unsafe_allow_html=True)

    # Stats
    weeks   = data["weeks"]
    present = sum(1 for w in weeks if w["css"] == "present")
    absent  = sum(1 for w in weeks if w["css"] == "absent")
    leave   = sum(1 for w in weeks if w["css"] == "leave")
    pct_raw = data["attendance_pct"]

    try:
        pct_num = float(str(pct_raw).replace("%", "").strip())
        pct_cls = "val-good" if pct_num >= 85 else ("val-warn" if pct_num >= 75 else "val-bad")
    except ValueError:
        pct_cls = ""

    st.markdown(f"""
    <div class="stats-row">
      <div class="stat-box"><div class="val {pct_cls}">{pct_raw}</div><div class="lbl">📊 Attendance</div></div>
      <div class="stat-box"><div class="val val-good">{present}</div><div class="lbl">🟢 Present</div></div>
      <div class="stat-box"><div class="val val-bad">{absent}</div><div class="lbl">🔴 Absent</div></div>
      <div class="stat-box"><div class="val val-warn">{leave}</div><div class="lbl">🟡 Leave</div></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Attendance table ──────────────────────────────────────────────────────
    st.markdown("### 📋 Weekly Attendance Record")

    if not weeks:
        st.info("No weekly data found in the sheet.")
    else:
        # Build table rows as a string
        rows_html = ""
        for w in weeks:
            rows_html += (
                f'<tr>'
                f'<td class="week-col">{w["label"]}</td>'
                f'<td><span class="pill pill-{w["css"]}">{w["emoji"]} {w["status"]}</span></td>'
                f'<td class="code-col">{w["raw"] or "—"}</td>'
                f'</tr>'
            )

        # Render as a proper HTML table
        table_html = f"""
<div class="att-wrap">
  <table>
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
</div>
"""
        st.markdown(table_html, unsafe_allow_html=True)

    from datetime import datetime
    now = datetime.now().strftime("%d %b %Y, %I:%M %p")
    st.markdown(f'<p class="updated">Last fetched: {now}</p>', unsafe_allow_html=True)

    if st.button("🔄 Refresh Attendance"):
        st.rerun()


# ── Router ────────────────────────────────────────────────────────────────────

if st.session_state.logged_in:
    page_dashboard()
elif st.session_state.page == "signup":
    page_signup()
elif st.session_state.page == "verify":
    page_verify()
else:
    page_login()
