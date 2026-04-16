from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import init_db, get_db
import hashlib
from datetime import date

app = Flask(__name__)
app.secret_key = 'fieldops_secret'
init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def get_notifications():
    db = get_db()
    notes = []
    # New tasks assigned (Pending)
    new_tasks = db.execute("SELECT COUNT(*) FROM tasks WHERE status='Pending'").fetchone()[0]
    if new_tasks > 0:
        notes.append({'type': 'info', 'msg': f'{new_tasks} task(s) are Pending'})
    # Completed tasks
    done = db.execute("SELECT COUNT(*) FROM tasks WHERE status='Completed'").fetchone()[0]
    if done > 0:
        notes.append({'type': 'success', 'msg': f'{done} task(s) completed'})
    # Deadline alerts - jobs whose deadline is today or past
    today = date.today().isoformat()
    overdue = db.execute(
        "SELECT COUNT(*) FROM jobs WHERE deadline <= ? AND status != 'Completed'",
        (today,)
    ).fetchone()[0]
    if overdue > 0:
        notes.append({'type': 'danger', 'msg': f'{overdue} job(s) have passed or reached deadline!'})
    db.close()
    return notes

# ─── AUTH ────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = hash_password(request.form['password'])
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
        db.close()
        if user and user['password'] == password:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            return redirect(url_for('dashboard'))
        flash('Wrong email or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email'].strip().lower()
        role = request.form['role']
        password = hash_password(request.form['password'])
        db = get_db()
        try:
            db.execute('INSERT INTO users (name,phone,email,role,password) VALUES (?,?,?,?,?)',
                       (name, phone, email, role, password))
            db.commit()
            flash('Registered! Please login.')
            return redirect(url_for('login'))
        except:
            flash('Email already exists.')
        finally:
            db.close()
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─── DASHBOARD ───────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    elec   = db.execute('SELECT COUNT(*) FROM electricians').fetchone()[0]
    jobs   = db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
    tasks  = db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0]
    done   = db.execute("SELECT COUNT(*) FROM tasks WHERE status='Completed'").fetchone()[0]
    mats   = db.execute('SELECT COUNT(*) FROM materials').fetchone()[0]
    recent = db.execute('SELECT * FROM activity ORDER BY id DESC LIMIT 5').fetchall()
    db.close()
    notifications = get_notifications()
    return render_template('dashboard.html',
        electricians=elec, jobs=jobs, tasks=tasks,
        completed=done, materials=mats, recent=recent,
        notifications=notifications)

# ─── ELECTRICIANS ────────────────────────────────────────

@app.route('/electricians')
@login_required
def electricians():
    db = get_db()
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', 'All')
    query = 'SELECT * FROM electricians WHERE 1=1'
    params = []
    if search:
        query += ' AND (name LIKE ? OR phone LIKE ? OR specialization LIKE ?)'
        params += [f'%{search}%', f'%{search}%', f'%{search}%']
    if status_filter != 'All':
        query += ' AND status=?'
        params.append(status_filter)
    data = db.execute(query, params).fetchall()
    db.close()
    return render_template('electricians.html', electricians=data,
                           search=search, status_filter=status_filter)

@app.route('/electricians/add', methods=['POST'])
@login_required
def add_electrician():
    name           = request.form['name']
    phone          = request.form['phone']
    email          = request.form.get('email', '')
    specialization = request.form.get('specialization', '')
    db = get_db()
    db.execute('INSERT INTO electricians (name, phone, email, specialization) VALUES (?,?,?,?)',
               (name, phone, email, specialization))
    db.execute("INSERT INTO activity (message) VALUES (?)", (f"Electrician '{name}' added",))
    db.commit()
    db.close()
    return redirect(url_for('electricians'))

@app.route('/electricians/edit/<int:eid>', methods=['GET', 'POST'])
@login_required
def edit_electrician(eid):
    db = get_db()
    if request.method == 'POST':
        name           = request.form['name']
        phone          = request.form['phone']
        email          = request.form.get('email', '')
        specialization = request.form.get('specialization', '')
        status         = request.form['status']
        db.execute('''UPDATE electricians SET name=?, phone=?, email=?, specialization=?, status=?
                      WHERE id=?''', (name, phone, email, specialization, status, eid))
        db.execute("INSERT INTO activity (message) VALUES (?)", (f"Electrician '{name}' updated",))
        db.commit()
        db.close()
        return redirect(url_for('electricians'))
    electrician = db.execute('SELECT * FROM electricians WHERE id=?', (eid,)).fetchone()
    db.close()
    return render_template('edit_electrician.html', electrician=electrician)

@app.route('/electricians/delete/<int:eid>')
@login_required
def delete_electrician(eid):
    db = get_db()
    name = db.execute('SELECT name FROM electricians WHERE id=?', (eid,)).fetchone()['name']
    db.execute('DELETE FROM electricians WHERE id=?', (eid,))
    db.execute("INSERT INTO activity (message) VALUES (?)", (f"Electrician '{name}' deleted",))
    db.commit()
    db.close()
    return redirect(url_for('electricians'))

# ─── JOBS ────────────────────────────────────────────────

@app.route('/jobs')
@login_required
def jobs():
    db = get_db()
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', 'All')
    query = '''SELECT jobs.*, electricians.name AS electrician_name
               FROM jobs LEFT JOIN electricians ON jobs.electrician_id = electricians.id
               WHERE 1=1'''
    params = []
    if search:
        query += ' AND (jobs.title LIKE ? OR jobs.location LIKE ?)'
        params += [f'%{search}%', f'%{search}%']
    if status_filter != 'All':
        query += ' AND jobs.status=?'
        params.append(status_filter)
    data = db.execute(query, params).fetchall()
    electricians_list = db.execute('SELECT * FROM electricians').fetchall()
    db.close()
    return render_template('jobs.html', jobs=data, electricians=electricians_list,
                           search=search, status_filter=status_filter)

@app.route('/jobs/add', methods=['POST'])
@login_required
def add_job():
    title          = request.form['title']
    location       = request.form['location']
    deadline       = request.form['deadline']
    electrician_id = request.form.get('electrician_id') or None
    db = get_db()
    db.execute('INSERT INTO jobs (title, location, deadline, electrician_id) VALUES (?,?,?,?)',
               (title, location, deadline, electrician_id))
    db.execute("INSERT INTO activity (message) VALUES (?)", (f"Job '{title}' created",))
    db.commit()
    db.close()
    return redirect(url_for('jobs'))

@app.route('/jobs/edit/<int:jid>', methods=['GET', 'POST'])
@login_required
def edit_job(jid):
    db = get_db()
    if request.method == 'POST':
        title          = request.form['title']
        location       = request.form['location']
        deadline       = request.form['deadline']
        electrician_id = request.form.get('electrician_id') or None
        status         = request.form['status']
        db.execute('''UPDATE jobs SET title=?, location=?, deadline=?,
                      electrician_id=?, status=? WHERE id=?''',
                   (title, location, deadline, electrician_id, status, jid))
        db.execute("INSERT INTO activity (message) VALUES (?)", (f"Job '{title}' updated",))
        db.commit()
        db.close()
        return redirect(url_for('jobs'))
    job = db.execute('SELECT * FROM jobs WHERE id=?', (jid,)).fetchone()
    electricians_list = db.execute('SELECT * FROM electricians').fetchall()
    db.close()
    return render_template('edit_job.html', job=job, electricians=electricians_list)

@app.route('/jobs/delete/<int:jid>')
@login_required
def delete_job(jid):
    db = get_db()
    title = db.execute('SELECT title FROM jobs WHERE id=?', (jid,)).fetchone()['title']
    db.execute('DELETE FROM jobs WHERE id=?', (jid,))
    db.execute("INSERT INTO activity (message) VALUES (?)", (f"Job '{title}' deleted",))
    db.commit()
    db.close()
    return redirect(url_for('jobs'))

@app.route('/jobs/status/<int:jid>', methods=['POST'])
@login_required
def update_job_status(jid):
    status = request.form['status']
    db = get_db()
    db.execute('UPDATE jobs SET status=? WHERE id=?', (status, jid))
    db.commit()
    db.close()
    return redirect(url_for('jobs'))

# ─── TASKS ───────────────────────────────────────────────

@app.route('/tasks')
@login_required
def tasks():
    db = get_db()
    status_filter = request.args.get('status', 'All')
    search = request.args.get('search', '').strip()
    query = '''SELECT tasks.*, jobs.title AS job_title, electricians.name AS electrician_name
               FROM tasks
               LEFT JOIN jobs ON tasks.job_id = jobs.id
               LEFT JOIN electricians ON tasks.electrician_id = electricians.id
               WHERE 1=1'''
    params = []
    if status_filter != 'All':
        query += ' AND tasks.status=?'
        params.append(status_filter)
    if search:
        query += ' AND tasks.task LIKE ?'
        params.append(f'%{search}%')
    data = db.execute(query, params).fetchall()
    jobs_list         = db.execute('SELECT * FROM jobs').fetchall()
    electricians_list = db.execute('SELECT * FROM electricians').fetchall()
    db.close()
    return render_template('tasks.html', tasks=data,
                           jobs=jobs_list, electricians=electricians_list,
                           status_filter=status_filter, search=search)

@app.route('/tasks/add', methods=['POST'])
@login_required
def add_task():
    task           = request.form['task']
    job_id         = request.form.get('job_id') or None
    electrician_id = request.form.get('electrician_id') or None
    status         = request.form.get('status', 'Pending')
    db = get_db()
    db.execute('INSERT INTO tasks (task, job_id, electrician_id, status) VALUES (?,?,?,?)',
               (task, job_id, electrician_id, status))
    db.execute("INSERT INTO activity (message) VALUES (?)", (f"Task '{task}' assigned",))
    db.commit()
    db.close()
    return redirect(url_for('tasks'))

@app.route('/tasks/update_status/<int:tid>', methods=['POST'])
@login_required
def update_task_status(tid):
    status = request.form['status']
    db = get_db()
    db.execute('UPDATE tasks SET status=? WHERE id=?', (status, tid))
    db.execute("INSERT INTO activity (message) VALUES (?)", (f"Task #{tid} status updated to {status}",))
    db.commit()
    db.close()
    return redirect(url_for('tasks'))

@app.route('/tasks/delete/<int:tid>')
@login_required
def delete_task(tid):
    db = get_db()
    db.execute('DELETE FROM tasks WHERE id=?', (tid,))
    db.commit()
    db.close()
    return redirect(url_for('tasks'))

# ─── MATERIALS ───────────────────────────────────────────

@app.route('/materials')
@login_required
def materials():
    db = get_db()
    data = db.execute('SELECT * FROM materials').fetchall()
    db.close()
    return render_template('materials.html', materials=data)

@app.route('/materials/add', methods=['POST'])
@login_required
def add_material():
    name     = request.form['name']
    quantity = request.form['quantity']
    unit     = request.form.get('unit', 'pcs')
    db = get_db()
    db.execute('INSERT INTO materials (name, quantity, unit) VALUES (?,?,?)',
               (name, quantity, unit))
    db.execute("INSERT INTO activity (message) VALUES (?)", (f"Material '{name}' added",))
    db.commit()
    db.close()
    return redirect(url_for('materials'))

@app.route('/materials/use/<int:mid>', methods=['POST'])
@login_required
def use_material(mid):
    amount = int(request.form['amount'])
    db = get_db()
    mat = db.execute('SELECT * FROM materials WHERE id=?', (mid,)).fetchone()
    new_used = mat['used'] + amount
    new_qty  = mat['quantity'] - amount
    if new_qty < 0:
        flash(f"Not enough stock for '{mat['name']}'")
        db.close()
        return redirect(url_for('materials'))
    db.execute('UPDATE materials SET used=?, quantity=? WHERE id=?', (new_used, new_qty, mid))
    db.execute("INSERT INTO activity (message) VALUES (?)",
               (f"Used {amount} {mat['unit']} of '{mat['name']}'",))
    db.commit()
    db.close()
    return redirect(url_for('materials'))

@app.route('/materials/delete/<int:mid>')
@login_required
def delete_material(mid):
    db = get_db()
    name = db.execute('SELECT name FROM materials WHERE id=?', (mid,)).fetchone()['name']
    db.execute('DELETE FROM materials WHERE id=?', (mid,))
    db.execute("INSERT INTO activity (message) VALUES (?)", (f"Material '{name}' deleted",))
    db.commit()
    db.close()
    return redirect(url_for('materials'))

# ─── REPORTS ─────────────────────────────────────────────

@app.route('/reports')
@login_required
def reports():
    db = get_db()
    # Task Completion Report
    pending   = db.execute("SELECT COUNT(*) FROM tasks WHERE status='Pending'").fetchone()[0]
    in_prog   = db.execute("SELECT COUNT(*) FROM tasks WHERE status='In Progress'").fetchone()[0]
    completed = db.execute("SELECT COUNT(*) FROM tasks WHERE status='Completed'").fetchone()[0]
    # Electrician Activity Report
    elec_activity = db.execute('''
        SELECT electricians.name,
               COUNT(tasks.id) AS total_tasks,
               SUM(CASE WHEN tasks.status='Completed' THEN 1 ELSE 0 END) AS done
        FROM electricians
        LEFT JOIN tasks ON tasks.electrician_id = electricians.id
        GROUP BY electricians.id
    ''').fetchall()
    # Daily Work Report - recent activity
    activity = db.execute('SELECT * FROM activity ORDER BY id DESC LIMIT 10').fetchall()
    # Jobs summary
    jobs_pending   = db.execute("SELECT COUNT(*) FROM jobs WHERE status='Pending'").fetchone()[0]
    jobs_inprog    = db.execute("SELECT COUNT(*) FROM jobs WHERE status='In Progress'").fetchone()[0]
    jobs_completed = db.execute("SELECT COUNT(*) FROM jobs WHERE status='Completed'").fetchone()[0]
    db.close()
    return render_template('reports.html',
        pending=pending, in_prog=in_prog, completed=completed,
        elec_activity=elec_activity, activity=activity,
        jobs_pending=jobs_pending, jobs_inprog=jobs_inprog,
        jobs_completed=jobs_completed)

# ─── NOTIFICATIONS ───────────────────────────────────────

@app.route('/notifications')
@login_required
def notifications():
    notes = get_notifications()
    return render_template('notifications.html', notifications=notes)

# ─── PROFILE ─────────────────────────────────────────────

@app.route('/profile')
@login_required
def profile():
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()
    db.close()
    return render_template('profile.html', user=user)

if __name__ == '__main__':
    app.run(debug=True)