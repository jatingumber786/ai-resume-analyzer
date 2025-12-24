# app.py

import os
from flask import Flask, render_template, request, redirect, url_for, flash

from resume_analyzer import extract_text, analyze_resume

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}

app = Flask(__name__)
app.secret_key = "change_this_secret_key"  # change to anything random
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        job_description = request.form.get("job_description", "")

        if "resume_file" not in request.files:
            flash("No file part in the request.")
            return redirect(request.url)

        file = request.files["resume_file"]

        if file.filename == "":
            flash("No file selected.")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = file.filename
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(save_path)

            resume_text = extract_text(save_path)

            if not resume_text.strip():
                flash("Could not extract text from the uploaded file. Try another file or a clearer PDF.")
                return redirect(request.url)

            analysis_result = analyze_resume(resume_text, job_description)

            # Optional: delete file after processing
            # os.remove(save_path)

            return render_template("result.html", result=analysis_result)

        else:
            flash("Unsupported file type. Please upload PDF, DOCX, or TXT.")
            return redirect(request.url)

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
