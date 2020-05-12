from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
from datetime import datetime
import time
import re

app = Flask(__name__)

app.secret_key = 'vinti_fara_restante'

# database connection details
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'parola10'
app.config['MYSQL_DB'] = 'pythonlogin'

# Intialize MySQL
mysql = MySQL(app)

categories = ['Arts', 'Animals', 'Games', 'Geography', 'Movies', 'Music', 'Science', 'Programming', 'Sport', 'Literature']


# http://localhost:5000 - this is the index page
@app.route('/')
def init():
    return render_template('index.html')


# http://localhost:5000/login/ - this will be the login page, we need to use both GET and POST requests
@app.route('/login/', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
            # Fetch one record and return result
            account = cursor.fetchone()
            # If account exists in accounts table in out database
            if account:
                # Create session data, we can access this data in other routes
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                # Redirect to home page
                return redirect(url_for('home'))
            else:
                # Account doesnt exist or username/password incorrect
                msg = 'Incorrect username/password!'
        except MySQLdb.OperationalError:
            msg = "ERROR: Could not connect to MySQL!"
    # Show the login form with message (if any)
    return render_template('login.html', msg=msg)


# http://localhost:5000/logout - this will be the logout page
@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    # Redirect to login page
    return redirect(url_for('init'))


# http://localhost:5000/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and\
            'email' in request.form and 'name' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        name = request.form['name']
        registered_on = datetime.now()
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        username_in_use = cursor.fetchone()
        cursor.execute('SELECT * FROM accounts WHERE email = %s', (email,))
        email_in_use = cursor.fetchone()
        # If account exists show error and validation checks
        if username_in_use and email_in_use:
            msg = 'Username and email are already in use!'
        elif username_in_use:
            msg = 'Username is already in use!'
        elif email_in_use:
            msg = 'Email is already in use!'
        elif not re.match(r'[A-Z][A-Za-z' ']+', name):
            msg = 'Invalid name!'
        elif not re.match(r'^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email or not name:
            msg = 'Please fill out the form!'
        else:
            # Account doesn't exist and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO accounts(username, password, name, email, registered_on) VALUES\
                           (%s, %s, %s, %s, %s)', (username, password, name, email, registered_on))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)


# http://localhost:5000/home - this will be the home page, only accessible for loggedin users
@app.route('/home')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('home.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


# http://localhost:5000/profile - this will be the profile page, only accessible for loggedin users
@app.route('/profile')
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route('/questions', methods=['GET', 'POST'])
def questions():
    msg = ''
    if request.method == 'POST' and 'text' in request.form and 'opt1' in request.form \
            and 'opt2' in request.form and 'opt3' in request.form and 'correct' in request.form:
        category = request.form['category']

        text = request.form['text']
        opt1 = request.form['opt1']
        opt2 = request.form['opt2']
        opt3 = request.form['opt3']
        correct = request.form['correct']

        # Check if question already exists
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if not category or not text or not correct or not opt1 or not opt2 or not opt3:
            msg = 'Please fill out the form!'
        elif category not in categories:
            msg = 'Invalid category!'
        else:
            # insert new question into questions table
            cursor.execute('INSERT INTO questions(category, text, opt1, opt2, opt3, correct) VALUES \
                               (%s, %s, %s, %s, %s, %s)', (category, text, opt1, opt2, opt3, correct))
            mysql.connection.commit()
            msg = 'Question added to database!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('questions.html', msg=msg, categories=categories)


@app.route('/home/single-player')
@app.route('/home/single-player/<selected_category>', methods=['GET'])
def single_player(selected_category):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM questions WHERE category=%s ORDER BY RAND() LIMIT 10', (selected_category,))
    questions_list = cursor.fetchall()

    return render_template('single_player.html', questions_list=questions_list, selected_category=selected_category)

@app.route('/home/single-player/<selected_category>', methods=['POST'])
def send_results(selected_category):
    if request.method == "POST":
        score =  request.get_json()
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        username = account['username']
        fs = str(score)
        cursor.execute('INSERT INTO games(username, mode, category, score) VALUES \
                               (%s, %s, %s, %s)', (username, 'single', selected_category, fs))
        mysql.connection.commit()
        time.sleep(4)

    return render_template('show_score.html')


@app.route('/home/single-player/categories', methods=['GET', 'POST'])
def categories_select():
    return render_template('categories_select.html')


@app.route('/home/daily-challenge', methods=['GET'])
def daily_challenge():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM questions ORDER BY RAND() LIMIT 10')
    questions_list = cursor.fetchall()

    return render_template('daily_challenge.html', questions_list=questions_list)

@app.route('/home/daily-challenge', methods=['POST'])
def send_daily_results():
    if request.method == "POST":
        score =  request.get_json()
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        username = account['username']
        played_at = datetime.now()
        fs = str(score)
        cursor.execute('INSERT INTO challenges(username, mode, score, played_at) VALUES \
                               (%s, %s, %s, %s)', (username, 'challenge', fs, played_at))
        mysql.connection.commit()
    return render_template('home.html')

@app.route('/home/show_score')
def show_score():
    return render_template('show_score.html')

@app.route('/home/ranking')
def ranking():
    return render_template('ranking.html')

@app.route('/contact-us')
def contact_us():
    return render_template('contact_us.html')