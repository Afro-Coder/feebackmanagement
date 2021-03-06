from . import auth
from .forms import RegForm,LoginForm
from flask import request,render_template,url_for,redirect,flash,session
from flask_login import current_user,logout_user,login_required,login_user
from ...models.users import User,Domains
from FMSapp import db

#from FMSapp import sess
from ..utils import send_email

import os

@auth.before_app_request
def before_request():
    print("\tREQUEST ENDPOINT ::"+str(request.endpoint))
    print("\tREQUEST ENDPOINT ::"+str(request.args.get('next')))
    if current_user.is_authenticated \
            and not current_user.confirmed \
            and request.endpoint \
            and request.endpoint[:5] != 'auth.' \
            and request.endpoint != 'static':
        return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('viewhome.home'))
    return render_template('Landing/unconfirmed.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            print("\tREQUEST ARGSSS :: "+str(request.args.get('next')))
            return redirect(request.args.get('next') or url_for('viewhome.home'))
        flash('Invalid username or password.')
    return render_template('Landing/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('viewhome.home'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegForm()
    if form.validate_on_submit():
        user=User(fname=form.fname.data,
        lname=form.lname.data,
        email=form.email.data,
        organization_name=form.username.data,
        password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, 'Confirm Your Account',
                   'email/auth/confirm', user=user, token=token)
        flash('A confirmation email has been sent to you by email.')
        return redirect(url_for('auth.login'))
    return render_template('Landing/entry.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('viewhome.home'))
    if current_user.confirm(token):
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('viewhome.home'))


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account',
               'email/auth/confirm', user=current_user, token=token)
    flash('A new confirmation email has been sent to you by email.')
    return redirect(url_for('viewhome.home'))
