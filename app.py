from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Demo data
roles = [
    {"id": "software", "name": "Software Developer"},
    {"id": "data", "name": "Data Scientist"},
    {"id": "web", "name": "Web Developer"},
]


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/roles")
def get_roles():
    return jsonify(roles)


@app.route("/api/stats")
def get_stats():
    return jsonify({
        "total": 3,
        "average": 78,
        "best": 91,
        "top_category": "Formatting"
    })


@app.route("/api/history")
def get_history():
    return jsonify([
        {
            "id": 1,
            "filename": "resume_sample.pdf",
            "role": "Software Developer",
            "score": 82,
            "issue_count": 4,
            "created_at": "2026-10-08"
        },
        {
            "id": 2,
            "filename": "my_resume.docx",
            "role": "Data Scientist",
            "score": 74,
            "issue_count": 7,
            "created_at": "2026-10-07"
        }
    ])


@app.route("/api/analyze", methods=["POST"])
def analyze():
    filename = "Pasted Resume"

    if "file" in request.files:
        uploaded = request.files["file"]
        if uploaded.filename:
            filename = uploaded.filename

    text = request.form.get("text", "")

    # Demo result
    return jsonify({
        "filename": filename,
        "score": 82,
        "stats": {
            "word_count": len(text.split()) if text else 247,
            "severity": {
                "high": 1,
                "medium": 2,
                "low": 2
            },
            "sections_found": [
                "education",
                "skills",
                "experience",
                "projects",
                "summary"
            ],
            "keywords_matched": [
                "Python",
                "SQL",
                "Git"
            ],
            "keywords_missing": [
                "Docker",
                "AWS"
            ]
        },
        "category_scores": {
            "Grammar": 88,
            "Formatting": 76,
            "Keywords": 81,
            "Clarity": 84
        },
        "issues": [
            {
                "severity": "high",
                "category": "Grammar",
                "message": "Improve the wording of this section.",
                "line_no": 2,
                "suggestion": "Use a clearer and more professional sentence."
            },
            {
                "severity": "medium",
                "category": "Keywords",
                "message": "Some relevant technical keywords are missing.",
                "line_no": 5,
                "suggestion": "Consider adding technologies relevant to the target role."
            },
            {
                "severity": "medium",
                "category": "Clarity",
                "message": "This sentence could be more concise.",
                "line_no": 8,
                "suggestion": "Use a shorter, action-oriented statement."
            },
            {
                "severity": "low",
                "category": "Formatting",
                "message": "Consider keeping formatting consistent.",
                "line_no": 11,
                "suggestion": "Use consistent spacing and formatting."
            },
            {
                "severity": "low",
                "category": "Content",
                "message": "Add measurable results where possible.",
                "line_no": 14,
                "suggestion": "Include numbers or outcomes to strengthen the achievement."
            }
        ],
        "lines": [
            "John Doe",
            "Software Developer with experience in Python.",
            "Built several applications using Python and SQL.",
            "Worked on web development projects.",
            "Skills: Python, SQL, Git",
            "Developed projects for college.",
            "Worked with different technologies.",
            "Good communication and problem solving skills.",
            "Experience in software development.",
            "Created applications and websites.",
            "Education: Bachelor of Computer Applications",
            "Projects",
            "Resume Error Detector",
            "Improved resume quality for users.",
            "Contact: john@example.com"
        ]
    })


@app.route("/api/analysis/<int:analysis_id>")
def get_analysis(analysis_id):
    return jsonify({
        "filename": "demo_resume.pdf",
        "score": 82,
        "stats": {
            "word_count": 247,
            "severity": {
                "high": 1,
                "medium": 2,
                "low": 2
            },
            "sections_found": [
                "education",
                "skills",
                "experience",
                "projects",
                "summary"
            ],
            "keywords_matched": ["Python", "SQL", "Git"],
            "keywords_missing": ["Docker", "AWS"]
        },
        "category_scores": {
            "Grammar": 88,
            "Formatting": 76,
            "Keywords": 81,
            "Clarity": 84
        },
        "issues": [],
        "lines": ["Demo analysis"]
    })


@app.route("/api/analysis/<int:analysis_id>", methods=["DELETE"])
def delete_analysis(analysis_id):
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(debug=True)