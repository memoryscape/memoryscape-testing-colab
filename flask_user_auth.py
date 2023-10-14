from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import os
from firebase_admin import credentials, initialize_app, storage, auth, firestore
from typing import Optional, List
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from flask_cors import CORS
import base64
app = Flask(__name__)
CORS(app)
app.secret_key = os.urandom(12)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'login'

cred = credentials.Certificate("/Users/dhruvroongta/Downloads/memoryscape-59213-b6a4d1938f99.json")
initialize_app(cred)
firestore_client = firestore.client()
coll_ref = firestore_client.collection("memoryscape_users")


def process(imgList, user_name, vault_name):
  ct = 1
  for img in imgList:
    img = img.decode()
    cv2.imwrite("/content/" + str(ct) + ".jpg", img)
    bucket = storage.bucket("memoryscape-59213.appspot.com")
    blob = bucket.blob(user_name + "/" + vault_name + "/" + str(ct) + ".jpg")
    blob.upload_from_filename("/content/" + str(ct) + ".jpg")
    blob.make_public()
    os.remove("/content/" + str(ct) + ".jpg")
    ct += 2

def add_user(email: str) -> None:
    doc_ref = coll_ref.document(email)
    create_time = doc_ref.set({
        "email": email,
        "vaults": []
    })


def add_vault(email: str, vault_name: str, vault_url: str, shared: bool) -> None:
    doc_ref = coll_ref.document(email)
    doc_ref.update({"vaults": firestore.ArrayUnion([{"vault_url": vault_url, "vault_name": vault_name, "shared": shared}])})


def is_authenticated() -> bool:
    return 'user_id' in session

def stitchImage(size):
  images = []
  ct = 1

  for i in range(size):
    bucket = storage.bucket("memoryscape-59213.appspot.com")
    blob = bucket.get_blob(str(ct) + ".jpg")
    blob.download_to_filename(str(ct) + ".jpg")
    images.append(cv2.imread("/content/" + str(ct) + ".jpg"))
    os.remove("/content/" + str(ct) + ".jpg")
    ct += 2
  prev = images[0]

  for i in range(1, len(images)):
    prev = np.concatenate([prev, images[i]], axis = 1)
  cv2.imwrite("/content/res.jpg", prev)

  plt.imshow(prev)

  bucket = storage.bucket("memoryscape-59213.appspot.com")
  blob = bucket.blob("result.jpg")
  blob.upload_from_filename("/content/res.jpg")
  blob.make_public()
  os.remove("/content/res.jpg")
  return blob.public_url

def process(imgList, user_name, vault_name):
  ct = 1

  for img in imgList:
    cv2.imwrite("/content/" + str(ct) + ".jpg", img)
    bucket = storage.bucket("memoryscape-59213.appspot.com")
    blob = bucket.blob(str(ct) + ".jpg")
    blob.upload_from_filename("/content/" + str(ct) + ".jpg")
    blob.make_public()
    os.remove("/content/" + str(ct) + ".jpg")
    ct += 2

@app.route('/')
def home():
    if is_authenticated():
        return f'Hello, User {session["user_id"]}! <a href="/logout">Logout</a>'
    return 'Home Page - <a href="/login">Login</a> - <a href="/signup">Sign Up</a>'


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM accounts WHERE email = % s', (email, ))
            account = cursor.fetchone()
            cursor.execute('INSERT INTO accounts VALUES (NULL, % s, % s)', (password, email, ))
            mysql.connection.commit()
            bucket = storage.bucket("memoryscape-59213.appspot.com")
            blob = bucket.blob(email + "/")
            blob.upload_from_filename('')
            blob.make_public()
            session['user_id'] = user.uid
            add_user(user.uid)
            return redirect(url_for('home'))
        except Exception as e:
            return f"Sign up failed: {e}"

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM accounts WHERE username = % s AND password = % s', (username, password, ))
            account = cursor.fetchone()
            if account:
              session['user_id'] = user['localId']
            else:
              raise Exception
            return redirect(url_for('home'))
        except Exception as e:
            return f"Login failed: {e}"

    return render_template('login.html')

@app.route('/get_vaults/<email>', methods = ['GET'])
def get_vaults(email: str):
    try: 
        result = coll_ref.document(email).get()
        return jsonify({'result': result.to_dict()})
    except Exception as e: 
        return f"Getting Vaults failed: {e}"

@app.route('/share_vault', methods = ['POST'])
def share_vault():
    try: 
        email = request.form('email')
        vault_name = request.form('vault_name')
        vault_url = request.form('vault_url')
        share_emails = request.form('share_emails')
        for share_email in share_emails:
            add_vault(share_email,vault_name, vault_url, True)
    except Exception as e: 
        return f"Sharing Vaults failed: {e}"

@app.route('/get_images', methods = ['GET'])
def get_images():
    try:
        email = request.form('email')
        vault_name = request.form('vault_name')
        list_imgs = request.form('list_imgs')
        process(list_imgs, email, vault_name)
    except Exception as e:
        return f"Images not received: {e}"

if __name__ == '__main__':
    app.run(debug=True)
