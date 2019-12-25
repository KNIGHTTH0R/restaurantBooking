import os
from flask import Flask, json, flash, jsonify, redirect, render_template, request, session, url_for
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import requests
import urllib.request, json
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import sqlite3
from datetime import datetime
from datetime import timedelta
from wtforms import Form, BooleanField, StringField, PasswordField, validators




app = Flask(__name__)
app.secret_key = 'm0De0qs1EP5uymYzyBzn@B2BQ'
app.config['TEMPLATES_AUTO_RELOAD'] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

conn = sqlite3.connect('restaurant.db')
db = conn.cursor()

@app.route('/', methods = ['POST', 'GET'])
def index():


    error = ""
    date = 0
    time = 0
    dateTime = 0
    firstName = ""
    lastName = ""
    numberOfGuests = 0
    phone = ""
    email = ""
    tableNumber = ""
    formDate = None
    tables = None
    booking = None
    bookingTime = None
    available = ""

    if(request.method == 'GET'):
        if(request.args.get("date")):
            formDate = request.args.get("date")
        else:
            formDate = datetime.now().strftime('%d.%m.%Y')

        tables = db.execute("SELECT * FROM reservation WHERE date = ? ORDER BY time", (formDate,))
        tables = db.fetchall()


    if(request.method == 'POST'):

        dateAndTime = request.form.get("date")
        firstName = request.form.get("firstName")
        lastName = request.form.get("lastName")
        email = request.form.get("email")
        phone = request.form.get("phone")
        numberOfGuests = request.form.get("guest")
        tableNumber = request.form.get("tableN")

        if(not firstName or not lastName):
            error = "Please fill in first or last name"
            return redirect(url_for("apology", message = error))

        #use date and time variable as separate entities and place them into database, make two fields to make same table
        # booked more times during day or even same customer
        if(dateAndTime):
            process = str(dateAndTime).split(None)
            date = process[0]
            time = process[1]
            error = ""
        else:
            error = "Please fill in date"
            return redirect(url_for("apology", message = error))

        seatings = db.execute("SELECT * FROM seatings WHERE tableNumber = ?", (tableNumber,))
        seatings = db.fetchone()

        if(int(seatings[2]) < int(numberOfGuests)):
            error = "table capacity is less than desired guest number"
            return redirect(url_for("apology", message = error))
        else:
            pass
        # this is if table hasn't been booked and there is nothing in database to compare to tableNumber !

        availableFrom = datetime.strptime(time, '%H:%M') + timedelta(hours=2)
        bookingTime = datetime.strptime(time, '%H:%M')

        i = (date, tableNumber)
        booking = db.execute("SELECT * FROM reservation WHERE date = ? AND tableNumber = ? ORDER BY time", i)
        booking = db.fetchall()

        timeMinus = datetime.strptime(time, '%H:%M') - timedelta(hours=2)
        timePlus = datetime.strptime(time, '%H:%M') + timedelta(hours=2)

        bookingStart = list()
        for b in booking:
            bookingStart.append(b[7])


# this is a bookingStart list of all time of arrival for bookings for same table and date, to test if the user can book given table
        for i in bookingStart:
            if(datetime.strptime(i, '%H:%M') >= timeMinus and datetime.strptime(time, '%H:%M') <= timePlus):
                error = "The desired table is already booked - check AVAILABLE FROM time"
                return redirect(url_for("apology", message = error))






        params = (firstName, lastName, email, phone, date, tableNumber, time, numberOfGuests, availableFrom.strftime("%H:%M")) #wrap availableFrom in str()
        db.execute("INSERT INTO reservation VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)", params)
        conn.commit()
        return redirect("/")

# debug is not visible in index.html as the page refreshes with redirect after database insert, comment it out if needed
    return render_template("index.html", formDate = formDate, tables = tables, tableNumber = tableNumber, time = time, date = date, firstName = firstName, lastName = lastName, numberOfGuests = numberOfGuests, email = email, phone = phone)

@app.route('/apology', methods = ['POST', 'GET'])
def apology():
    message = ""

    if(request.method == "GET"):
        message = request.args.get("message")

    return render_template("apology.html", message = message)

@app.route('/search', methods = ['POST', 'GET'])
def search():

# get user input, search first name or last name to find all bookings ordered by date, spilt input to first, last name one is enough
    userInput = ""

    row = ""

    if(request.method == "GET"):
        userInput = request.args.get("name")

        process = str(userInput).split(None)
        if( len(process) > 1 ):
            firstN = process[0]
            lastN = process[1]
            i = (firstN, lastN)
            rowG = db.execute("SELECT firstName, lastName, phone, numberOfGuests, date, time FROM reservation WHERE firstName = ? COLLATE NOCASE AND lastName = ? COLLATE NOCASE ORDER BY date", i)
            rowG = db.fetchall()
            return jsonify(rowG)
        else:
            i = (userInput, userInput)
            if(userInput):
                rowG = db.execute("SELECT firstName, lastName, phone, numberOfGuests, date, time FROM reservation WHERE firstName LIKE ? OR lastName LIKE ? ORDER BY date", i)
                rowG = db.fetchall()

                return jsonify(rowG)
            #return json.dumps({"`booking":rowG})

    if(request.method == "POST"):
        userInput = request.form.get("name")

        process = str(userInput).split(None)
        if( len(process) > 1 ):
            firstN = process[0]
            lastN = process[1]
            i = (firstN, lastN)
            row = db.execute("SELECT firstName, lastName, phone, numberOfGuests, date, time FROM reservation WHERE firstName = ? COLLATE NOCASE AND lastName = ? COLLATE NOCASE ORDER BY date", i)
            row = db.fetchall()
        else:
            wildUser = str(userInput) + '%'
            i = (wildUser, wildUser)
            if(userInput):
                row = db.execute("SELECT firstName, lastName, phone, numberOfGuests, date, time FROM reservation WHERE firstName LIKE ? OR lastName LIKE ? ORDER BY date", i)
                row = db.fetchall()

    return render_template("search.html", row = row)



@app.route('/about', methods = ['POST', 'GET'])
def about():


    return render_template("about.html")




@app.route('/delete', methods = ['POST', 'GET'])
def delete():



    if(request.method == "POST"):
        fullName = request.form.get("fullName")
        date = request.form.get("date")
        dateOnly = date.split(None)
        dateOfBooking = dateOnly[2]

        tableNumber = request.form.get("tableNumber")
        tn = tableNumber.split(None)
        tableN = tn[1]
        time = request.form.get("time")
        t = time.split(None)
        timeOnly = t[0]

        process = fullName.split(None)
        firstN = process[1]
        lastN = process[2]
        i = (firstN, lastN, dateOfBooking, tableN, timeOnly)
        db.execute("DELETE FROM reservation WHERE firstName = ? AND lastName = ? AND date = ? AND tableNumber = ? AND time = ?", i)
        conn.commit()
        return redirect("/")


    return render_template("index.html", timeOnly = timeOnly)

@app.route('/update', methods = ['POST', 'GET'])
def update():

# 1. gather data from form to update and hidden data what to update or who
# 2. process data and return success or error to user, use same test like insert booking, final is UPDATE db.commit()

    return render_template("index.html")

@app.route('/foodOrder', methods = ['POST', 'GET'])
def foodOrder():

    fullName = request.form.get("fullName")


    return render_template("foodOrder.html", fullName = fullName)
