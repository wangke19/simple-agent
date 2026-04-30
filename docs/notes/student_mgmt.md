Create a student registration management GUI app (tkinter + SQLite).

Requires: db.py (database layer with students/courses/grades tables CRUD), app.py (GUI layer with 4 tabs: Student Management / Course Management / Grade Entry / Grade Query).

Database schema:
- Students table: id (integer PK), name (text), gender (text), birthday (text), class (text), phone (text)
- Courses table: id (integer PK), name (text), credits (real), teacher (text)
- Grades table: id (integer PK), student_id (integer FK), course_id (integer FK), score (real), semester (text)

Features:
- Student Management tab: add/edit/delete students, list all students in Treeview
- Course Management tab: add/edit/delete courses, list all courses in Treeview
- Grade Entry tab: select student and course from dropdowns, enter score and semester
- Grade Query tab: query grades by student or course, show results in Treeview with calculated average score
