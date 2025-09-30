import click, pytest, sys
from flask import Flask
from flask.cli import AppGroup
from sqlalchemy import select, func

from App.database import db, get_migrate
from App.models import User, Student, Staff, Log, Request, Activity
from App.main import create_app
from App.controllers import (
    create_student, create_staff, get_all_users_json, get_all_users,
    initialize, add_student_hours, resolve_milestone, milestones_for
)

app = create_app()
migrate = get_migrate(app)

# =========================
# Helper
# =========================

def get_user_by_username(username):
    return User.query.filter_by(username=username).first()

# =========================
# Init / Leaderboard
# =========================

@app.cli.command("init", help="Creates and initializes the database")
def init():
    initialize()
    print('Database initialized.')

@app.cli.command("leaderboard", help="Shows the Leaderboard")
def view_leaderboard():
    students = Student.query.order_by(Student.hours.desc(), Student.username.asc()).all()
    if not students:
        print('No students added.')
        return
    print('===== LEADERBOARD =====')
    for i, student in enumerate(students):
        print(f'{i+1}. {student.username}: {student.hours} Hours')

# =========================
# User Commands
# =========================

user_cli = AppGroup('user', help='User commands')

@user_cli.command("create", help="Creates a user")
@click.argument("user_type", default="student")
@click.argument("username", default="rob")
@click.argument("password", default="robpass")
def create_user_command(user_type, username, password):
    if user_type == "student":
        create_student(username, password)
    elif user_type == "staff":
        create_staff(username, password)
    else:
        print('Unknown user type. Use "student" or "staff".')
        return
    user = get_user_by_username(username)
    print(f'Created {user_type}: {username} (id={user.id})')

@user_cli.command("list", help="Lists users in the database")
@click.argument("format", default="string")
def list_users(format):
    if format == 'string':
        print(get_all_users())
    else:
        print(get_all_users_json())

@user_cli.command("logs", help="Lists logs in the database")
@click.argument("format", default="string")
def list_logs(format):
    from App.controllers import get_all_logs, get_all_logs_json
    if format == 'string':
        print(get_all_logs())
    else:
        print(get_all_logs_json())

# =========================
# Student Requests / Accolades
# =========================

@user_cli.command("request", help="Student requests hours")
@click.argument("hours", type=int)
@click.argument("activity_name", type=str)
@click.argument("student_username", type=str)
def request_hours(hours, activity_name, student_username):
    student = Student.query.filter_by(username=student_username).first()
    activity = Activity.query.filter_by(name=activity_name).first()
    if not student:
        print("Student not found.")
        return
    if not activity:
        print("Activity not found.")
        return
    from App.models import Request
    req = Request(student_id=student.id, activity_id=activity.id, hours=hours)
    db.session.add(req)
    db.session.commit()
    print(f"{student.username} requested {hours} hours for {activity.name}.")

@user_cli.command("accolades", help="View student accolades")
@click.argument("student_username", type=str)
def view_accolades(student_username):
    student = Student.query.filter_by(username=student_username).first()
    if not student:
        print("Student not found.")
        return
    activities = db.session.execute(select(Activity.id, Activity.name)).all()
    hours_rows = db.session.execute(
        select(Log.activity_id, func.coalesce(func.sum(Log.hours), 0))
        .where(Log.student_id == student.id)
        .group_by(Log.activity_id)
    ).all()
    hours_by_activity = {aid: int(total) for (aid, total) in hours_rows}
    
    print("===== ACCOLADES =====")
    accolade_text = ""
    for activity_id, activity_name in activities:
        total = hours_by_activity.get(activity_id, 0)
        result = resolve_milestone(total, milestones_for(activity_name))
        print(f"{activity_name}: {result}")
        accolade_text += f"{activity_name}: {result}\n"
    
    if not student.accolade:
        student.accolade = accolade_text
        db.session.add(student)
        db.session.commit()

# =========================
# Staff Approvals / Logging
# =========================

@user_cli.command("logs_hours", help="Staff logs hours for student")
@click.argument("staff_username", type=str)
@click.argument("student_username", type=str)
@click.argument("hours", type=int)
@click.argument("activity_name", type=str)
def log_hours(staff_username, student_username, hours, activity_name):
    staff = Staff.query.filter_by(username=staff_username).first()
    student = Student.query.filter_by(username=student_username).first()
    activity = Activity.query.filter_by(name=activity_name).first()
    if not staff or not student or not activity:
        print("Invalid staff, student, or activity")
        return
    log = Log(staff_id=staff.id, student_id=student.id, hours=hours, activity_id=activity.id)
    db.session.add(log)
    add_student_hours(student.id, hours)
    db.session.commit()
    print(f"Logged {hours} hours for {student.username} ({activity.name}) by {staff.username}.")

@user_cli.command("confirm", help="Staff approves/rejects student request")
@click.argument("staff_username", type=str)
@click.argument("action", type=str)
@click.argument("request_id", type=int)
def confirm_hours(staff_username, action, request_id):
    staff = Staff.query.filter_by(username=staff_username).first()
    if not staff:
        print("Staff not found.")
        return
    req = Request.query.get(request_id)
    if not req:
        print("Request not found.")
        return
    student = Student.query.get(req.student_id)
    activity = Activity.query.get(req.activity_id)
    
    if action == "approve":
        log = Log(staff_id=staff.id, student_id=student.id, hours=req.hours, activity_id=activity.id)
        db.session.add(log)
        add_student_hours(student.id, req.hours)
        db.session.delete(req)
        db.session.commit()
        print(f"Approved {req.hours} hours for {student.username} ({activity.name})")
    elif action == "reject":
        db.session.delete(req)
        db.session.commit()
        print(f"Rejected {req.hours} hours for {student.username}")
    else:
        print("Invalid action. Use 'approve' or 'reject'.")

# =========================
# Add CLI groups
# =========================

app.cli.add_command(user_cli)

# =========================
# Test commands
# =========================

test = AppGroup('test', help='Run tests')
@test.command("user", help="Run User tests")
@click.argument("type", default="all")
def user_tests_command(type):
    if type == "unit":
        sys.exit(pytest.main(["-k", "UserUnitTests"]))
    elif type == "int":
        sys.exit(pytest.main(["-k", "UserIntegrationTests"]))
    else:
        sys.exit(pytest.main(["-k", "App"]))

app.cli.add_command(test)
