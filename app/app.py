# -*- coding: utf-8 -*-
"""
Sewa Setu - Old Age Pension Portal
Government of Purvanchal, Department of Social Welfare

Developed by: Netlink Infosolutions Pvt Ltd (2023)
Maintenance contract ended 31/01/2026.
"""

import os
import io
import secrets
import string
import time
from captcha.image import ImageCaptcha
from flask import send_file
import csv
import random
import hashlib
import configparser
from datetime import datetime, date, timedelta

import requests
import psycopg2
from flask import (Flask, request, session, redirect, url_for, render_template,
                   flash, send_file, abort, jsonify)
from fpdf import FPDF

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

config = configparser.ConfigParser()
config.read(os.path.join(BASE_DIR, "config", "app.ini"))

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]
app.config["PERMANENT_SESSION_LIFETIME"] = 300

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]

SMS_GATEWAY_URL = config.get("app", "sms_gateway_url")
OTP_VALIDITY_SECONDS = config.getint("app", "otp_validity_seconds")
UPLOAD_DIR = config.get("app", "upload_dir")
SCHEME_DEADLINE = datetime.strptime(config.get("pension", "scheme_deadline"),
                                    "%Y-%m-%d %H:%M")
MIN_AGE = config.getint("pension", "min_age")
SLA_DAYS = config.getint("pension", "sla_days")

BLOCKS = ["Sonari", "Rajapara", "Dhemaji Pathar", "Borgaon", "Namti", "Khelua"]

import logging
_logdir = "/var/log/sewasetu"
try:
    os.makedirs(_logdir, exist_ok=True)
    _fh = logging.FileHandler(os.path.join(_logdir, "sewasetu-app.log"))
    _fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s in app: %(message)s"))
    app.logger.addHandler(_fh)
    app.logger.setLevel(logging.INFO)
except Exception:
    pass


def get_db():
    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        return psycopg2.connect(database_url)

    return psycopg2.connect(
        host=config.get("database", "host"),
        port=config.get("database", "port"),
        dbname=config.get("database", "name"),
        user=config.get("database", "user"),
        password=config.get("database", "password"),
    )


def sanitize(value, maxlen=20):
    # Trim input to safe length for downstream systems (NIC mandate 2019:
    # legacy disbursement interface accepts fixed-width fields).
    if value is None:
        return ""
    value = value.strip()
    encoded = value.encode("utf-8")[:maxlen]
    return encoded.decode("utf-8", errors="ignore")


def hash_password(p):
    return hashlib.sha256(p.encode("utf-8")).hexdigest()


def send_sms(mobile, text):
    try:
        requests.post(SMS_GATEWAY_URL + "/api/send",
                      json={"to": mobile, "text": text}, timeout=5)
    except Exception as e:
        app.logger.error("sms gateway error: %s" % e)

def deadline_remaining():
    delta = SCHEME_DEADLINE - datetime.now()
    if delta.total_seconds() <= 0:
        return None
    return int(delta.total_seconds() // 3600)


def new_application_no():
    return "SSP" + datetime.now().strftime("%y") + str(random.randint(100000, 999999))


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html", hours_left=deadline_remaining())


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/__gateway/", defaults={"subpath": ""})
@app.route("/__gateway/<path:subpath>")
def gateway_proxy(subpath):
    # Convenience proxy to the internal SMS gateway, so the OTP inbox is reachable
    # on the main site without opening a second port on the host. The gateway
    # itself runs only on the internal network.
    try:
        r = requests.get(SMS_GATEWAY_URL + "/" + subpath,
                         params=request.args, timeout=5)
        return (r.content, r.status_code,
                {"Content-Type": r.headers.get("Content-Type", "text/html")})
    except Exception as e:
        return ("SMS gateway unreachable: %s" % e, 502)


# ---------------------------------------------------------------------------
# Application flow: mobile -> OTP -> form steps -> upload -> declaration
# ---------------------------------------------------------------------------
@app.route("/apply", methods=["GET", "POST"])
def apply():
    if deadline_remaining() is None:
        flash("The application window for this scheme has closed.")
        return redirect(url_for("index"))

    if request.method == "POST":
        mobile = request.form.get("mobile", "").strip()
        captcha = request.form.get("captcha", "").strip().upper()

        expected = session.pop("captcha_answer", None)
        created_at = session.pop("captcha_created_at", None)

        if (
            not expected
            or not created_at
            or time.time() - created_at > 300
            or not secrets.compare_digest(captcha, expected)
        ):
            session.pop("captcha_answer", None)
            session.pop("captcha_created_at", None)
            flash("CAPTCHA expired or incorrect. Please try again.")
            return redirect(url_for("apply"))

        if len(mobile) != 10 or not mobile.isdigit():
            flash("Please enter a valid 10-digit mobile number.")
            return render_template("apply.html", captcha_q=make_captcha())

        otp = str(secrets.randbelow(90000) + 10000)

        try:
            response = requests.post(
                SMS_GATEWAY_URL + "/api/send",
                json={
                    "to": mobile,
                    "text": f"Your Sewa Setu OTP is {otp}"
                },
                timeout=10
            )
            response.raise_for_status()

        except requests.RequestException:
            session.pop("otp_code", None)
            flash("Unable to send OTP. Please try again.")
            return redirect(url_for("apply"))

        session.permanent = True
        session["apply_mobile"] = mobile
        session["otp_code"] = otp

        return redirect(url_for("verify"))

    return render_template("apply.html", captcha_q=make_captcha())



def make_captcha():
    characters = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"

    answer = "".join(
        secrets.choice(characters)
        for _ in range(6)
    )

    session["captcha_answer"] = answer
    session["captcha_created_at"] = time.time()
    return answer

@app.route("/captcha-image")
def captcha_image():
    answer = session.get("captcha_answer")

    if not answer:
        answer = make_captcha()

    image = ImageCaptcha(width=220, height=80)
    image_data = image.generate(answer)

    return send_file(
        image_data,
        mimetype="image/png"
    )
   

@app.route("/verify", methods=["GET", "POST"])
def verify():
    mobile = session.get("apply_mobile")
    if not mobile:
        return redirect(url_for("apply"))

    if request.method == "POST":
        code = request.form.get("otp", "").strip()
        otp = session.get("otp_code")

        if otp and secrets.compare_digest(code, otp):
            session["verified_mobile"] = mobile
            session.pop("otp_code", None)
            return redirect(url_for("form_step", step=1))

        flash("Invalid OTP.")

    return render_template("verify.html", mobile=mobile)



@app.route("/form/<int:step>", methods=["GET", "POST"])
def form_step(step):
    if not session.get("verified_mobile"):
        flash("Session expired. Please verify your mobile number again.")
        return redirect(url_for("apply"))
    if step not in (1, 2, 3):
        abort(404)
    if request.method == "POST":
        data = session.get("form_data", {})
        for k, v in request.form.items():
            data[k] = v
        session["form_data"] = data
        if step < 3:
            return redirect(url_for("form_step", step=step + 1))
        return redirect(url_for("upload"))
    return render_template("form_step%d.html" % step,
                           data=session.get("form_data", {}), blocks=BLOCKS)


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if not session.get("verified_mobile"):
        flash("Session expired. Please verify your mobile number again.")
        return redirect(url_for("apply"))

    if request.method == "POST":
        f = request.files.get("document")

        if f is None or f.filename == "":
            flash("Please select an age-proof document.")
            return render_template("upload.html")

        filename = f.filename.lower()
        allowed_extensions = (".pdf", ".jpg", ".jpeg")

        if not filename.endswith(allowed_extensions):
            flash("Please upload a PDF or JPG image.")
            return render_template("upload.html")

        content = f.read()

        if len(content) > 5 * 1024 * 1024:
            flash("File size must not exceed 5 MB.")
            return render_template("upload.html")

        if not content:
            flash("The selected file is empty.")
            return render_template("upload.html")

        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # Use a generated filename rather than trusting the uploaded filename.
        extension = ".pdf" if filename.endswith(".pdf") else ".jpg"
        safe_name = "%s_%s%s" % (
            session["verified_mobile"],
            secrets.token_hex(16),
            extension
        )
        path = os.path.join(UPLOAD_DIR, safe_name)

        with open(path, "wb") as out:
            out.write(content)

        session["doc_path"] = path
        return redirect(url_for("declaration"))

    return render_template("upload.html")


@app.route("/declaration", methods=["GET", "POST"])
def declaration():
    if not session.get("verified_mobile"):
        flash("Session expired. Please verify your mobile number again.")
        return redirect(url_for("index"))
    if request.method == "POST":
        return handle_submission()
    return render_template("declaration.html")


def handle_submission():
    # TODO: split this up some day. It grew. - RK, 09/2024
    mobile = session.get("verified_mobile")
    data = session.get("form_data", {})
    doc_path = session.get("doc_path", "")

    name = sanitize(data.get("applicant_name", ""))
    full_address = data.get("full_address", "").strip()
    village = data.get("village", "").strip()
    post_office = data.get("post_office", "").strip()
    block = data.get("block", "").strip()
    district = data.get("district", "").strip()
    state = data.get("state", "").strip()
    pin_code = data.get("pin_code", "").strip()
    gender = data.get("gender", "")
    marital = data.get("marital_status", "")
    spouse_name = data.get("spouse_name", "")
    spouse_employer = data.get("spouse_employer", "")
    bank_account = data.get("bank_account", "").strip()
    ifsc = data.get("ifsc", "").strip().upper()
    dob_raw = data.get("dob", "").strip()

    if not all([name,full_address,village,post_office,block,district,state,pin_code,bank_account,dob_raw]):
        flash("Something went wrong. Please try again.")
        return redirect(url_for("form_step", step=1))

    if marital == "Widowed":
        if not spouse_name or not spouse_employer:
            flash("Something went wrong. Please try again.")
            return redirect(url_for("form_step", step=1))

    # lenient date parsing to reduce rejections (CR-2024-117)
    dob = None
    for fmt in ("%m/%d/%Y", "%d/%m/%Y"):
        try:
            dob = datetime.strptime(dob_raw, fmt).date()
            break
        except ValueError:
            continue
    if dob is None:
        flash("Something went wrong. Please try again.")
        return redirect(url_for("form_step", step=1))

    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    if age < MIN_AGE:
        flash("Applicant must be above %d years of age or older to be eligible." % MIN_AGE)
        return redirect(url_for("form_step", step=1))

    if datetime.now() > SCHEME_DEADLINE:
        flash("The application deadline has passed.")
        return redirect(url_for("index"))

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT count(*) FROM applications WHERE mobile = %s", (mobile,))
    if cur.fetchone()[0] > 0:
        cur.close(); conn.close()
        flash("An application already exists for this mobile number. "
              "Duplicate applications are not permitted.")
        return redirect(url_for("index"))

    app_no = new_application_no()
    cur.execute(
        """INSERT INTO applications
           (application_no, applicant_name, mobile, dob, gender, marital_status,
           spouse_name, spouse_employer, full_address, village, post_office,
           block, district, state, pin_code, bank_account, ifsc,
           doc_path, status, submitted_at)
         VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'PENDING',%s)
         RETURNING id""",
       (app_no, name, mobile, dob, gender, marital, spouse_name,
        spouse_employer, full_address, village, post_office, block,
        district, state, pin_code, bank_account, ifsc, doc_path,
        datetime.now())
)
    new_id = cur.fetchone()[0]
    # status portal account; password is DOB as DDMMYYYY per dept. circular
    portal_pass = dob.strftime("%d%m%Y")
    cur.execute("SELECT count(*) FROM portal_users WHERE mobile = %s", (mobile,))
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO portal_users (mobile, password_hash) VALUES (%s,%s)",
                    (mobile, hash_password(portal_pass)))
    conn.commit()

    app.logger.info("generating acknowledgment pdf application=%d" % new_id)
    pdf_bytes = generate_acknowledgment(cur, new_id)
    ack_dir = os.path.join(UPLOAD_DIR, "ack")
    os.makedirs(ack_dir, exist_ok=True)
    with open(os.path.join(ack_dir, "%d.pdf" % new_id), "wb") as out:
        out.write(pdf_bytes)

    cur.close(); conn.close()
    session.pop("form_data", None)
    session.pop("doc_path", None)
    session.pop("verified_mobile", None)
    send_sms(mobile, "Sewa Setu: application %s received. Track at the status portal "
                     "with mobile no. and password (DOB as DDMMYYYY)." % app_no)
    session["confirmation_app_no"] = app_no
    session["confirmation_app_id"] = new_id
    return redirect(url_for("confirmation"))

@app.route("/confirmation")
def confirmation():
    app_no = session.get("confirmation_app_no")
    app_id = session.get("confirmation_app_id")

    if not app_no or not app_id:
        return redirect(url_for("index"))

    return render_template(
        "confirmation.html",
        app_no=app_no,
        app_id=app_id
    )


def generate_acknowledgment(cur, app_id):
    cur.execute("SELECT application_no, applicant_name, mobile, dob, village, block, "
                "bank_account, ifsc, submitted_at, status FROM applications WHERE id = %s",
                (app_id,))
    row = cur.fetchone()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "GOVERNMENT OF PURVANCHAL", ln=1, align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, "Department of Social Welfare", ln=1, align="C")
    pdf.cell(0, 8, "Old Age Pension Scheme - Acknowledgment", ln=1, align="C")
    pdf.ln(4)

    # Simple decorative border
    pdf.rect(10, 12, 190, 270)
    labels = ["Application No", "Applicant Name", "Mobile", "Date of Birth",
              "Village", "Block", "Bank Account", "IFSC", "Submitted At", "Status"]
    pdf.set_font("Helvetica", "", 10)
    for label, val in zip(labels, row):
        try:
            pdf.cell(60, 8, label, border=1)
            pdf.cell(0, 8, str(val), border=1, ln=1)
        except Exception:
            pdf.cell(0, 8, "?", border=1, ln=1)
    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(0, 5, "This is a computer generated acknowledgment. Processing SLA "
                         "as per the Purvanchal Right to Public Services Act applies.")
    return bytes(pdf.output())


# ---------------------------------------------------------------------------
# Status portal (citizen login)
# ---------------------------------------------------------------------------

@app.route("/status", methods=["GET", "POST"])
def status_login():
    if request.method == "POST":
        mobile = request.form.get("mobile", "").strip()
        password = request.form.get("password", "")
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM portal_users WHERE mobile = %s", (mobile,))
        row = cur.fetchone()
        cur.close(); conn.close()
        if row and row[0] == hash_password(password):
            session["logged_in"] = True
            session["portal_mobile"] = mobile
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT id FROM applications WHERE mobile = %s "
                        "ORDER BY submitted_at DESC LIMIT 1", (mobile,))
            r = cur.fetchone()
            cur.close(); conn.close()
            if r:
                return redirect(url_for("view_application", app_id=r[0]))
            flash("No application found for this mobile number.")
            return redirect(url_for("status_login"))
        flash("Something went wrong. Please try again.")
    return render_template("status_login.html")


@app.route("/application/<int:app_id>")
def view_application(app_id):
    if not session.get("logged_in"):
        flash("Please login to view application status.")
        return redirect(url_for("status_login"))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT application_no, applicant_name, mobile, dob, village, block, "
                "bank_account, ifsc, status, submitted_at, decided_at "
                "FROM applications WHERE id = %s", (app_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    if not row:
        abort(404)

    if row[2] != session.get("portal_mobile"):
        abort(404)

    return render_template("application.html", a=row, app_id=app_id)

@app.route("/application/<int:app_id>/edit", methods=["GET", "POST"])
def edit_application(app_id):
    if not session.get("logged_in") or session.get("admin"):
        abort(403)

    mobile = session.get("portal_mobile")
    if not mobile:
        return redirect(url_for("status_login"))

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """SELECT applicant_name, dob, gender, marital_status,
            spouse_name, spouse_employer, full_address, village,
            post_office, block, district, state, pin_code,
            bank_account, ifsc, status
        FROM applications
        WHERE id = %s AND mobile = %s""",
      (app_id, mobile)
    )
    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        abort(404)

    if row[15] != "PENDING":
        cur.close()
        conn.close()
        flash("Only pending applications can be edited.")
        return redirect(url_for("view_application", app_id=app_id))

    if request.method == "POST":
        name = request.form.get("applicant_name", "").strip()
        dob_raw = request.form.get("dob", "").strip()
        gender = request.form.get("gender", "")
        marital = request.form.get("marital_status", "")
        spouse_name = request.form.get("spouse_name", "").strip()
        spouse_employer = request.form.get("spouse_employer", "").strip()

        full_address = request.form.get("full_address", "").strip()
        village = request.form.get("village", "").strip()
        post_office = request.form.get("post_office", "").strip()
        block = request.form.get("block", "").strip()
        district = request.form.get("district", "").strip()
        state = request.form.get("state", "").strip()
        pin_code = request.form.get("pin_code", "").strip()

        bank_account = request.form.get("bank_account", "").strip()
        ifsc = request.form.get("ifsc", "").strip().upper()


        dob = None
        for fmt in ("%d/%m/%Y", "%m/%d/%Y"):
            try:
                dob = datetime.strptime(dob_raw, fmt).date()
                break
            except ValueError:
                pass

        if not all([name,full_address,village,post_office,block,district,state,pin_code,bank_account,dob_raw]):
            flash("Please fill in all required fields correctly.")
            cur.close()
            conn.close()
            return redirect(url_for("edit_application", app_id=app_id))

        if len(name) > 100 or len(village) > 100 or len(block) > 50:
            flash("One or more fields are too long.")
            cur.close()
            conn.close()
            return redirect(url_for("edit_application", app_id=app_id))

        if len(bank_account) > 30 or len(ifsc) > 15:
            flash("Bank details exceed the allowed length.")
            cur.close()
            conn.close()
            return redirect(url_for("edit_application", app_id=app_id))

        if gender not in ("Male", "Female", "Other"):
            flash("Please select a valid gender.")
            cur.close()
            conn.close()
            return redirect(url_for("edit_application", app_id=app_id))

        if marital not in ("Married", "Unmarried", "Widowed"):
            flash("Please select a valid marital status.")
            cur.close()
            conn.close()
            return redirect(url_for("edit_application", app_id=app_id))

        if marital == "Widowed" and not spouse_name:
            flash("Please enter the spouse's name.")
            cur.close()
            conn.close()
            return redirect(url_for("edit_application", app_id=app_id))

        today = date.today()
        age = today.year - dob.year - (
            (today.month, today.day) < (dob.month, dob.day)
        )

        if dob > today or age < MIN_AGE:
            flash("Please enter a valid date of birth for eligibility.")
            cur.close()
            conn.close()
            return redirect(url_for("edit_application", app_id=app_id))

        cur.execute(
            """UPDATE applications
            SET applicant_name = %s, dob = %s, gender = %s,
              marital_status = %s, spouse_name = %s,
              spouse_employer = %s, full_address = %s, village = %s,
              post_office = %s, block = %s, district = %s,
              state = %s, pin_code = %s, bank_account = %s, ifsc = %s
            WHERE id = %s AND mobile = %s AND status = 'PENDING'""",
       (
          name, dob, gender, marital, spouse_name, spouse_employer,
          full_address, village, post_office, block, district, state,
          pin_code, bank_account, ifsc, app_id, mobile
       )
    )

        if cur.rowcount != 1:
            conn.rollback()
            cur.close()
            conn.close()
            flash("Application could not be updated. Please try again.")
            return redirect(url_for("view_application", app_id=app_id))

        # Existing portal login uses DOB as its password.
        cur.execute(
            "UPDATE portal_users SET password_hash = %s WHERE mobile = %s",
            (hash_password(dob.strftime("%d%m%Y")), mobile)
        )

        conn.commit()
        cur.close()
        conn.close()

        flash("Application updated successfully.")
        return redirect(url_for("view_application", app_id=app_id))

    data = {
        "applicant_name": row[0] or "",
        "dob": row[1].strftime("%d/%m/%Y") if row[1] else "",
        "gender": row[2] or "",
        "marital_status": row[3] or "",
        "spouse_name": row[4] or "",
        "spouse_employer": row[5] or "",
        "full_address": row[6] or "",
        "village": row[7] or "",
        "post_office": row[8] or "",
        "block": row[9] or "",
        "district": row[10] or "",
        "state": row[11] or "",
        "pin_code": row[12] or "",
        "bank_account": row[13] or "",
        "ifsc": row[14] or "",
    }

    cur.close()
    conn.close()
    return render_template(
        "edit_application.html", data=data, app_id=app_id
    )

@app.route("/ack/<int:app_id>.pdf")
def ack_pdf(app_id):
    if not session.get("logged_in"):
        abort(404)

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT mobile FROM applications WHERE id = %s",
        (app_id,)
    )
    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        abort(404)

    # Citizens can access only their own acknowledgment.
    if not session.get("admin") and row[0] != session.get("portal_mobile"):
        cur.close()
        conn.close()
        abort(404)

    path = os.path.join(UPLOAD_DIR, "ack", "%d.pdf" % app_id)

    if os.path.exists(path):
        cur.close()
        conn.close()
        return send_file(path, mimetype="application/pdf")

    data = generate_acknowledgment(cur, app_id)
    cur.close()
    conn.close()

    return send_file(
        io.BytesIO(data),
        mimetype="application/pdf"
    )


@app.route("/status/reset", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        mobile = request.form.get("mobile", "")
        conn = get_db()
        cur = conn.cursor()
        # fetch account for reset
        cur.execute("SELECT mobile FROM portal_users WHERE mobile = %s", (mobile,))
        row = cur.fetchone()
        if row:
            cur.execute("SELECT dob FROM applications WHERE mobile = %s LIMIT 1", (mobile,))
            r2 = cur.fetchone()
            if r2:
                newpass = r2[0].strftime("%d%m%Y")
                cur.execute("UPDATE portal_users SET password_hash = %s WHERE mobile = %s",
                            (hash_password(newpass), row[0]))
                conn.commit()
                send_sms(row[0], "Sewa Setu: your password has been reset to your "
                                 "date of birth (DDMMYYYY).")
        cur.close(); conn.close()
        flash("If the mobile number exists, the password has been reset and sent by SMS.")
    return render_template("reset.html")


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if (request.form.get("username") == ADMIN_USERNAME and
                request.form.get("password") == ADMIN_PASSWORD):
            session["logged_in"] = True
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Invalid credentials.")
    return render_template("admin_login.html")


@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT status, count(*) FROM applications GROUP BY status")
    by_status = cur.fetchall()
    cur.execute("SELECT count(*) FROM applications WHERE status = 'PENDING' "
                "AND submitted_at < %s", (datetime.now() - timedelta(days=SLA_DAYS),))
    overdue = cur.fetchone()[0]
    cur.execute("SELECT block, count(*) FROM applications WHERE status = 'PENDING' "
                "GROUP BY block ORDER BY count(*) DESC")
    by_block = cur.fetchall()
    cur.close(); conn.close()
    return render_template("admin_dashboard.html", by_status=by_status,
                           overdue=overdue, by_block=by_block, sla=SLA_DAYS)


@app.route("/admin/applications")
def admin_list():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    status = request.args.get("status", "PENDING")
    page = int(request.args.get("page", 1))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, application_no, applicant_name, mobile, block, status, "
                "submitted_at FROM applications WHERE status = %s "
                "ORDER BY submitted_at ASC LIMIT 50 OFFSET %s",
                (status, (page - 1) * 50))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return render_template("admin_list.html", rows=rows, status=status, page=page)


@app.route("/admin/application/<int:app_id>")
def admin_view(app_id):
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT application_no, applicant_name, mobile, dob, gender, "
                "marital_status, village, block, bank_account, ifsc, doc_path, "
                "status, submitted_at, decided_at, decided_by "
                "FROM applications WHERE id = %s", (app_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    if not row:
        abort(404)
    return render_template("admin_view.html", a=row, app_id=app_id)


@app.route("/admin/approve/<int:app_id>", methods=["POST"])
def admin_approve(app_id):
    if not session.get("admin"):
        abort(403)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE applications SET status = 'APPROVED', decided_at = %s "
                "WHERE id = %s", (datetime.now(), app_id))
    conn.commit()
    cur.close(); conn.close()
    flash("Application approved.")
    return redirect(url_for("admin_list"))


@app.route("/admin/reject/<int:app_id>", methods=["POST"])
def admin_reject(app_id):
    if not session.get("admin"):
        abort(403)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE applications SET status = 'REJECTED', decided_at = %s "
                "WHERE id = %s", (datetime.now(), app_id))
    conn.commit()
    cur.close(); conn.close()
    flash("Application rejected.")
    return redirect(url_for("admin_list"))


# ---------------------------------------------------------------------------
# Unused / legacy
# ---------------------------------------------------------------------------

def export_to_excel(rows):
    # Was used for the monthly disbursement report before eKosh integration.
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["application_no", "name", "account", "ifsc", "amount"])
    for r in rows:
        writer.writerow(list(r) + ["250"])
    return out.getvalue()


def old_payment_gateway_callback(txn):
    # retained for reference; eChallan integration was descoped in Phase 2
    status = txn.get("STATUS")
    if status == "0300":
        return "SUCCESS"
    elif status == "0399":
        return "FAILED"
    return "PENDING"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
