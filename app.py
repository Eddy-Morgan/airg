from flask import Flask, render_template, jsonify, request, url_for, redirect, abort
from model import Certification
import Crypto
import Crypto.Random
import binascii
import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4
from Crypto.PublicKey import RSA
import requests
from flask_cors import CORS
from forms import LoginForm, StudentregistrationForm

app = Flask(__name__)
app.secret_key = '+jmhDJtIkpDLq2S/m2qe7oyV6Q320penadqKjO4meugfgqs6gA4JcYyurG34IZ+i3A5/n93cZHM2CCSMJeixy1n7L1O5VYENMc3'

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/<level>/login')
def login(level):
  levels = {'student': 'student.html','school':'institution.html','employer':'hire.html'}
  template = levels.get(level)
  try:
    return render_template(template, loginform = LoginForm())
  except:
    abort(404)

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")


@app.route('/register')
def register():
    return render_template('register.html', registrationform =StudentregistrationForm())

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/make/certification')
def make_transaction():
    return render_template('./make_transaction.html')

@app.route('/view/certification')
def view_transaction():
    return render_template('./view_certifications.html')

@app.route('/portfolio/new', methods=['GET'])
def new_wallet():
  random_gen = Crypto.Random.new().read
  private_key = RSA.generate(1024, random_gen)
  public_key = private_key.publickey()
  response = {
    'private_key': binascii.hexlify(private_key.exportKey(format='DER')).decode('ascii'),
    'public_key': binascii.hexlify(public_key.exportKey(format='DER')).decode('ascii')
  }

  return jsonify(response), 200

@app.route('/generate/certification', methods=['POST'])
def generate_certification():
  sender_address = request.form['sender_address']
  sender_private_key = request.form['sender_private_key']
  recipient_address = request.form['recipient_address']
  value = request.form['amount']
  
  certification = Certification(sender_address, sender_private_key, recipient_address, value)

  response = {'certification': certification.to_dict(), 'signature': certification.sign_certification()}

  return jsonify(response), 200

if __name__ == "__main__":
    app.run(debug=True, port= 8080)