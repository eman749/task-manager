from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-only-change-in-production')

# MySQL Configuration — reads env vars (Docker) or falls back to local defaults
app.config['MYSQL_HOST']        = os.environ.get('MYSQL_HOST', 'db')
app.config['MYSQL_USER']        = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD']    = os.environ.get('MYSQL_PASSWORD', '123456')
app.config['MYSQL_DB']          = os.environ.get('MYSQL_DB', 'task_management')
app.config['MYSQL_PORT']        = int(os.environ.get('MYSQL_PORT', 3306))
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


# ─── Login Required Decorator ────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ─── ENDPOINT 1: Home ────────────────────────────────────────────────────────
@app.route('/')
def home():
    return redirect(url_for('dashboard') if 'user_id' in session else url_for('login'))


# ─── ENDPOINT 2: Register ────────────────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email    = request.form['email']
        password = generate_password_hash(request.form['password'])
        cur = mysql.connection.cursor()
        try:
            cur.execute(
                "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                (username, email, password)
            )
            mysql.connection.commit()
            flash('Account created! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception:
            flash('Username or email already exists.', 'danger')
        finally:
            cur.close()
    return render_template('register.html')


# ─── ENDPOINT 3: Login ───────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        if user and check_password_hash(user['password'], password):
            session['user_id']  = user['id']
            session['username'] = user['username']
            flash(f"Welcome back, {user['username']}!", 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('login.html')


# ─── ENDPOINT 4: Logout ──────────────────────────────────────────────────────
@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))


# ─── ENDPOINT 5: Dashboard ───────────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT p.*, COUNT(t.id) as task_count
        FROM projects p
        LEFT JOIN tasks t ON p.id = t.project_id
        WHERE p.user_id = %s
        GROUP BY p.id
        ORDER BY p.created_at DESC
    """, (session['user_id'],))
    projects = cur.fetchall()

    cur.execute("""
        SELECT t.*, p.name as project_name
        FROM tasks t
        JOIN projects p ON t.project_id = p.id
        WHERE p.user_id = %s AND t.status != 'done'
        ORDER BY t.due_date ASC
        LIMIT 5
    """, (session['user_id'],))
    upcoming_tasks = cur.fetchall()

    cur.execute("SELECT COUNT(*) as total FROM projects WHERE user_id = %s", (session['user_id'],))
    total_projects = cur.fetchone()['total']

    cur.execute("""
        SELECT COUNT(*) as total FROM tasks t
        JOIN projects p ON t.project_id = p.id
        WHERE p.user_id = %s
    """, (session['user_id'],))
    total_tasks = cur.fetchone()['total']

    cur.execute("""
        SELECT COUNT(*) as total FROM tasks t
        JOIN projects p ON t.project_id = p.id
        WHERE p.user_id = %s AND t.status = 'done'
    """, (session['user_id'],))
    done_tasks = cur.fetchone()['total']
    cur.close()

    return render_template('dashboard.html',
        projects=projects,
        upcoming_tasks=upcoming_tasks,
        total_projects=total_projects,
        total_tasks=total_tasks,
        done_tasks=done_tasks
    )


# ─── ENDPOINT 6: Add Project ─────────────────────────────────────────────────
@app.route('/project/add', methods=['GET', 'POST'])
@login_required
def add_project():
    if request.method == 'POST':
        name        = request.form['name']
        description = request.form.get('description', '')
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO projects (user_id, name, description) VALUES (%s, %s, %s)",
            (session['user_id'], name, description)
        )
        mysql.connection.commit()
        cur.close()
        flash('Project created!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_project.html')


# ─── ENDPOINT 7: Project Tasks ───────────────────────────────────────────────
@app.route('/project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def project_tasks(project_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM projects WHERE id = %s AND user_id = %s", (project_id, session['user_id']))
    project = cur.fetchone()
    if not project:
        flash('Project not found.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title       = request.form['title']
        description = request.form.get('description', '')
        priority    = request.form.get('priority', 'medium')
        due_date    = request.form.get('due_date') or None
        cur.execute("""
            INSERT INTO tasks (project_id, title, description, priority, due_date)
            VALUES (%s, %s, %s, %s, %s)
        """, (project_id, title, description, priority, due_date))
        mysql.connection.commit()
        flash('Task added!', 'success')

    cur.execute("SELECT * FROM tasks WHERE project_id = %s ORDER BY created_at DESC", (project_id,))
    tasks = cur.fetchall()
    cur.close()
    return render_template('project_tasks.html', project=project, tasks=tasks)


# ─── ENDPOINT 8: Edit Task ───────────────────────────────────────────────────
@app.route('/task/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT t.*, p.user_id FROM tasks t
        JOIN projects p ON t.project_id = p.id
        WHERE t.id = %s AND p.user_id = %s
    """, (task_id, session['user_id']))
    task = cur.fetchone()
    if not task:
        flash('Task not found.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title       = request.form['title']
        description = request.form.get('description', '')
        priority    = request.form.get('priority', 'medium')
        status      = request.form.get('status', 'todo')
        due_date    = request.form.get('due_date') or None
        cur.execute("""
            UPDATE tasks SET title=%s, description=%s, priority=%s, status=%s, due_date=%s
            WHERE id=%s
        """, (title, description, priority, status, due_date, task_id))
        mysql.connection.commit()
        cur.close()
        flash('Task updated!', 'success')
        return redirect(url_for('project_tasks', project_id=task['project_id']))

    cur.close()
    return render_template('edit_task.html', task=task)


# ─── ENDPOINT 9: Delete Task ─────────────────────────────────────────────────
@app.route('/task/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    project_id = request.form.get('project_id')
    cur = mysql.connection.cursor()
    cur.execute("""
        DELETE tasks FROM tasks
        JOIN projects p ON tasks.project_id = p.id
        WHERE tasks.id = %s AND p.user_id = %s
    """, (task_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    flash('Task deleted.', 'info')
    return redirect(url_for('project_tasks', project_id=project_id))


# ─── ENDPOINT 10: Delete Project ─────────────────────────────────────────────
@app.route('/project/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM projects WHERE id=%s AND user_id=%s", (project_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    flash('Project deleted.', 'info')
    return redirect(url_for('dashboard'))


# ─── ENDPOINT 11: Profile ────────────────────────────────────────────────────
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id=%s", (session['user_id'],))
    user = cur.fetchone()

    if request.method == 'POST':
        username = request.form['username']
        email    = request.form['email']
        try:
            cur.execute("UPDATE users SET username=%s, email=%s WHERE id=%s",
                        (username, email, session['user_id']))
            mysql.connection.commit()
            session['username'] = username
            flash('Profile updated!', 'success')
        except Exception:
            flash('Username or email already exists.', 'danger')
        finally:
            cur.close()
        return redirect(url_for('profile'))

    cur.close()
    return render_template('profile.html', user=user)


if __name__ == '__main__':
    app.run(debug=True)
