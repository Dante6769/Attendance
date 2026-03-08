from flask_cors import CORS
from flask import Flask, request, jsonify, send_file
import pandas as pd
import qrcode
from datetime import datetime
from io import BytesIO
import os
import threading

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Absolute paths to Excel files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
students_file = os.path.join(BASE_DIR, "../excel_data/students.xlsx")
teachers_file = os.path.join(BASE_DIR, "../excel_data/teachers.xlsx")
attendance_file = os.path.join(BASE_DIR, "../excel_data/attendance.xlsx")

SESSION = {}
lock = threading.Lock()

# -------------------------
# TEACHER LOGIN
# -------------------------
@app.route("/teacher_login", methods=["POST"])
def teacher_login():
    data = request.json
    username = str(data.get("username")).strip()
    password = str(data.get("password")).strip()

    df = pd.read_excel(teachers_file, dtype=str)
    user = df[(df["username"] == username) & (df["password"] == password)]
    if not user.empty:
        SESSION["teacher"] = username
        return jsonify({"status": "success"})
    return jsonify({"status": "invalid"})

# -------------------------
# START SESSION
# -------------------------
@app.route("/start_session", methods=["POST"])
def start_session():
    data = request.json
    division = data["division"]
    lecture = int(data["lecture"])
    teacher = data["teacher"]

    timetable_file = f"../excel_data/timetable{division}.xlsx"
    timetable = pd.read_excel(timetable_file, dtype=str)

    today = datetime.now().strftime("%A")
    lec = timetable[(timetable["Day"] == today) & (timetable["Lecture"] == str(lecture))]

    if lec.empty:
        return jsonify({"status": "no_lecture_today"})

    subject = lec.iloc[0]["Subject"]
    session_id = str(datetime.now().timestamp())

    SESSION.update({
        "session": session_id,
        "division": division,
        "lecture": lecture,
        "subject": subject,
        "teacher": teacher
    })

    return jsonify({
        "status": "session_started",
        "subject": subject,
        "session": session_id
    })

# -------------------------
# STOP SESSION
# -------------------------
@app.route("/stop_session", methods=["POST"])
def stop_session():
    SESSION.clear()
    return jsonify({"status": "stopped"})

# -------------------------
# STUDENT LOGIN
# -------------------------
@app.route("/student_login", methods=["POST"])
def student_login():
    data = request.json
    username = str(data.get("username")).strip()
    password = str(data.get("password")).strip()

    df = pd.read_excel(students_file, dtype=str)
    df["Username"] = df["Username"].str.strip()
    df["Password"] = df["Password"].str.strip()

    user = df[(df["Username"] == username) & (df["Password"] == password)]
    if user.empty:
        return jsonify({"status": "fail"})

    student = user.iloc[0]
    return jsonify({
        "status": "success",
        "name": student["Name"],
        "roll": str(student["Roll"]),
        "division": student["Division"]
    })

# -------------------------
# GENERATE QR
# -------------------------
@app.route("/generate_qr")
def generate_qr():
    session_id = SESSION.get("session")
    if not session_id:
        return jsonify({"error": "session not started"})

    # Change this BASE URL when deploying on server
    url = f"http://127.0.0.1:5500/verify.html?session={session_id}"
    img = qrcode.make(url)

    buffer = BytesIO()
    img.save(buffer)
    buffer.seek(0)
    return send_file(buffer, mimetype="image/png")

# -------------------------
# MARK ATTENDANCE
# -------------------------
@app.route("/mark_attendance", methods=["POST"])
def mark_attendance():
    if "session" not in SESSION:
        return jsonify({"status": "attendance_closed"})

    data = request.json
    name = data.get("name")
    roll = str(data.get("roll"))
    division = data.get("division")

    if not all([name, roll, division]):
        return jsonify({"status": "error", "message": "Incomplete data"})
    
    if division != SESSION["division"]:
        return jsonify({"status": "wrong_division"})

    # Lock to prevent Excel corruption
    with lock:
        if os.path.exists(attendance_file):
            df = pd.read_excel(attendance_file, dtype=str)
        else:
            df = pd.DataFrame(columns=[
                "Date","Time","Name","Roll","Division",
                "Subject","Lecture","Teacher"
            ])

        today = str(datetime.now().date())
        existing = df[
            (df["Roll"].astype(str) == roll) &
            (df["Date"] == today) &
            (df["Lecture"] == str(SESSION["lecture"]))
        ]

        if not existing.empty:
            return jsonify({"status": "already_marked"})

        row = {
            "Date": today,
            "Time": datetime.now().strftime("%H:%M"),
            "Name": name,
            "Roll": roll,
            "Division": division,
            "Subject": SESSION["subject"],
            "Lecture": SESSION["lecture"],
            "Teacher": SESSION["teacher"]
        }

        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        df.to_excel(attendance_file, index=False)

    return jsonify({"status": "present"})

# -------------------------
# VIEW ATTENDANCE BY DIVISION
# -------------------------
@app.route("/attendance_by_division")
def attendance_by_division():
    division = request.args.get("division")
    if not os.path.exists(attendance_file):
        return jsonify([])

    df = pd.read_excel(attendance_file, dtype=str)
    df = df[df["Division"] == division]
    return jsonify(df.to_dict(orient="records"))

# -------------------------
# ATTENDANCE DATA FOR REPORT
# -------------------------
@app.route("/attendance_data")
def attendance_data():
    if os.path.exists(attendance_file):
        df = pd.read_excel(attendance_file, dtype=str)
        return jsonify(df.to_dict(orient="records"))
    return jsonify([])

# -------------------------
# RUN SERVER
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)