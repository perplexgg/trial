# Student Incentive System - CLI Command Reference

This document provides a concise guide to all Flask CLI commands for the Student Incentive System. Commands are grouped by area, with arguments, roles, and expected behavior.

---

## Roles

Commands are role-aware. Instead of logging in, commands now accept a **username** to identify the acting user.

- **student**: can request hours and view accolades.  
- **staff**: can log hours directly, view pending requests, and approve/reject requests.

---

## App-Level Commands

### `flask init`
- **Args:** None  
- **Role:** Anyone  
- **Does:** Creates and initializes the database with default users and activities.

### `flask leaderboard`
- **Args:** None  
- **Role:** Anyone  
- **Does:** Prints a ranked list of students by total hours (descending; tie-break by username).

---

## User Group Commands (`flask user …`)

### `flask user create <user_type> <username> <password>`
- **Role:** Anyone  
- **Does:** Creates a new user.  
- **Notes:** `user_type` must be `student` or `staff`.

### `flask user list [string|json]`
- **Role:** Anyone  
- **Does:** Lists all users.  
- **Notes:** Default output is `string`. Use `json` to output JSON.

### `flask user logs [string|json]`
- **Role:** Anyone  
- **Does:** Lists all log entries of hours.  
- **Notes:** Default output is `string`. Use `json` to output JSON.

### `flask user request <hours> <activity_name> <student_username>`
- **Role:** Student  
- **Does:** Creates a request for staff to approve hours for a specific activity.  
- **Notes:** Fails if the activity does not exist or student username is invalid.

### `flask user accolades <student_username>`
- **Role:** Student  
- **Does:** Displays milestone status per activity for the specified student using `resolve_milestone` and `milestones_for`.  
- **Output:** One line per activity showing current milestone and progress.

### `flask user logs_hours <staff_username> <student_username> <hours> <activity_name>`
- **Role:** Staff  
- **Does:** Logs hours for a student in a specific activity and updates the student’s total hours.  
- **Notes:** Fails if the staff, student, or activity is invalid.

### `flask user confirm <staff_username> <approve|reject> <request_id>`
- **Role:** Staff  
- **Does:** Approves or rejects a pending student request.  
  - **Approve:** Adds a log entry, increments student hours, and deletes the request.  
  - **Reject:** Deletes the request without adding hours.  
- **Notes:** `staff_username` identifies the acting staff member.

---

## Examples

- Initialize database:  
  ```bash
  flask init
