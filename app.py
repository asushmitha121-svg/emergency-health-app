import streamlit as st
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import face6 as f6


st.set_page_config(
    page_title="Emergency Medical System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

[data-testid="stAppViewContainer"] {
    background: #0a0f1a;
    color: #e0e8f0;
}
[data-testid="stSidebar"] {
    background: #0d1525 !important;
    border-right: 1px solid #1e3050;
}
[data-testid="stSidebar"] * {
    color: #c8d8e8 !important;
}

h1, h2, h3 {
    font-family: 'IBM Plex Mono', monospace;
    color: #4fc3f7 !important;
    letter-spacing: -0.5px;
}

.card {
    background: #0d1525;
    border: 1px solid #1e3050;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}
.card-title {
    font-family: 'IBM Plex Mono', monospace;
    color: #4fc3f7;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 1rem;
    border-bottom: 1px solid #1e3050;
    padding-bottom: 0.5rem;
}

.data-row {
    display: flex;
    justify-content: space-between;
    padding: 0.4rem 0;
    border-bottom: 1px solid #111d2e;
    font-size: 0.9rem;
}
.data-label {
    color: #607d9a;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
}
.data-value {
    color: #e0e8f0;
    text-align: right;
}

.badge-email { background: #0d3349; color: #4fc3f7; padding: 2px 10px; border-radius: 4px; font-family: monospace; font-size: 0.82rem; }
.badge-uuid  { background: #1a2a1a; color: #66bb6a; padding: 2px 10px; border-radius: 4px; font-family: monospace; font-size: 0.72rem; }

.section-header {
    font-family: 'IBM Plex Mono', monospace;
    color: #607d9a;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin: 1.2rem 0 0.5rem;
}

.alert-success { background:#0a2a0a; border-left:3px solid #66bb6a; padding:0.8rem 1rem; border-radius:4px; color:#a5d6a7; margin:0.5rem 0; }
.alert-error   { background:#2a0a0a; border-left:3px solid #ef5350; padding:0.8rem 1rem; border-radius:4px; color:#ef9a9a; margin:0.5rem 0; }
.alert-info    { background:#0a1a2a; border-left:3px solid #4fc3f7; padding:0.8rem 1rem; border-radius:4px; color:#81d4fa; margin:0.5rem 0; }
.alert-warn    { background:#2a1a0a; border-left:3px solid #ffa726; padding:0.8rem 1rem; border-radius:4px; color:#ffcc80; margin:0.5rem 0; }

.stButton > button {
    background: #0d3349 !important;
    color: #4fc3f7 !important;
    border: 1px solid #1e5070 !important;
    border-radius: 4px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.5px !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: #1e5070 !important;
    border-color: #4fc3f7 !important;
}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {
    background: #0d1525 !important;
    border: 1px solid #1e3050 !important;
    color: #e0e8f0 !important;
    border-radius: 4px !important;
}

.stRadio > div { gap: 0.4rem; }
.stRadio label { color: #c8d8e8 !important; }

hr { border-color: #1e3050 !important; }

.streamlit-expanderHeader {
    background: #0d1525 !important;
    color: #4fc3f7 !important;
    border: 1px solid #1e3050 !important;
}

.stDataFrame { border: 1px solid #1e3050 !important; }

/* Interaction table */
.interaction-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'IBM Plex Sans', sans-serif;
}
.interaction-table thead tr {
    background: #0a1a2e;
}
.interaction-table thead th {
    padding: 10px 14px;
    text-align: left;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    color: #4fc3f7;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    border-bottom: 2px solid #1e3050;
}
.interaction-table tbody tr:hover {
    background: #111d2e;
}
.interaction-table tbody td {
    padding: 9px 14px;
    border-bottom: 1px solid #1e3050;
    color: #e0e8f0;
    font-size: 0.88rem;
    text-transform: capitalize;
}
.interaction-table tbody td:first-child {
    color: #4fc3f7;
    font-weight: 600;
}
.interaction-wrap {
    background: #0d1525;
    border: 1px solid #1e3050;
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 1rem;
    max-height: 420px;
    overflow-y: auto;
}
</style>
""", unsafe_allow_html=True)

defaults = {
    "logged_in": False,
    "role": None,
    "email": None,
    "page": "home",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

def alert(kind, msg):
    css = {"success": "alert-success", "error": "alert-error",
           "info": "alert-info", "warn": "alert-warn"}
    st.markdown(f'<div class="{css[kind]}">{msg}</div>', unsafe_allow_html=True)


def show_patient_card(patient_email, user_id, decrypted: dict):
    st.markdown(f"""
    <div class="card">
      <div class="card-title">Patient Record</div>
      <div class="data-row">
        <span class="data-label">EMAIL</span>
        <span class="badge-email">{patient_email}</span>
      </div>
      <div class="data-row">
        <span class="data-label">UUID</span>
        <span class="badge-uuid">{user_id}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    basic_keys = ["name", "phone", "blood_group", "emergency_contact"]
    medical_keys = [k for k in decrypted if k not in basic_keys]

    with col1:
        st.markdown('<div class="section-header">Basic Info</div>', unsafe_allow_html=True)
        for k in basic_keys:
            if k in decrypted:
                st.markdown(f"""
                <div class="data-row">
                  <span class="data-label">{k.replace('_',' ').upper()}</span>
                  <span class="data-value">{decrypted[k]}</span>
                </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-header">Medical Info</div>', unsafe_allow_html=True)
        for k in medical_keys:
            st.markdown(f"""
            <div class="data-row">
              <span class="data-label">{k.replace('_',' ').upper()}</span>
              <span class="data-value">{decrypted[k]}</span>
            </div>""", unsafe_allow_html=True)



def get_drug_interactions(medications_str: str):
    """
    Takes the patient's ongoing_medications string, splits into individual
    drug names, queries drug_interactions for each, and returns a list of
    unique (drug1, drug2) tuples.
    """
    if not medications_str or not medications_str.strip():
        return []

    import re
    raw_drugs = re.split(r'[,;/\n]+', medications_str)
    drugs = [d.strip().lower() for d in raw_drugs if d.strip()]

    if not drugs:
        return []

    interactions = []
    seen = set()

    try:
        conn = f6.connect_db()
        cur = conn.cursor()

        for drug in drugs:
            cur.execute("""
                SELECT drug1, drug2
                FROM drug_interactions
                WHERE LOWER(drug1) = %s OR LOWER(drug2) = %s
            """, (drug, drug))
            rows = cur.fetchall()

            for row in rows:
                d1 = row[0].lower().strip()
                d2 = row[1].lower().strip()
                key = tuple(sorted([d1, d2]))
                if key not in seen:
                    seen.add(key)
                    interactions.append((d1, d2))

        cur.close()
        conn.close()

    except Exception as e:
        st.error(f"Drug interaction lookup failed: {e}")

    return interactions


def show_drug_interactions(decrypted: dict):
    """
    Reads ongoing_medications from decrypted patient data,
    fetches interactions from DB, and renders a clean table.
    Only called for doctor / maintainer views.
    """
    meds = decrypted.get("ongoing_medications", "").strip()

    st.markdown("---")
    st.markdown('<div class="section-header">Drug–Drug Interactions</div>', unsafe_allow_html=True)

    if not meds or meds.lower() in ("none", "nil", "n/a", "-", ""):
        alert("info", "No ongoing medications listed — interaction check skipped.")
        return

    st.markdown(
        f'<div class="alert-info" style="margin-bottom:0.5rem;">'
        f'Checking interactions for: <b>{meds}</b></div>',
        unsafe_allow_html=True
    )

    with st.spinner("Querying drug interaction database..."):
        interactions = get_drug_interactions(meds)

    if not interactions:
        alert("success", f"No known drug–drug interactions found.")
        return

    rows_html = "".join(
        f"""<tr>
              <td>{d1.title()}</td>
              <td>{d2.title()}</td>
            </tr>"""
        for d1, d2 in interactions
    )

    table_html = f"""
    <div class="interaction-wrap">
      <table class="interaction-table">
        <thead>
          <tr>
            <th>Drug 1</th>
            <th>Drug 2</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>
    </div>
    """

    st.markdown(table_html, unsafe_allow_html=True)
    alert("warn", f"⚠️ {len(interactions)} interaction(s) found. Please review before prescribing.")


def fetch_patient_by_email(email):
    """Returns (patient_email, user_id, decrypted_dict) or None."""
    try:
        conn = f6.connect_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT user_id, encrypted_data, nonce FROM users WHERE email=%s",
            (email,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            uid, enc, nonce = row
            return email, uid, f6.decrypt_data(enc, nonce)
        return None
    except Exception as e:
        st.error(f"DB error: {e}")
        return None


def fetch_patient_by_fingerprint():
    with st.spinner("Scanning fingerprint — place finger on scanner..."):
        email = f6._fingerprint_lookup_only()
    if not email:
        return None
    return fetch_patient_by_email(email)


def fetch_patient_by_face():
    with st.spinner("Opening camera — press 'c' to capture..."):
        email = f6.find_patient_by_face()
    if not email:
        return None
    return fetch_patient_by_email(email)


def patient_lookup_widget(key_prefix="lu"):
    """
    Common 3-option lookup widget.
    Returns (patient_email, user_id, decrypted_dict) or (None, None, None).
    """
    method = st.radio(
        "Lookup Method",
        ["Email", "Face Scan", "Fingerprint Scan"],
        horizontal=True,
        key=f"{key_prefix}_method"
    )

    result = None

    if method == "Email":
        em = st.text_input("Patient Email", key=f"{key_prefix}_em")
        if st.button("Search", key=f"{key_prefix}_search"):
            if not em.strip():
                alert("error", "Email cannot be blank.")
            else:
                result = fetch_patient_by_email(em.strip())
                if not result:
                    alert("error", "Patient not found.")

    elif method == "Face Scan":
        alert("info", "Click the button — camera will open. Press **'c'** inside the camera window to capture.")
        if st.button("Start Face Scan", key=f"{key_prefix}_face"):
            result = fetch_patient_by_face()
            if not result:
                alert("error", "No matching face found.")

    else:
        alert("info", "Click the button then place your finger on the scanner.")
        if st.button("Start Fingerprint Scan", key=f"{key_prefix}_fp"):
            result = fetch_patient_by_fingerprint()
            if not result:
                alert("error", "No matching fingerprint found.")

    if result:
        return result
    return None, None, None


try:
    f6.create_table()
except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.stop()


with st.sidebar:
    st.markdown("## Smart Emergency Healthcare System")
    st.markdown("---")

    if not st.session_state.logged_in:
        st.markdown("**Select Role**")
        role_choice = st.selectbox(
            "Role", ["User", "Doctor", "Medical Maintainer"],
            label_visibility="collapsed"
        )
        role_map = {"User": "user", "Doctor": "doctor", "Medical Maintainer": "maintainer"}
        st.session_state.role = role_map[role_choice]
        auth_choice = st.radio("Action", ["Login", "Signup"], horizontal=True)
        st.session_state.page = auth_choice.lower()
    else:
        st.markdown(f"**{st.session_state.role.title()}**")
        st.markdown(
            f'<span class="badge-email">{st.session_state.email}</span>',
            unsafe_allow_html=True
        )
        st.markdown("---")

        role = st.session_state.role

        if role == "user":
            pages = ["View My Data", "Access History", "Edit History"]
        else:
            pages = [
                "Enter Patient Data", "View Patient", "Edit Patient Data",
                "Access History", "Edit History", "Data Entry History"
            ]

        for pg in pages:
            if st.button(pg, use_container_width=True, key=f"nav_{pg}"):
                if pg != "Edit Patient Data":
                    st.session_state.edit_patient_email = None
                    st.session_state.edit_patient_dec   = None
                st.session_state.page = pg

        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


if not st.session_state.logged_in:
    page = st.session_state.page
    role = st.session_state.role

    if page == "login":
        st.markdown("# Login")
        with st.form("login_form"):
            em = st.text_input("Email")
            pw = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

        if submitted:
            errors = []
            if not em.strip():
                errors.append("Email cannot be blank.")
            if not pw.strip():
                errors.append("Password cannot be blank.")
            if errors:
                for e in errors:
                    alert("error", e)
            else:
                try:
                    conn = f6.connect_db()
                    cur = conn.cursor()
                    table = {
                        "user": "user_auth",
                        "doctor": "doctor_auth",
                        "maintainer": "medical_maintainer_auth"
                    }[role]
                    cur.execute(
                        f"SELECT password,nonce FROM {table} WHERE email=%s",
                        (em.strip(),)
                    )
                    row = cur.fetchone()
                    cur.close()
                    conn.close()

                    if not row:
                        alert("error", "Account not found.")
                    else:
                        dec = f6.decrypt_data(row[0], row[1])
                        if dec["password"] == pw:
                            st.session_state.logged_in = True
                            st.session_state.email = em.strip()
                            st.session_state.page = (
                                "View My Data" if role == "user"
                                else "Enter Patient Data"
                            )
                            alert("success", "Login successful!")
                            st.rerun()
                        else:
                            alert("error", "Incorrect password.")
                except Exception as e:
                    alert("error", f"Error: {e}")

    elif page == "signup":
        st.markdown("# Signup")
        with st.form("signup_form"):
            em  = st.text_input("Email")
            pw  = st.text_input("Password", type="password")
            pw2 = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Create Account")

        if submitted:
            errors = []
            if not em.strip():
                errors.append("Email cannot be blank.")
            if not pw.strip():
                errors.append("Password cannot be blank.")
            if pw != pw2:
                errors.append("Passwords do not match.")
            if errors:
                for e in errors:
                    alert("error", e)
            else:
                try:
                    enc, nonce = f6.encrypt_data({"password": pw})
                    conn = f6.connect_db()
                    cur = conn.cursor()
                    table = {
                        "user": "user_auth",
                        "doctor": "doctor_auth",
                        "maintainer": "medical_maintainer_auth"
                    }[role]
                    cur.execute(
                        f"INSERT INTO {table} VALUES (%s,%s,%s)",
                        (em.strip(), enc, nonce)
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                    alert("success", "Account created! Please login.")
                    st.session_state.page = "login"
                    st.rerun()
                except Exception as e:
                    alert("error", f"Error: {e}")

    st.stop()


page         = st.session_state.page
role         = st.session_state.role
logged_email = st.session_state.email

if page == "View My Data":
    st.markdown("# My Medical Record")
    try:
        result = fetch_patient_by_email(logged_email)
        if result:
            em, uid, dec = result
            show_patient_card(em, uid, dec)
        else:
            alert("warn", "No medical record found for your account.")
    except Exception as e:
        alert("error", str(e))

elif page == "Enter Patient Data":
    st.markdown("# Enter Patient Data")

    with st.form("enter_form"):
        st.markdown('<div class="section-header">Patient Identity</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            em        = st.text_input("Patient Email *")
            name      = st.text_input("Full Name *")
            phone     = st.text_input("Phone *")
        with c2:
            blood_group       = st.text_input("Blood Group *")
            emergency_contact = st.text_input("Emergency Contact *")

        st.markdown('<div class="section-header">Medical Conditions</div>', unsafe_allow_html=True)
        c3, c4 = st.columns(2)
        with c3:
            asthma       = st.text_input("Asthma *")
            diabetes     = st.text_input("Diabetes *")
            heart_issues = st.text_input("Heart Issues *")
            hypertension = st.text_input("Hypertension *")
            thyroid      = st.text_input("Thyroid *")
            hiv          = st.text_input("HIV *")
        with c4:
            recent_heart_attack  = st.text_input("Recent Heart Attack *")
            past_surgery         = st.text_input("Past Surgery *")
            ongoing_medications  = st.text_input("Ongoing Medications *")
            mental_medications   = st.text_input("Mental Medications *")
            inheritance_diseases = st.text_input("Inheritance Diseases *")
            genetic_disorders    = st.text_input("Genetic Disorders *")

        st.markdown('<div class="section-header">Lifestyle</div>', unsafe_allow_html=True)
        c5, c6 = st.columns(2)
        with c5:
            smoke_alcohol = st.text_input("Smoke / Alcohol *")
        with c6:
            allergies = st.text_input("Allergies *")

        st.markdown('<div class="section-header">Biometrics</div>', unsafe_allow_html=True)
        capture_face_opt = st.checkbox("Capture Face (opens camera)")

        submitted = st.form_submit_button("Save & Capture Fingerprints")

    if submitted:
        required = {
            "Email": em, "Name": name, "Phone": phone,
            "Blood Group": blood_group, "Emergency Contact": emergency_contact,
            "Asthma": asthma, "Diabetes": diabetes, "Heart Issues": heart_issues,
            "Hypertension": hypertension, "Thyroid": thyroid, "HIV": hiv,
            "Recent Heart Attack": recent_heart_attack,
            "Past Surgery": past_surgery,
            "Ongoing Medications": ongoing_medications,
            "Mental Medications": mental_medications,
            "Inheritance Diseases": inheritance_diseases,
            "Genetic Disorders": genetic_disorders,
            "Smoke/Alcohol": smoke_alcohol,
            "Allergies": allergies,
        }
        errors = [f"{k} cannot be blank." for k, v in required.items() if not v.strip()]
        if errors:
            for e in errors:
                alert("error", e)
        else:
            face_hash = None
            if capture_face_opt:
                with st.spinner("Opening camera — press 'c' to capture face..."):
                    face_hash = f6.get_face_hash()
                if not face_hash:
                    alert("warn", "Face capture failed or skipped.")

            alert("info", "Fingerprint 1 — place finger on scanner...")
            with st.spinner("Scanning fingerprint 1..."):
                fp1 = f6.capture_fingerprint()
            if not fp1:
                alert("error", "Fingerprint 1 capture failed. Aborting.")
                st.stop()

            alert("info", "Fingerprint 2 — place finger again...")
            with st.spinner("Scanning fingerprint 2..."):
                fp2 = f6.capture_fingerprint()
            if not fp2:
                alert("error", "Fingerprint 2 capture failed. Aborting.")
                st.stop()

            data = {
                "name": name.strip(), "phone": phone.strip(),
                "blood_group": blood_group.strip(),
                "emergency_contact": emergency_contact.strip(),
                "asthma": asthma.strip(), "diabetes": diabetes.strip(),
                "heart_issues": heart_issues.strip(),
                "hypertension": hypertension.strip(),
                "thyroid": thyroid.strip(), "hiv": hiv.strip(),
                "recent_heart_attack": recent_heart_attack.strip(),
                "past_surgery": past_surgery.strip(),
                "ongoing_medications": ongoing_medications.strip(),
                "mental_medications": mental_medications.strip(),
                "inheritance_diseases": inheritance_diseases.strip(),
                "genetic_disorders": genetic_disorders.strip(),
                "smoke_alcohol": smoke_alcohol.strip(),
                "allergies": allergies.strip(),
            }
            try:
                import uuid as _uuid
                import psycopg2 as _pg
                enc, nonce = f6.encrypt_data(data)
                conn = f6.connect_db()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO users
                    (user_id,email,encrypted_data,nonce,face_embeddings,fingerprint1,fingerprint2)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (str(_uuid.uuid4()), em.strip(), enc, nonce, face_hash,
                      _pg.Binary(fp1), _pg.Binary(fp2)))
                cur.execute("""
                    INSERT INTO data_entry_history
                    (entry_email, patient_email, entry_time, entry_role)
                    VALUES (%s,%s,%s,%s)
                """, (logged_email, em.strip(), datetime.now(), role.title()))
                conn.commit()
                cur.close()
                conn.close()
                alert("success", f"Patient **{name}** registered successfully.")
            except Exception as e:
                alert("error", f"Save failed: {e}")

elif page == "View Patient":
    st.markdown("# View Patient")
    em, uid, dec = patient_lookup_widget("vp")

    if em:
        show_patient_card(em, uid, dec)

        if role in ("doctor", "maintainer"):
            show_drug_interactions(dec)

        try:
            conn = f6.connect_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO access_history
                (access_email, patient_email, access_time, access_role)
                VALUES (%s,%s,%s,%s)
            """, (logged_email, em, datetime.now(), role.title()))
            conn.commit()
            cur.close()
            conn.close()
        except Exception:
            pass

elif page == "Edit Patient Data":
    st.markdown("# Edit Patient Data")

    if "edit_patient_email" not in st.session_state:
        st.session_state.edit_patient_email = None
    if "edit_patient_dec" not in st.session_state:
        st.session_state.edit_patient_dec = None

    if st.session_state.edit_patient_email is None:
        st.markdown('<div class="section-header">Step 1 — Identify Patient</div>', unsafe_allow_html=True)
        method = st.radio(
            "Lookup Method",
            ["Email", "Face Scan", "Fingerprint Scan"],
            horizontal=True,
            key="ep_method"
        )
        if method == "Email":
            em_input = st.text_input("Patient Email", key="ep_em")
            if st.button("Search", key="ep_search"):
                if not em_input.strip():
                    alert("error", "Email cannot be blank.")
                else:
                    result = fetch_patient_by_email(em_input.strip())
                    if result:
                        st.session_state.edit_patient_email = result[0]
                        st.session_state.edit_patient_dec   = result[2]
                        st.rerun()
                    else:
                        alert("error", "Patient not found.")
        elif method == "Face Scan":
            alert("info", "Click the button — camera will open. Press **'c'** inside the camera window to capture.")
            if st.button("Start Face Scan", key="ep_face"):
                result = fetch_patient_by_face()
                if result:
                    st.session_state.edit_patient_email = result[0]
                    st.session_state.edit_patient_dec   = result[2]
                    st.rerun()
                else:
                    alert("error", "No matching face found.")
        else:
            alert("info", "Click the button then place your finger on the scanner.")
            if st.button("Start Fingerprint Scan", key="ep_fp"):
                result = fetch_patient_by_fingerprint()
                if result:
                    st.session_state.edit_patient_email = result[0]
                    st.session_state.edit_patient_dec   = result[2]
                    st.rerun()
                else:
                    alert("error", "No matching fingerprint found.")

    if st.session_state.edit_patient_email and st.session_state.edit_patient_dec:
        em  = st.session_state.edit_patient_email
        dec = st.session_state.edit_patient_dec

        col_hdr, col_btn = st.columns([5, 1])
        with col_hdr:
            st.markdown(
                f'<div class="section-header">Editing record for: '
                f'<span class="badge-email">{em}</span></div>',
                unsafe_allow_html=True
            )
        with col_btn:
            if st.button("Change Patient", key="ep_reset"):
                st.session_state.edit_patient_email = None
                st.session_state.edit_patient_dec   = None
                st.rerun()

        st.markdown("*All fields are required. Change only what you need.*")

        with st.form("edit_form"):
            c1, c2 = st.columns(2)
            with c1:
                name                 = st.text_input("Full Name *",            value=dec.get("name",""))
                phone                = st.text_input("Phone *",                value=dec.get("phone",""))
                blood_group          = st.text_input("Blood Group *",          value=dec.get("blood_group",""))
                emergency_contact    = st.text_input("Emergency Contact *",    value=dec.get("emergency_contact",""))
                asthma               = st.text_input("Asthma *",               value=dec.get("asthma",""))
                diabetes             = st.text_input("Diabetes *",             value=dec.get("diabetes",""))
                heart_issues         = st.text_input("Heart Issues *",         value=dec.get("heart_issues",""))
                hypertension         = st.text_input("Hypertension *",         value=dec.get("hypertension",""))
                thyroid              = st.text_input("Thyroid *",              value=dec.get("thyroid",""))
            with c2:
                hiv                  = st.text_input("HIV *",                  value=dec.get("hiv",""))
                recent_heart_attack  = st.text_input("Recent Heart Attack *",  value=dec.get("recent_heart_attack",""))
                past_surgery         = st.text_input("Past Surgery *",         value=dec.get("past_surgery",""))
                ongoing_medications  = st.text_input("Ongoing Medications *",  value=dec.get("ongoing_medications",""))
                mental_medications   = st.text_input("Mental Medications *",   value=dec.get("mental_medications",""))
                inheritance_diseases = st.text_input("Inheritance Diseases *", value=dec.get("inheritance_diseases",""))
                genetic_disorders    = st.text_input("Genetic Disorders *",    value=dec.get("genetic_disorders",""))
                smoke_alcohol        = st.text_input("Smoke/Alcohol *",        value=dec.get("smoke_alcohol",""))
                allergies            = st.text_input("Allergies *",            value=dec.get("allergies",""))

            save = st.form_submit_button("Save Changes")

        if save:
            fields = {
                "Name": name, "Phone": phone, "Blood Group": blood_group,
                "Emergency Contact": emergency_contact, "Asthma": asthma,
                "Diabetes": diabetes, "Heart Issues": heart_issues,
                "Hypertension": hypertension, "Thyroid": thyroid, "HIV": hiv,
                "Recent Heart Attack": recent_heart_attack,
                "Past Surgery": past_surgery,
                "Ongoing Medications": ongoing_medications,
                "Mental Medications": mental_medications,
                "Inheritance Diseases": inheritance_diseases,
                "Genetic Disorders": genetic_disorders,
                "Smoke/Alcohol": smoke_alcohol,
                "Allergies": allergies,
            }
            errors = [f"{k} cannot be blank." for k, v in fields.items() if not v.strip()]
            if errors:
                for e in errors:
                    alert("error", e)
            else:
                new_data = {
                    "name": name.strip(), "phone": phone.strip(),
                    "blood_group": blood_group.strip(),
                    "emergency_contact": emergency_contact.strip(),
                    "asthma": asthma.strip(), "diabetes": diabetes.strip(),
                    "heart_issues": heart_issues.strip(),
                    "hypertension": hypertension.strip(),
                    "thyroid": thyroid.strip(), "hiv": hiv.strip(),
                    "recent_heart_attack": recent_heart_attack.strip(),
                    "past_surgery": past_surgery.strip(),
                    "ongoing_medications": ongoing_medications.strip(),
                    "mental_medications": mental_medications.strip(),
                    "inheritance_diseases": inheritance_diseases.strip(),
                    "genetic_disorders": genetic_disorders.strip(),
                    "smoke_alcohol": smoke_alcohol.strip(),
                    "allergies": allergies.strip(),
                }
                try:
                    enc, nonce = f6.encrypt_data(new_data)
                    conn = f6.connect_db()
                    cur = conn.cursor()
                    cur.execute("""
                        UPDATE users SET encrypted_data=%s, nonce=%s WHERE email=%s
                    """, (enc, nonce, em))
                    cur.execute("""
                        INSERT INTO edit_history
                        (editor_email, patient_email, edit_time, editor_role)
                        VALUES (%s,%s,%s,%s)
                    """, (logged_email, em, datetime.now(), role.title()))
                    conn.commit()
                    cur.close()
                    conn.close()
                    st.session_state.edit_patient_dec = new_data
                    alert("success", "Patient record updated successfully.")
                except Exception as e:
                    alert("error", f"Update failed: {e}")

elif page == "Access History":
    st.markdown("# Access History")
    try:
        conn = f6.connect_db()
        cur = conn.cursor()
        if role == "user":
            cur.execute("""
                SELECT access_email, access_role, access_time
                FROM access_history WHERE patient_email=%s ORDER BY access_time DESC
            """, (logged_email,))
            rows = cur.fetchall()
            cur.close(); conn.close()
            if rows:
                import pandas as pd
                df = pd.DataFrame(rows, columns=["Accessed By", "Role", "Time"])
                st.dataframe(df, use_container_width=True)
            else:
                alert("info", "No access history yet.")
        else:
            cur.execute("""
                SELECT patient_email, access_time
                FROM access_history WHERE access_email=%s ORDER BY access_time DESC
            """, (logged_email,))
            rows = cur.fetchall()
            cur.close(); conn.close()
            if rows:
                import pandas as pd
                df = pd.DataFrame(rows, columns=["Patient Email", "Time"])
                st.dataframe(df, use_container_width=True)
            else:
                alert("info", "No access history yet.")
    except Exception as e:
        alert("error", str(e))

elif page == "Edit History":
    st.markdown("# Edit History")
    try:
        conn = f6.connect_db()
        cur = conn.cursor()
        if role == "user":
            cur.execute("""
                SELECT editor_email, editor_role, edit_time
                FROM edit_history WHERE patient_email=%s ORDER BY edit_time DESC
            """, (logged_email,))
            rows = cur.fetchall()
            cur.close(); conn.close()
            if rows:
                import pandas as pd
                df = pd.DataFrame(rows, columns=["Edited By", "Role", "Time"])
                st.dataframe(df, use_container_width=True)
            else:
                alert("info", "No edit history yet.")
        else:
            cur.execute("""
                SELECT patient_email, edit_time
                FROM edit_history WHERE editor_email=%s ORDER BY edit_time DESC
            """, (logged_email,))
            rows = cur.fetchall()
            cur.close(); conn.close()
            if rows:
                import pandas as pd
                df = pd.DataFrame(rows, columns=["Patient Email", "Time"])
                st.dataframe(df, use_container_width=True)
            else:
                alert("info", "No edit history yet.")
    except Exception as e:
        alert("error", str(e))

elif page == "Data Entry History":
    st.markdown("# Data Entry History")
    try:
        conn = f6.connect_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT patient_email, entry_time
            FROM data_entry_history WHERE entry_email=%s ORDER BY entry_time DESC
        """, (logged_email,))
        rows = cur.fetchall()
        cur.close(); conn.close()
        if rows:
            import pandas as pd
            df = pd.DataFrame(rows, columns=["Patient Email", "Time"])
            st.dataframe(df, use_container_width=True)
        else:
            alert("info", "No data entry history yet.")
    except Exception as e:
        alert("error", str(e))