# Task Manager — Flask Application

A full-stack task management web app built with **Flask** and **MySQL**.


## Features

- User registration & session-based login
- Create, view, and delete projects
- Add, edit, and delete tasks with priority & due date
- User profile management
- Docker support for easy deployment


## Endpoints (11 total)

| # | Route | Method | Description |
|---|-------|--------|-------------|
| 1 | `/` | GET | Redirect to dashboard or login |
| 2 | `/register` | GET, POST | User registration |
| 3 | `/login` | GET, POST | User login |
| 4 | `/logout` | GET | Clear session & logout |
| 5 | `/dashboard` | GET | Overview: projects, tasks, stats |
| 6 | `/project/add` | GET, POST | Create new project |
| 7 | `/project/<id>` | GET, POST | View project tasks & add task |
| 8 | `/task/<id>/edit` | GET, POST | Edit task details |
| 9 | `/task/<id>/delete` | POST | Delete a task |
| 10 | `/project/<id>/delete` | POST | Delete a project |
| 11 | `/profile` | GET, POST | View & update profile |

---

## Run Locally

```bash
pip install -r requirements.txt
# Set up MySQL and run init.sql
python app.py
```

---

## Run with Docker (Bonus)

```bash
docker-compose up --build
```

App runs at **http://localhost:5000**  
MySQL runs on port **3306** (auto-initialized via `init.sql`)

```bash
# Stop containers
docker-compose down

# View logs
docker-compose logs web
```

---

## Database Schema

**3 tables:** `users` → `projects` → `tasks`

- `users`: id, username, email, password, created_at  
- `projects`: id, user_id (FK), name, description, created_at  
- `tasks`: id, project_id (FK), title, description, priority, status, due_date, created_at

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Flask (Python 3.11) |
| Database | MySQL 8.0 |
| Auth | Session + Werkzeug hashing |
| Frontend | Bootstrap 5 + Jinja2 |
| Container | Docker + Docker Compose |

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Flask session secret — use a long random string in production |
| `MYSQL_HOST` | MySQL host (use `db` when running with Docker) |
| `MYSQL_USER` | MySQL username |
| `MYSQL_PASSWORD` | MySQL password |
| `MYSQL_DB` | Database name |

---

## Project Structure

```
task_management/
├── app.py                  # Flask routes & logic
├── requirements.txt        # Python dependencies
├── init.sql                # Database schema
├── Dockerfile
├── docker-compose.yml
├── .env.example            # Environment variables template
├── .gitignore
├── static/
│   ├── css/style.css       # Shared styles
│   └── js/main.js          # Shared scripts
└── templates/
    ├── base.html           # Base layout (sidebar + topbar)
    ├── dashboard.html
    ├── login.html
    ├── register.html
    ├── add_project.html
    ├── project_tasks.html
    ├── edit_task.html
    └── profile.html
```
