from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.urandom(12)

# Function to check if the user is authenticated
def is_authenticated():
    return 'user_id' in session

# Route for the home page
@app.route('/')
def home():
    if is_authenticated():
        return f'Hello, User {session["user_id"]}! <a href="/logout">Logout</a>'
    return 'Home Page - <a href="/login">Login</a> - <a href="/signup">Sign Up</a>'

# Route for user registration (sign up)
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            user = auth.create_user(
                email=email,
                password=password
            )
            session['user_id'] = user.uid
            return redirect(url_for('home'))
        except auth.AuthError as e:
            return f"Sign up failed: {e}"

    return render_template('signup.html')

# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            user = auth.sign_in_with_email_and_password(email, password)
            session['user_id'] = user['localId']
            return redirect(url_for('home'))
        except auth.AuthError as e:
            return f"Login failed: {e}"

    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
