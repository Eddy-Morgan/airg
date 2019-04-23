from flask import Flask, render_template, jsonify, request, url_for, redirect, abort
from model import Certification, db, Students, Employers, Institutions, AdminModelView
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
from forms import LoginForm, RegistrationForm
import os
from flask_admin import Admin

app = Flask(__name__)
app.secret_key = '+jmhDJtIkpDLq2S/m2qe7oyV6Q320penadqKjO4meugfgqs6gA4JcYyurG34IZ+i3A5/n93cZHM2CCSMJeixy1n7L1O5VYENMc3'

basedir = os.path.abspath(os.path.dirname(__file__))

production =  os.environ.get('PRODUCTION',False)


admin = Admin(app,name='ADMIN', template_mode='bootstrap3',url='/sudo')
admin.add_view(AdminModelView(Students, db.session))
admin.add_view(AdminModelView(Institutions, db.session))
admin.add_view(AdminModelView(Employers, db.session))

if production:
    print('DEVELOPMENT DATABASE')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

else:
    print('TESTING DATABASE')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')


app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] =False

with app.app_context():
    db.init_app(app)
    db.create_all()

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/<level>/login')
def login(level):
  levels = {'student': 'student.html','school':'institution.html','employer':'hire.html'}
  template = levels.get(level)
  print(template)
  try:
    return render_template(template, loginform = LoginForm())
  except:
    abort(404)

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")


@app.route('/register',methods=["GET","POST"])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
          random_gen = Crypto.Random.new().read
          private_key = RSA.generate(1024, random_gen)
          public_key = private_key.publickey()
          response = {
            'private_key': binascii.hexlify(private_key.exportKey(format='DER')).decode('ascii'),
            'public_key': binascii.hexlify(public_key.exportKey(format='DER')).decode('ascii')
            }
          if form.institution_name.data != 'None' and form.company_name == 'None':
                institute = Institutions(form.institution_name.data,form.email.data,response['public_key'],response['private_key'],form.password.data)
                db.session.add(institute)
          elif form.company_name.data != 'None' and form.institution_name.data == 'None':
                company = Employers(form.institution_name.data,form.email.data,response['public_key'],response['private_key'],form.password.data)
                db.session.add(company)
          elif form.company_name.data == 'None' and form.institution_name.data == 'None':
                student = Students(form.email.data,response['public_key'],response['private_key'],form.password.data)
                db.session.add(student)
          db.session.commit()
          return redirect(url_for('registered'))
    return render_template('register.html', registrationform = RegistrationForm())

@app.route('/registered')
def registered():
    print('successful')
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/make/certification')
def make_transaction():
    return render_template('./make_transaction.html')

@app.route('/view/certification')
def view_transaction():
    return render_template('./view_certifications.html')


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