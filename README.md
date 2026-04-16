# week04-Project

FieldOps Manager is a full-stack web application built to manage electricians, jobs, tasks, and materials for a contractor business. The system allows admins to assign work, track progress, manage inventory, and generate reports — all in real time with no static data.

#TECH STACK
Backend - Python (Flask)
Database-SQLite
Frontend- HTML5, Bootstrap 5, Chart.js
Templating -Jinja2


Week04-Project/
├── app.py              # All Flask routes
├── database.py         # DB init and connection
├── requirements.txt    # Flask dependency
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── electricians.html
│   ├── edit_electrician.html
│   ├── jobs.html
│   ├── edit_job.html
│   ├── tasks.html
│   ├── materials.html
│   ├── reports.html
│   ├── notifications.html
│   └── profile.html
└── static/
    └── css/style.css

#WEEK-04 FEATURES
Reports Module — Task completion chart, Jobs status chart, Electrician activity report with progress bars, Daily work log
Search & Filter — Search jobs by title/location, filter electricians by status, search tasks
Notifications — Pending task alerts, job deadline alerts, completed task count
UI/UX Improvements — Redesigned sidebar, stat cards, improved typography and colors
Bug Fixes — Fixed base.html comment issue, DB schema issues, template errors
