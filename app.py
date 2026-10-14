"""Flask backend - Resume Error Detector and Suggestion System (Team: Future Coders)."""
from flask import Flask, request, jsonify, render_template
from database import get_db, init_db, load_rules
from extractor import extract_text
from analyzer import analyze

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB
init_db()

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/api/roles")
def roles():
    conn = get_db()
    data = [dict(r) for r in conn.execute("SELECT id, name FROM job_roles ORDER BY id")]
    conn.close()
    return jsonify(data)

@app.post("/api/analyze")
def api_analyze():
    role_id = request.form.get("role_id", type=int)
    filename, text = "Pasted text", request.form.get("text", "")
    f = request.files.get("file")
    try:
        if f and f.filename:
            filename, text = f.filename, extract_text(f)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    if len(text.strip()) < 30:
        return jsonify({"error": "Could not read enough text. Upload a text-based PDF/DOCX/TXT or paste your resume."}), 400

    conn = get_db()
    result = analyze(text, load_rules(conn, role_id))
    cur = conn.execute(
        "INSERT INTO analyses(filename, role_id, score, word_count, issue_count, resume_text) VALUES (?,?,?,?,?,?)",
        (filename, role_id, result["score"], result["stats"]["word_count"], len(result["issues"]), text))
    aid = cur.lastrowid
    conn.executemany(
        "INSERT INTO issues(analysis_id, category, severity, line_no, message, suggestion) VALUES (?,?,?,?,?,?)",
        [(aid, i["category"], i["severity"], i["line_no"], i["message"], i["suggestion"]) for i in result["issues"]])
    conn.commit(); conn.close()
    result.update(id=aid, filename=filename)
    return jsonify(result)

@app.get("/api/history")
def history():
    conn = get_db()
    rows = conn.execute("""SELECT a.id, a.filename, a.score, a.word_count, a.issue_count, a.created_at,
                                  COALESCE(r.name,'-') AS role
                           FROM analyses a LEFT JOIN job_roles r ON r.id=a.role_id
                           ORDER BY a.id DESC LIMIT 20""").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.get("/api/analysis/<int:aid>")
def get_analysis(aid):
    conn = get_db()
    a = conn.execute("SELECT * FROM analyses WHERE id=?", (aid,)).fetchone()
    if not a:
        conn.close()
        return jsonify({"error": "Not found"}), 404
    rules = load_rules(conn, a["role_id"])
    conn.close()
    result = analyze(a["resume_text"], rules)   # re-run: deterministic & always up to date
    result.update(id=aid, filename=a["filename"])
    return jsonify(result)

@app.delete("/api/analysis/<int:aid>")
def delete_analysis(aid):
    conn = get_db()
    conn.execute("DELETE FROM analyses WHERE id=?", (aid,))
    conn.commit(); conn.close()
    return jsonify({"ok": True})

@app.get("/api/stats")
def stats():
    conn = get_db()
    r = conn.execute("SELECT COUNT(*) n, COALESCE(ROUND(AVG(score)),0) avg, COALESCE(MAX(score),0) best FROM analyses").fetchone()
    top = conn.execute("""SELECT category, COUNT(*) c FROM issues GROUP BY category ORDER BY c DESC LIMIT 1""").fetchone()
    conn.close()
    return jsonify({"total": r["n"], "average": r["avg"], "best": r["best"], "top_category": top["category"] if top else "-"})

@app.get("/api/team")
def team():
    conn = get_db()
    data = [dict(r) for r in conn.execute("SELECT * FROM team ORDER BY id")]
    conn.close()
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
