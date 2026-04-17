import os
from flask import Flask, render_template, request, jsonify
import psycopg2
from werkzeug.utils import secure_filename

app = Flask(__name__)

DB_CONFIG = {
    "host": "localhost",
    "database": "students_db",
    "user": "postgres",
    "password": "postgres"
}

UPLOAD_FOLDER = "static/resumes"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


@app.route("/")
@app.route("/home.html")
def home():
    return render_template("home.html")


@app.route("/student.html")
def student_page():
    return render_template("student.html")


@app.route("/studentEntry.html")
def attendance_page():
    return render_template("studentEntry.html")


@app.route("/studentList.html")
def student_list_page():
    return render_template("studentList.html")

@app.route("/attendanceLog.html")
def attendance_log_page():
    return render_template("attendanceLog.html")


@app.route("/api/add_student", methods=["POST"])
def add_student():
    conn = None
    cur = None

    try:
        student_id = request.form.get("id")
        full_name = request.form.get("name")
        dob = request.form.get("dob")
        email = request.form.get("email")
        phone = request.form.get("phone")
        address = request.form.get("address")
        course = request.form.get("course")

        if not student_id or not full_name:
            return jsonify({"error": "Required fields missing"}), 400

        file = request.files.get("resume")
        filename = None

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO students
            (student_id, full_name, dob, email, phone, address, course, resume_filename, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)
        """, (
            student_id,
            full_name,
            dob,
            email,
            phone,
            address,
            course,
            filename
        ))

        conn.commit()

        return jsonify({"message": "Student added successfully!"}), 201

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route("/api/get_students")
def get_students():
    conn = get_conn()
    cur = conn.cursor()

   
    cur.execute("""
        SELECT student_id, full_name, email, course, is_active, phone
        FROM students
        ORDER BY full_name
    """)

    students = [{
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "course": row[3],
        "active": row[4],
        "phone": row[5] 
    } for row in cur.fetchall()]

    cur.close()
    conn.close()

    return jsonify(students)

@app.route("/api/update_student", methods=["POST"])
def update_student():
    data = request.get_json()

    old_id = data.get("old_id")
    new_id = data.get("id")
    full_name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")

    if not old_id:
        return jsonify({"error": "Original Student ID required"}), 400

    conn = None
    cur = None

    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
            UPDATE students 
            SET student_id = %s,
                full_name = %s,
                email = %s,
                phone = %s
            WHERE student_id = %s
        """, (new_id, full_name, email, phone, old_id))

        conn.commit()

        if cur.rowcount == 0:
            return jsonify({"error": "No student found"}), 404

        return jsonify({"message": "Student updated successfully!"}), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()



@app.route("/api/delete_student/<student_id>", methods=["DELETE"])
def delete_student(student_id):
    conn = None
    cur = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        
    
        cur.execute("DELETE FROM students WHERE student_id = %s", (student_id,))
        
        conn.commit()
        return jsonify({"message": "Student deleted successfully!"}), 200
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if cur: cur.close()
        if conn: conn.close()



@app.route("/api/mark_attendance", methods=["POST"])
def mark_attendance():
    data = request.get_json()

    student_id = data.get("id")
    date = data.get("date")
    check_in = data.get("in")
    check_out = data.get("out")

    if not student_id or not date:
        return jsonify({"error": "Missing data"}), 400

    conn = None
    cur = None

    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO attendance
            (student_id, date, check_in, check_out)
            VALUES (%s, %s, %s, %s)
        """, (student_id, date, check_in, check_out))

        conn.commit()

        return jsonify({"message": "Attendance saved successfully!"})

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route("/api/get_attendance")
def get_attendance():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT student_id, date, check_in, check_out
        FROM attendance
        ORDER BY date DESC
    """)

    logs = [{
        "id": row[0],
        "date": row[1].strftime("%Y-%m-%d"),
        "in": str(row[2]),
        "out": str(row[3])
    } for row in cur.fetchall()]

    cur.close()
    conn.close()

    return jsonify(logs)

@app.route("/api/delete_selected_students", methods=["POST"])
def delete_selected_students():
    data = request.get_json()
    student_ids = data.get("ids")

    if not student_ids or not isinstance(student_ids, list):
        return jsonify({"error": "Invalid student ID list"}), 400

    conn = None
    cur = None

    try:
        conn = get_conn()
        cur = conn.cursor()

       
        cur.execute(
            "DELETE FROM students WHERE student_id = ANY(%s)",
            (student_ids,)
        )

        conn.commit()

        return jsonify({
            "message": f"{cur.rowcount} students deleted successfully!"
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    app.run(debug=True)
    
