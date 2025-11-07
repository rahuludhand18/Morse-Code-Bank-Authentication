from flask import Flask, render_template, request, session
import sqlite3
from recognition import Recognise
from dataset import create_dataset
import smtplib
from email.message import EmailMessage

# Initialize SQLite database
connection = sqlite3.connect('user_data.db', check_same_thread=False)
cursor = connection.cursor()
command = """CREATE TABLE IF NOT EXISTS user(
    name TEXT, 
    password TEXT, 
    mpassword TEXT, 
    mobile TEXT, 
    email TEXT, 
    question TEXT, 
    answer TEXT
)"""
cursor.execute(command)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "romeshproject"

# Email configuration
apppassword = 'mfjg nfcm mcyb yzcx'  # Replace with your app password

# Function to send email with attachment
def send_email_attach(from_email_addr, from_email_pass, to_email_addr, subject, body, attachment_path=None):
    msg = EmailMessage()
    msg.set_content(body)
    msg['From'] = from_email_addr
    msg['To'] = to_email_addr
    msg['Subject'] = subject

    if attachment_path:
        with open(attachment_path, 'rb') as attachment:
            msg.add_attachment(attachment.read(), maintype='application', subtype='octet-stream', filename=attachment_path.split('/')[-1])
    
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_email_addr, from_email_pass)
    server.send_message(msg)
    server.quit()

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# User login route
@app.route('/userlog', methods=['GET', 'POST'])
def userlog():
    if request.method == 'POST':
        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        name = request.form['name']
        password = request.form['password']

        # Corrected SQL query with parameterized inputs
        query = "SELECT * FROM user WHERE name = ? AND password = ?"
        cursor.execute(query, (name, password))  # Pass parameters as a tuple
        result = cursor.fetchone()

        if result:
            try:
                res = Recognise()
                if res == name:
                    # Generate OTP and send email even if face recognition is successful
                    import random
                    otp = random.randint(1111, 9999)
                    print(f"\n\n\n OTP is     {otp} \n\n\n")
                    session['otp'] = otp
                    session['email'] = result[4]
                    session['pass'] = result[2]  # Set session['pass'] here
                    send_email_attach('romesh3005@gmail.com', apppassword, result[4], 'OTP', f'Your OTP is {otp}', 'frame.jpg')
                    
                    # Redirect to verification page to enter OTP
                    return render_template("verification.html", msg="OTP sent to your email. Please verify.")
                else:
                    # Generate OTP and send email if face recognition is unsuccessful
                    import random
                    otp = random.randint(1111, 9999)
                    session['otp'] = otp
                    session['email'] = result[4]
                    session['pass'] = result[2]  # Set session['pass'] here
                    send_email_attach('romesh3005@gmail.com', apppassword, result[4], 'OTP', f'Your OTP is {otp}', 'frame.jpg')
                    return render_template("verification.html", msg="Face recognition unsuccessful. OTP sent to your email.")
            except Exception as e:
                print(e)
                return render_template("index.html", msg="Something went wrong. Please try again.")
        else:
            return render_template('resetpassword.html', msg='Answer for security question')

    return render_template('index.html')

# User registration route
@app.route('/userreg', methods=['GET', 'POST'])
def userreg():
    if request.method == 'POST':
        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        name = request.form['name']
        password = request.form['password']
        mpassword = request.form['mpassword']
        mobile = request.form['phone']
        email = request.form['email']
        question = request.form['question']
        answer = request.form['answer']

        query = "SELECT * FROM user WHERE mobile = ?"
        cursor.execute(query, (mobile,))
        result = cursor.fetchone()

        if result:
            return render_template('index.html', msg='Phone number already exists')
        else:
            cursor.execute("INSERT INTO user VALUES (?, ?, ?, ?, ?, ?, ?)", 
                          (name, password, mpassword, mobile, email, question, answer))
            connection.commit()
            create_dataset(name)
            return render_template('index.html', msg='Successfully Registered')
    
    return render_template('index.html')

# OTP verification route
@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        otp = request.form['otp']
        if str(otp) == str(session['otp']):
            # OTP is correct, proceed to home page
            return render_template("home.html", msg="Login Successful")
        else:
            # OTP is incorrect, redirect back to verification page
            return render_template("verification.html", msg="Incorrect OTP. Please try again.")

    return render_template('index.html')

# Morse code route
@app.route('/morsecode')
def morsecode():
    if 'pass' not in session:
        return render_template('index.html', msg="Session expired. Please log in again.")

    from only_morse import Morse
    res = Morse(session['pass'])
    if res == 'Successful':
        # Send email confirming successful login
        send_email_attach('romesh3005@gmail.com', apppassword, session['email'], 'Login Successful', 'You have successfully logged in.', 'frame.jpg')
        
        # Render the welcome page
        return render_template('welcome.html', msg="Welcome! You have successfully logged in.")
    else:
        return render_template('index.html', msg="Morse code verification failed. Please try again.")

# Logout route
@app.route('/logout')
def logout():
    session.clear()  # Clear the session on logout
    return render_template('index.html')

# Run the app
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)