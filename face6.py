import subprocess, sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

required_packages = [
    "opencv-python",
    "deepface",
    "numpy",
    "psycopg2-binary",
    "cryptography"
]

if __name__ == "__main__":
    for pkg in required_packages:
        try:
            __import__(pkg.split("-")[0])
        except:
            install(pkg)

import psycopg2
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import uuid, json, base64, os, getpass
from datetime import datetime

import cv2
import numpy as np
import hashlib
from deepface import DeepFace

import uuid
import json
import base64
import os
import getpass
from datetime import datetime


DB_NAME = "emergency_medical_db"
DB_USER = "postgres"
DB_PASSWORD = "1234"
DB_HOST = "localhost"
DB_PORT = "5432"

def connect_db():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )


def create_table():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
        user_id UUID PRIMARY KEY,
        email TEXT UNIQUE,
        encrypted_data TEXT,
        nonce TEXT,
        face_embeddings TEXT,
        fingerprint1 TEXT,
        fingerprint2 TEXT
    )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_auth (
        email TEXT PRIMARY KEY,
        password TEXT,
        nonce TEXT
    )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS doctor_auth (
        email TEXT PRIMARY KEY,
        password TEXT,
        nonce TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS medical_maintainer_auth (
        email TEXT PRIMARY KEY,
        password TEXT,
        nonce TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS access_history (
        access_email TEXT,
        patient_email TEXT,
        access_time TIMESTAMP,
        access_role TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS edit_history (
        editor_email TEXT,
        patient_email TEXT,
        edit_time TIMESTAMP,
        editor_role TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS data_entry_history (
        entry_email TEXT,
        patient_email TEXT,
        entry_time TIMESTAMP,
        entry_role TEXT
    )
    """)

    conn.commit()
    cur.close()
    conn.close()


AES_KEY = base64.b64decode("q7h5l9Tg8yR2w3XzK4Vn6Jc1P0mF8BQa2dL5s7W9uYQ=")

def encrypt_data(data):
    aes = AESGCM(AES_KEY)
    nonce = os.urandom(12)

    plaintext = json.dumps(data).encode()
    ciphertext = aes.encrypt(nonce, plaintext, None)

    return base64.b64encode(ciphertext).decode(), base64.b64encode(nonce).decode()


def decrypt_data(ciphertext, nonce):
    aes = AESGCM(AES_KEY)

    ciphertext = base64.b64decode(ciphertext)
    nonce = base64.b64decode(nonce)

    plaintext = aes.decrypt(nonce, ciphertext, None)

    return json.loads(plaintext.decode())


def capture_face():
    cap = cv2.VideoCapture(0)
    print("Press 'c' to capture face")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Camera error")
            break

        cv2.imshow("Capture Face", frame)
        if cv2.waitKey(1) & 0xFF == ord('c'):
            cap.release()
            cv2.destroyAllWindows()
            return frame


def capture_fingerprint():
    """
    Calls the C# app with mode 'capture'.
    C# sends ALL device quality logs to stderr; only TEMPLATE:<base64> goes to stdout.
    Python reads stdout only, so quality spam never interferes.
    Returns: bytes (template) or None on failure
    """
    try:
        project_path = os.path.join(os.getcwd(), "FingerprintApp")

        result = subprocess.run(
            ["dotnet", "run", "--", "capture"],
            cwd=project_path,
            stdout=subprocess.PIPE,   
            stderr=subprocess.PIPE,   
            timeout=30
        )

        stdout = result.stdout.decode("utf-8", errors="replace").strip()

        if not stdout:
            print("Fingerprint capture: no output from device")
            return None

        for line in stdout.splitlines():
            line = line.strip()
            if line.startswith("TEMPLATE:"):
                b64 = line[len("TEMPLATE:"):].strip()
                return base64.b64decode(b64)
            if line.startswith("ERROR:") or line == "INIT_FAIL":
                print("Fingerprint capture error:", line)
                return None

        print("Fingerprint capture failed. stdout:", stdout)
        return None

    except subprocess.TimeoutExpired:
        print("Fingerprint capture timed out")
        return None
    except Exception as e:
        print("Fingerprint error:", e)
        return None


def match_fingerprint():
    """
    1. Calls C# to capture & extract a fresh template (bytes)
    2. Sends those bytes back to C# with mode 'match' via stdin
       (C# does the SourceAFIS matching against the two stored columns)
       -- OR --
       Python loads both stored templates from DB and calls C# per-pair.
    
    Chosen approach: Python fetches stored templates from DB,
    then calls C# with mode 'match_template' passing the live template
    via stdin and each stored template as a second argument, so the
    matching logic (SourceAFIS) stays in C# where the library lives.

    Flow:
      Python captures live template → for each row in DB →
        call C# 'match_pair' with live_b64 + stored_b64 → C# returns score →
        Python picks best score → if > threshold return email + data
    """
    print("Scan fingerprint for matching...")

    live_bytes = capture_fingerprint()
    if not live_bytes:
        print("Could not capture fingerprint")
        return None

    live_b64 = base64.b64encode(live_bytes).decode()

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT email, user_id, encrypted_data, nonce, fingerprint1, fingerprint2 FROM users")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        print("No patients registered")
        return None

    project_path = os.path.join(os.getcwd(), "FingerprintApp")

    best_score = -1
    best_row = None

    for email, user_id, encrypted_data, nonce, fp1, fp2 in rows:
        for fp_col in (fp1, fp2):
            if not fp_col:
                continue

            if isinstance(fp_col, memoryview):
                stored_b64 = base64.b64encode(bytes(fp_col)).decode()
            elif isinstance(fp_col, (bytes, bytearray)):
                stored_b64 = base64.b64encode(fp_col).decode()
            else:
                stored_b64 = fp_col

            try:
                result = subprocess.run(
                    ["dotnet", "run", "--", "match_pair", live_b64, stored_b64],
                    cwd=project_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=15
                )
                output = result.stdout.decode("utf-8", errors="replace").strip()

                for line in output.splitlines():
                    if line.startswith("SCORE:"):
                        score = float(line[len("SCORE:"):].strip())
                        if score > best_score:
                            best_score = score
                            best_row = (email, user_id, encrypted_data, nonce)
            except Exception as e:
                print(f"Match error for {email}:", e)
                continue

    THRESHOLD = 20.0 

    if best_score >= THRESHOLD and best_row:
        email, user_id, encrypted_data, nonce = best_row
        print(f"\nFingerprint Match Found (Score: {best_score:.2f})")
        decrypted = decrypt_data(encrypted_data, nonce)
        print("\n------ Patient Data ------\n")
        print(f"Email          : {email}")
        print(f"UUID           : {user_id}")
        print()
        for key, value in decrypted.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        return email
    else:
        print("No matching fingerprint found")
        return None


def generate_embedding(image):
    embedding = DeepFace.represent(
        img_path=image,
        model_name="Facenet",
        enforce_detection=True
    )[0]["embedding"]

    return np.array(embedding)

def hash_embedding(embedding):
    return hashlib.sha256(embedding.tobytes()).hexdigest()

def get_face_hash():
    try:
        img = capture_face()
        emb = generate_embedding(img)

        return json.dumps(emb.tolist())

    except Exception as e:
        print("Face capture failed:", e)
        return None


def enter_patient_data(editor_email, role):

    print("\nEnter Patient Details")

    email = input("Patient Email: ")
    name = input("Name: ")
    phone = input("Phone: ")
    blood_group = input("Blood Group: ")
    emergency_contact = input("Emergency Contact: ")

    asthma = input("Asthma: ")
    diabetes = input("Diabetes: ")
    heart_issues = input("Heart Issues: ")
    hypertension = input("Hypertension: ")
    thyroid = input("Thyroid: ")
    hiv = input("HIV: ")
    recent_heart_attack = input("Recent Heart Attack: ")
    past_surgery = input("Past Surgery: ")
    ongoing_medications = input("Ongoing Medications: ")
    mental_medications = input("Mental Medications: ")
    inheritance_diseases = input("Inheritance Diseases: ")
    genetic_disorders = input("Genetic Disorders: ")
    smoke_alcohol = input("Smoke/Alcohol: ")
    allergies = input("Allergies: ")

    user_uuid = str(uuid.uuid4())

    face_hash = None
    choice = input("Do you want to capture face? (y/n): ")

    if choice.lower() == 'y':
        face_hash = get_face_hash()


    print("\nCapture Fingerprint 1 — place finger on scanner...")
    fp1 = capture_fingerprint()
    if not fp1:
        print("Fingerprint 1 capture failed")
        return

    print("\nCapture Fingerprint 2 — place finger on scanner again...")
    fp2 = capture_fingerprint()
    if not fp2:
        print("Fingerprint 2 capture failed")
        return

    data = {
        "name": name,
        "phone": phone,
        "blood_group": blood_group,
        "emergency_contact": emergency_contact,
        "asthma": asthma,
        "diabetes": diabetes,
        "heart_issues": heart_issues,
        "hypertension": hypertension,
        "thyroid": thyroid,
        "hiv": hiv,
        "recent_heart_attack": recent_heart_attack,
        "past_surgery": past_surgery,
        "ongoing_medications": ongoing_medications,
        "mental_medications": mental_medications,
        "inheritance_diseases": inheritance_diseases,
        "genetic_disorders": genetic_disorders,
        "smoke_alcohol": smoke_alcohol,
        "allergies": allergies
    }

    encrypted, nonce = encrypt_data(data)

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO users (user_id,email,encrypted_data,nonce,face_embeddings,fingerprint1,fingerprint2)
    VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (
        str(uuid.uuid4()),
        email,
        encrypted,
        nonce,
        face_hash,
        psycopg2.Binary(fp1),   
        psycopg2.Binary(fp2)    
    ))

    cur.execute("""
    INSERT INTO data_entry_history(entry_email,patient_email,entry_time,entry_role)
    VALUES (%s,%s,%s,%s)
    """,(editor_email,email,datetime.now(),role))

    conn.commit()
    cur.close()
    conn.close()

    print("Patient data + fingerprints stored successfully")


def _fingerprint_lookup_only():
    """
    Capture live fingerprint, compare against DB in Python (same as match_fingerprint),
    but only return the matched email WITHOUT printing patient data.
    Used by edit_patient_data so it can proceed to the edit form.
    """
    print("Scan fingerprint...")
    live_bytes = capture_fingerprint()
    if not live_bytes:
        print("Could not capture fingerprint")
        return None

    live_b64 = base64.b64encode(live_bytes).decode()

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT email, fingerprint1, fingerprint2 FROM users")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        print("No patients registered")
        return None

    project_path = os.path.join(os.getcwd(), "FingerprintApp")
    best_score = -1
    best_email = None

    for email, fp1, fp2 in rows:
        for fp_col in (fp1, fp2):
            if not fp_col:
                continue
            if isinstance(fp_col, memoryview):
                stored_b64 = base64.b64encode(bytes(fp_col)).decode()
            elif isinstance(fp_col, (bytes, bytearray)):
                stored_b64 = base64.b64encode(fp_col).decode()
            else:
                stored_b64 = fp_col
            try:
                result = subprocess.run(
                    ["dotnet", "run", "--", "match_pair", live_b64, stored_b64],
                    cwd=project_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=15
                )
                output = result.stdout.decode("utf-8", errors="replace").strip()
                for line in output.splitlines():
                    if line.startswith("SCORE:"):
                        score = float(line[len("SCORE:"):].strip())
                        if score > best_score:
                            best_score = score
                            best_email = email
            except Exception as e:
                print(f"Match error for {email}:", e)
                continue

    THRESHOLD = 20.0
    if best_score >= THRESHOLD and best_email:
        print(f"Fingerprint matched: {best_email} (Score: {best_score:.2f})")
        return best_email
    else:
        print("No matching fingerprint found")
        return None


def edit_patient_data(editor_email, role):

    print("\nChoose Patient Lookup Method")
    print("1 Email")
    print("2 Face Scan")
    print("3 Fingerprint Scan")

    lookup = input("Enter option: ")

    if lookup == "1":
        patient_email = input("Enter patient email to edit: ")
    elif lookup == "2":
        patient_email = find_patient_by_face()
    elif lookup == "3":
        patient_email = _fingerprint_lookup_only()
    else:
        print("Invalid option")
        return

    if not patient_email:
        print("Patient not identified")
        return

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT encrypted_data,nonce FROM users WHERE email=%s",(patient_email,))
    result = cur.fetchone()

    if not result:
        print("Patient not found")
        return

    data = decrypt_data(result[0],result[1])

    print("\nLeave blank to keep old value\n")

    name = input(f"Name ({data['name']}): ") or data["name"]
    phone = input(f"Phone ({data['phone']}): ") or data["phone"]
    blood_group = input(f"Blood Group ({data['blood_group']}): ") or data["blood_group"]
    emergency_contact = input(f"Emergency Contact ({data['emergency_contact']}): ") or data["emergency_contact"]

    asthma = input(f"Asthma ({data['asthma']}): ") or data["asthma"]
    diabetes = input(f"Diabetes ({data['diabetes']}): ") or data["diabetes"]
    heart_issues = input(f"Heart Issues ({data['heart_issues']}): ") or data["heart_issues"]
    hypertension = input(f"Hypertension ({data['hypertension']}): ") or data["hypertension"]
    thyroid = input(f"Thyroid ({data['thyroid']}): ") or data["thyroid"]
    hiv = input(f"HIV ({data['hiv']}): ") or data["hiv"]
    recent_heart_attack = input(f"Recent Heart Attack ({data['recent_heart_attack']}): ") or data["recent_heart_attack"]
    past_surgery = input(f"Past Surgery ({data['past_surgery']}): ") or data["past_surgery"]
    ongoing_medications = input(f"Ongoing Medications ({data['ongoing_medications']}): ") or data["ongoing_medications"]
    mental_medications = input(f"Mental Medications ({data['mental_medications']}): ") or data["mental_medications"]
    inheritance_diseases = input(f"Inheritance Diseases ({data['inheritance_diseases']}): ") or data["inheritance_diseases"]
    genetic_disorders = input(f"Genetic Disorders ({data['genetic_disorders']}): ") or data["genetic_disorders"]
    smoke_alcohol = input(f"Smoke/Alcohol ({data['smoke_alcohol']}): ") or data["smoke_alcohol"]
    allergies = input(f"Allergies ({data['allergies']}): ") or data["allergies"]

    new_data = {
        "name": name,
        "phone": phone,
        "blood_group": blood_group,
        "emergency_contact": emergency_contact,
        "asthma": asthma,
        "diabetes": diabetes,
        "heart_issues": heart_issues,
        "hypertension": hypertension,
        "thyroid": thyroid,
        "hiv": hiv,
        "recent_heart_attack": recent_heart_attack,
        "past_surgery": past_surgery,
        "ongoing_medications": ongoing_medications,
        "mental_medications": mental_medications,
        "inheritance_diseases": inheritance_diseases,
        "genetic_disorders": genetic_disorders,
        "smoke_alcohol": smoke_alcohol,
        "allergies": allergies
    }

    encrypted, nonce = encrypt_data(new_data)

    cur.execute("""
    UPDATE users
    SET encrypted_data=%s, nonce=%s
    WHERE email=%s
    """,(encrypted,nonce,patient_email))

    cur.execute("""
    INSERT INTO edit_history(editor_email,patient_email,edit_time,editor_role)
    VALUES (%s,%s,%s,%s)
    """,(editor_email,patient_email,datetime.now(),role))

    conn.commit()
    cur.close()
    conn.close()

    print("Patient data updated successfully")

def login(role):

    email = input("Enter Email: ")
    password = getpass.getpass("Enter Password: ")

    conn = connect_db()
    cur = conn.cursor()

    if role == "user":
        cur.execute("SELECT password,nonce FROM user_auth WHERE email=%s",(email,))
    elif role == "doctor":
        cur.execute("SELECT password,nonce FROM doctor_auth WHERE email=%s",(email,))
    else:
        cur.execute("SELECT password,nonce FROM medical_maintainer_auth WHERE email=%s",(email,))

    result = cur.fetchone()

    if not result:
        print("Account not found")
        return None

    decrypted = decrypt_data(result[0],result[1])

    if decrypted["password"] == password:
        print("Login Successful")
        return email
    else:
        print("Invalid Password")
        return None
    
def signup(role):

    email = input("Enter Email: ")
    password = getpass.getpass("Enter Password: ")

    encrypted, nonce = encrypt_data({"password": password})

    conn = connect_db()
    cur = conn.cursor()

    if role == "user":
        cur.execute("INSERT INTO user_auth VALUES (%s,%s,%s)",(email,encrypted,nonce))
    elif role == "doctor":
        cur.execute("INSERT INTO doctor_auth VALUES (%s,%s,%s)",(email,encrypted,nonce))
    elif role == "maintainer":
        cur.execute("INSERT INTO medical_maintainer_auth VALUES (%s,%s,%s)",(email,encrypted,nonce))

    conn.commit()
    cur.close()
    conn.close()

    print("Signup Successful")

def view_user_access_history(user_email):

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT access_email,access_role,access_time
    FROM access_history
    WHERE patient_email=%s
    """,(user_email,))

    rows = cur.fetchall()

    for r in rows:
        print(r[1],":",r[0],"| Time:",r[2])

    cur.close()
    conn.close()


def view_user_edit_history(user_email):

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT editor_email,editor_role,edit_time
    FROM edit_history
    WHERE patient_email=%s
    """,(user_email,))

    rows = cur.fetchall()

    for r in rows:
        print(r[1],":",r[0],"| Time:",r[2])

    cur.close()
    conn.close()

def view_data_entry_history(email):

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT patient_email, entry_time
    FROM data_entry_history
    WHERE entry_email=%s
    """,(email,))

    rows = cur.fetchall()

    for r in rows:
        print("Patient:",r[0],"| Time:",r[1])

    cur.close()
    conn.close()

def view_doctor_access_history(doctor_email):

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT patient_email,access_time
    FROM access_history
    WHERE access_email=%s
    """,(doctor_email,))

    rows = cur.fetchall()

    for r in rows:
        print("Patient:",r[0],"| Time:",r[1])

    cur.close()
    conn.close()


def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def find_patient_by_face():
    print("Capturing face for recognition...")
    
    try:
        img = capture_face()
        emb = generate_embedding(img)

        conn = connect_db()
        cur = conn.cursor()

        cur.execute("SELECT email, face_embeddings FROM users WHERE face_embeddings IS NOT NULL")
        rows = cur.fetchall()

        best_match = None
        best_score = -1

        for email, stored_emb in rows:
            stored_emb = np.array(json.loads(stored_emb))
            score = cosine_similarity(emb, stored_emb)

            if score > best_score:
                best_score = score
                best_match = email

        cur.close()
        conn.close()

        if best_score > 0.7:
            print(f"\nMatch Found (Score: {best_score:.2f}) → {best_match}")
            return best_match
        else:
            print("No matching face found")
            return None

    except Exception as e:
        print("Face recognition failed:", e)
        return None


def view_doctor_edit_history(doctor_email):

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT patient_email,edit_time
    FROM edit_history
    WHERE editor_email=%s
    """,(doctor_email,))

    rows = cur.fetchall()

    for r in rows:
        print("Patient:",r[0],"| Time:",r[1])

    cur.close()
    conn.close()

def _display_patient(patient_email, conn, cur):
    """Fetch and print email, uuid, encrypted_data, and decrypted fields for a patient."""
    cur.execute("SELECT user_id, encrypted_data, nonce FROM users WHERE email=%s",(patient_email,))
    result = cur.fetchone()
    if result:
        user_id, encrypted_data, nonce = result
        decrypted = decrypt_data(encrypted_data, nonce)
        print("\n------ Patient Data ------\n")
        print(f"Email          : {patient_email}")
        print(f"UUID           : {user_id}")
        print()
        for key, value in decrypted.items():
            print(f"{key.replace('_',' ').title()}: {value}")
        return True
    else:
        print("Patient not found")
        return False


def doctor_access(access_email, role):

    print("\nChoose Access Method")
    print("1 Email")
    print("2 Face Recognition")
    print("3 Fingerprint")

    choice = input("Enter option: ")

    if choice == "1":
        patient_email = input("Enter patient email: ")
    elif choice == "2":
        patient_email = find_patient_by_face()
    elif choice == "3":
        patient_email = _fingerprint_lookup_only()
    else:
        print("Invalid option")
        return

    if not patient_email:
        return

    conn = connect_db()
    cur = conn.cursor()

    found = _display_patient(patient_email, conn, cur)

    if found:
        cur.execute("""
        INSERT INTO access_history(access_email,patient_email,access_time,access_role)
        VALUES (%s,%s,%s,%s)
        """,(access_email, patient_email, datetime.now(), role))
        conn.commit()

    cur.close()
    conn.close()


def view_user_data(email):

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT user_id, encrypted_data, nonce FROM users WHERE email=%s",(email,))
    result = cur.fetchone()

    if result:
        user_id, encrypted_data, nonce = result
        decrypted = decrypt_data(encrypted_data, nonce)

        print("\n------ Patient Data ------\n")
        print(f"Email          : {email}")
        print(f"UUID           : {user_id}")
        print()
        for key, value in decrypted.items():
            print(f"{key.replace('_',' ').title()}: {value}")

    else:
        print("No data found")

    cur.close()
    conn.close()


def main():

    create_table()

    while True:

        print("\nChoose Role")
        print("1 User")
        print("2 Doctor")
        print("3 Medical Data Maintainer")
        print("4 Exit")

        role = input("Enter option: ")

        if role == "1":

            print("\n1 Signup")
            print("2 Login")
            auth = input("Choose: ")

            if auth == "1":
                signup("user")
                continue

            email = login("user")
            if not email:
                continue

            while True:

                print("\nUser Options")
                print("1 View Data")
                print("2 View Access History")
                print("3 View Edit History")
                print("4 Logout")

                c = input("Choose: ")

                if c == "1":
                    view_user_data(email)
                elif c == "2":
                    view_user_access_history(email)
                elif c == "3":
                    view_user_edit_history(email)
                elif c == "4":
                    break


        elif role == "2":

            print("\n1 Signup")
            print("2 Login")
            auth = input("Choose: ")

            if auth == "1":
                signup("doctor")
                continue

            doctor_email = login("doctor")
            if not doctor_email:
                continue

            while True:

                print("\nDoctor Options")
                print("1 Enter Patient Data")
                print("2 View Patient")
                print("3 Edit Patient Data")
                print("4 View Access History")
                print("5 View Edit History")
                print("6 Data Entry History")
                print("7 Logout")

                c = input("Choose: ")

                if c == "1":
                    enter_patient_data(doctor_email,"Doctor")
                elif c == "2":
                    doctor_access(doctor_email,"Doctor")
                elif c == "3":
                    edit_patient_data(doctor_email,"Doctor")
                elif c == "4":
                    view_doctor_access_history(doctor_email)
                elif c == "5":
                    view_doctor_edit_history(doctor_email)
                elif c == "6":
                    view_data_entry_history(doctor_email)
                elif c == "7":
                    break


        elif role == "3":

            print("\n1 Signup")
            print("2 Login")
            auth = input("Choose: ")

            if auth == "1":
                signup("maintainer")
                continue

            maintainer_email = login("maintainer")
            if not maintainer_email:
                continue

            while True:

                print("\nMaintainer Options")
                print("1 Enter Patient Data")
                print("2 View Patient")
                print("3 Edit User Data")
                print("4 View Access History")
                print("5 View Edit History")
                print("6 Data Entry History")
                print("7 Logout")

                c = input("Choose: ")

                if c == "1":
                    enter_patient_data(maintainer_email,"Maintainer")
                elif c == "2":
                    doctor_access(maintainer_email,"Maintainer")
                elif c == "3":
                    edit_patient_data(maintainer_email,"Maintainer")
                elif c == "4":
                    view_doctor_access_history(maintainer_email)
                elif c == "5":
                    view_doctor_edit_history(maintainer_email)
                elif c == "6":
                    view_data_entry_history(maintainer_email)
                elif c == "7":
                    break

        elif role == "4":
            break

if __name__ == "__main__":
    main()