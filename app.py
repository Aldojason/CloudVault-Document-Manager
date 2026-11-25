
import os
from functools import wraps
from io import BytesIO

import boto3
from botocore.exceptions import ClientError
from flask import (
    Flask, render_template, request, jsonify,
    redirect, url_for, session, send_file, flash
)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, generate_csrf
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


app = Flask(__name__)

# Configuration
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "change-this-development-secret"
)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cloudvault.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = (
    os.environ.get("FLASK_HTTPS") == "1"
)

db = SQLAlchemy(app)
csrf = CSRFProtect(app)

BUCKET_NAME = "aldo-cloud-file-storage-2026-576738459493-ap-southeast-2-an"
s3 = boto3.client("s3")


# Database model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


with app.app_context():
    db.create_all()


# Authentication decorator
def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/") or request.path in (
                "/files", "/upload", "/search"
            ) or request.path.startswith(("/download/", "/delete/")):
                return jsonify({"error": "Please log in"}), 401

            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return wrapper


def user_prefix():
    return f"users/{session['user_id']}/"


# Registration
@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or len(password) < 8:
            flash("Enter all details. Password must be at least 8 characters.")
            return redirect(url_for("register"))

        existing = User.query.filter(
            db.or_(User.username == username, User.email == email)
        ).first()

        if existing:
            flash("Username or email already registered.")
            return redirect(url_for("register"))

        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password)
        )

        db.session.add(user)
        db.session.commit()

        flash("Account created. Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html", csrf_token=generate_csrf())


# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session.clear()
            session["user_id"] = user.id
            session["username"] = user.username
            session.permanent = True
            return redirect(url_for("home"))

        flash("Invalid email or password.")
        return redirect(url_for("login"))

    return render_template("login.html", csrf_token=generate_csrf())


# Logout
@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))


# Dashboard
@app.route("/")
@login_required
def home():
    return render_template(
        "index.html",
        username=session["username"],
        csrf_token=generate_csrf()
    )


# List user's documents
@app.route("/files")
@login_required
def list_files():
    try:
        paginator = s3.get_paginator("list_objects_v2")
        files = []

        for page in paginator.paginate(
            Bucket=BUCKET_NAME,
            Prefix=user_prefix()
        ):
            for file in page.get("Contents", []):
                files.append({
                    "filename": file["Key"].removeprefix(user_prefix()),
                    "size": file["Size"],
                    "last_modified": file["LastModified"].isoformat(),
                    "storage_class": file.get("StorageClass", "STANDARD")
                })

        return jsonify({
            "success": True,
            "total_files": len(files),
            "files": files
        })

    except ClientError:
        app.logger.exception("S3 listing failed")
        return jsonify({"success": False, "error": "Unable to list documents"}), 500


# Upload
@app.route("/upload", methods=["POST"])
@login_required
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    filename = secure_filename(file.filename or "")

    if not filename:
        return jsonify({"error": "Invalid filename"}), 400

    key = user_prefix() + filename

    try:
        s3.upload_fileobj(
            file,
            BUCKET_NAME,
            key,
            ExtraArgs={
                "ContentType": file.content_type or "application/octet-stream"
            }
        )

        return jsonify({
            "success": True,
            "message": "File uploaded successfully",
            "filename": filename
        }), 201

    except ClientError:
        app.logger.exception("S3 upload failed")
        return jsonify({"error": "Unable to upload document"}), 500


# Download
@app.route("/download/<path:filename>")
@login_required
def download_file(filename):
    filename = secure_filename(filename)

    if not filename:
        return jsonify({"error": "Invalid filename"}), 400

    try:
        result = s3.get_object(
            Bucket=BUCKET_NAME,
            Key=user_prefix() + filename
        )

        return send_file(
            BytesIO(result["Body"].read()),
            as_attachment=True,
            download_name=filename,
            mimetype=result.get("ContentType", "application/octet-stream")
        )

    except ClientError as error:
        code = error.response.get("Error", {}).get("Code")

        if code in ("NoSuchKey", "404", "NotFound"):
            return jsonify({"error": "Document not found"}), 404

        app.logger.exception("S3 download failed")
        return jsonify({"error": "Unable to download document"}), 500


# Delete
@app.route("/delete/<path:filename>", methods=["DELETE"])
@login_required
def delete_file(filename):
    filename = secure_filename(filename)

    if not filename:
        return jsonify({"error": "Invalid filename"}), 400

    try:
        s3.delete_object(
            Bucket=BUCKET_NAME,
            Key=user_prefix() + filename
        )

        return jsonify({
            "success": True,
            "message": "Document deleted",
            "filename": filename
        })

    except ClientError:
        app.logger.exception("S3 deletion failed")
        return jsonify({"error": "Unable to delete document"}), 500


# Search
@app.route("/search")
@login_required
def search_files():
    query = request.args.get("name", "").strip().lower()

    if not query:
        return jsonify({"success": True, "results": [], "total_results": 0})

    try:
        paginator = s3.get_paginator("list_objects_v2")
        results = []

        for page in paginator.paginate(
            Bucket=BUCKET_NAME,
            Prefix=user_prefix()
        ):
            for file in page.get("Contents", []):
                filename = file["Key"].removeprefix(user_prefix())

                if query in filename.lower():
                    results.append({
                        "filename": filename,
                        "size": file["Size"],
                        "last_modified": file["LastModified"].isoformat()
                    })

        return jsonify({
            "success": True,
            "total_results": len(results),
            "results": results
        })

    except ClientError:
        app.logger.exception("S3 search failed")
        return jsonify({"error": "Unable to search documents"}), 500


@app.errorhandler(413)
def file_too_large(error):
    return jsonify({"error": "File exceeds the 20 MB upload limit"}), 413


if __name__ == "__main__":
    app.run(debug=True)
