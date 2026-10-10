ResumeIQ - frontend only
templates/index.html   -> page (Flask/Jinja template)
static/style.css       -> styling
static/app.js          -> logic (calls the backend /api/* endpoints)
static/sample_resume.txt -> demo resume for the "Load sample resume" button
Needs the backend API: /api/roles, /api/analyze, /api/history, /api/analysis/<id>, /api/stats
