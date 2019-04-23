from flask_wtf import FlaskForm
from wtforms import PasswordField,StringField,ValidationError,SubmitField,validators,HiddenField,SelectField,BooleanField
from model import Students

def available_email(form,field):
    if Students.query.filter_by(email=field.data).first():
        raise ValidationError("Email already registered")


class LoginForm(FlaskForm):
    wallet_id = StringField('Wallet ID',
                            validators=[validators.DataRequired()],render_kw={'autofocus': True})
    password = PasswordField('Password',
                                 validators=[validators.DataRequired(message='Password field is required')])
    submit = SubmitField('Sign in', [validators.DataRequired()])

class RegistrationForm(FlaskForm):
    myChoices = [('student','Student'),('institution','Institution'),('employer','Employer')]
    myField = SelectField('Register As', choices = myChoices, validators = [validators.DataRequired()])
    institution_name = StringField('Insitution Name',
                       validators = [])
    company_name = StringField('Company Name',
                       validators = [])
    
    email = StringField('Email', validators=[validators.DataRequired(),validators.Length(1,64),validators.Email(),available_email])

    password = PasswordField('Password',
                             validators = [validators.DataRequired(),
                                            validators.Regexp(regex=r'^(?=.*[A-Z])(?=.*[\W])(?=.*[0-9])(?=.*[a-z]).{8,128}$',
                                                message='Use at least 8 characters, a mix of letters, numbers and symbols.'),
                                           validators.EqualTo('passwordconfirm', message='Passwords must match')])
    passwordconfirm = PasswordField('confirm Password', validators=[validators.DataRequired()
                                                       ])
    agree = BooleanField('I have read and agreed to the  Terms of Service &  Privacy Policy.',
                         validators=[validators.DataRequired(u'You must accept our Terms of Service')])
    submit = SubmitField('Register', [validators.DataRequired()])
