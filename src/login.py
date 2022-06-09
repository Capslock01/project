"""Handles login and logout."""

import re
import functools
from flask import g
from flask import redirect
from flask import render_template
from flask import session
from flask import request
from flask import url_for
from flask import flash
from passlib.hash import sha512_crypt
from src import app, db


def require_login():
    """Check that user is logged in when accessing app."""

    def decorator(func):
        """Check access decorator."""

        @functools.wraps(func)
        def decorated_function(*args, **kwargs):
            """Check that user is logged in."""

            if  not g.user:
                return redirect(url_for('login'))
            return func(*args, **kwargs)
        return decorated_function
    return decorator

def hash_passwd(password) -> str:
    """Return password hash as string."""

    return sha512_crypt.hash(password)

def validate_passwd(user, password, user_password) -> bool:
    """Validate user's password."""

    return user and password and sha512_crypt.verify(password, user_password)

@app.before_request
def before_request():
    """Entry function to define g.user."""

    g.user = session.get('user')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    """Log in to the app."""

    if g.user:
        return redirect(url_for('home'))
    
    # Create new login
    invalidate_login()
    name = request.values.get('username')
    password = request.values.get('password')

    # If no posts, just render login.html
    if not name or not password:
        return render_template('login.html')

    query = 'SELECT id, name, password FROM account WHERE name=:name'
    result = db.session.execute(query, {'name': name}).fetchone()
    # If user doesn't exist, redirect to register page
    if not result:
        flash('Invalid username or password.')
        return redirect(url_for('login'))
    # If login succesful, set session user
    if validate_passwd(result[1], password, result[2]):
        session['user'] = result[0]
        return redirect(url_for('home'))
    # Flash error message if login unsuccessful
    flash('Invalid username or password.')
    return redirect(url_for('login'))
    

@app.route('/register', methods = ['GET', 'POST'])
def register():
    """Register a new user."""

    if g.user:
        return redirect(url_for('home'))
    
    # Create new user
    invalidate_login()
    name = request.values.get('username')
    password = request.values.get('password')
    repeat_pw = request.values.get('repeat_pw')

    if not name or not password or not repeat_pw:
        return render_template('register.html')

    name_regex = '^(?![-._])(?!.*[_.-]{2})[\w.-]{3,32}(?<![-._])$'
    if re.match(name_regex, name) is None:
        flash('Invalid username. Please refer to instructions for username.')
        return redirect(url_for('register'))
    if len(password) < 10:
        flash('Password must be at least 10 characters.')
        return redirect(url_for('register'))
    if password != repeat_pw:
        flash('Please enter matching passwords!')
        return redirect(url_for('register'))
    # Username taken?
    query = 'SELECT id, name, password FROM account WHERE name=:name'
    result = db.session.execute(query, {'name': name}).fetchone()
    if result:
        flash('Username already exists.')
        return redirect(url_for('register'))

    # Successful creation of new user
    password = hash_passwd(password)
    insert = 'INSERT INTO account (name, password) VALUES (:name, :password)'
    db.session.execute(insert, {'name': name, 'password': password})
    db.session.commit()
    flash(f'User {name} has been successfully created.')
    return redirect(url_for('login'))
    

def invalidate_login():
    """Remove all current user information from session."""

    session.pop('user', None)
    g.user = None

@app.route('/logout')
def logout():
    """Log out from the app."""

    invalidate_login()
    return redirect(url_for('login'))
