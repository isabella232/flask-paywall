# project/users/views.py


#################
#### imports ####
#################

import stripe

from flask import render_template, Blueprint, url_for, \
    redirect, flash, request
from flask.ext.login import login_user, logout_user, \
    login_required, current_user

from project import db, bcrypt, stripe_keys
from project.util import check_paid
from project.models import User
from project.user.forms import LoginForm, RegisterForm, StripeForm

################
#### config ####
################

stripe.api_key = stripe_keys['stripe_secret_key']

user_blueprint = Blueprint('user', __name__,)


################
#### routes ####
################

@user_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if form.validate_on_submit():
        try:
            user = User(
                email=form.email.data,
                password=form.password.data
            )
            db.session.add(user)
            db.session.commit()

            login_user(user)
            flash('You registered and are now logged in. Welcome!', 'success')

            return redirect(url_for('user.members'))
        except:
            flash('Sorry. That email and/or username already exist.', 'danger')
            return redirect(url_for('user.register'))
    return render_template('user/register.html', form=form)


@user_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(
                user.password, request.form['password']):
            login_user(user)
            flash('You are logged in. Welcome!', 'success')
            return redirect(url_for('user.members'))
        else:
            flash('Invalid email and/or password.', 'danger')
            return render_template('user/login.html', form=form)
    return render_template('user/login.html', form=form)


@user_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You are logged out. Bye!', 'success')
    return redirect(url_for('main.home'))


@user_blueprint.route('/members', methods=['GET', 'POST'])
@login_required
def members():
    form = StripeForm(request.form)
    if request.method == 'POST':
        amount = 500
        customer = stripe.Customer.create(
            email=current_user.email,
            card=request.form['stripeToken']
        )
        try:
            charge = stripe.Charge.create(
                customer=customer.id,
                amount=amount,
                currency='usd',
                description='Flask Charge'
            )
            if charge:
                User.query.filter_by(
                    email=current_user.email).update(dict(paid=True))
                db.session.commit()
                flash('Thanks for paying!', 'success')
                return redirect(url_for('user.members'))
        except stripe.CardError:
            flash('Oops. Something is wrong with your card info!', 'danger')
            return redirect(url_for('user.checkout'))
    else:
        return render_template(
            'user/members.html',
            form=form, key=stripe_keys['stripe_publishable_key'])


@user_blueprint.route('/premium')
@login_required
@check_paid
def premium():
    return render_template('user/premium.html')