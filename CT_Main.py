#Import all required classes
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, redirect, url_for, render_template, request, flash
import time

#Create the extension
db = SQLAlchemy()
# create the app
app = Flask("CT_Main")
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
# initialize the app with the extension
db.init_app(app)

# This table contains 5 fields 
# event_id - This ID is unique and will increment automatically for each record (primary key)
# epochtime - Represents epoch time in milli seconds
# fixed_station_id - Fixed station sending data
# beacon_id - Beacon 
# RSSI - Received Signal Strength Indicator (dB) 
class FixedStationData(db.Model):
    event_id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    epochtime = db.Column(db.Integer)
    fixed_station_id = db.Column(db.Integer, nullable=False)
    beacon_id = db.Column(db.Integer, nullable=False)
    RSSI = db.Column(db.Integer,nullable=False)

with app.app_context():
    db.create_all()

# Login interface to validate users
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form["username"] != "admin" or request.form["password"] != "admin":
            error = "Please enter correct credentials."
        else:
            return redirect(url_for("Contact_Tracing_Application"))
    return render_template("login.html", error=error)


# Push data URL for ESP-32 
# URL format: http://127.0.0.1:5000/PushData?fixed_station_id=101&beacon_id=201&RSSI=-30
@app.route("/PushData")
def PushData():
    fixed_station_id1 = request.args.get('fixed_station_id')
    beacon_id1 = request.args.get('beacon_id')
    RSSI1 = request.args.get('RSSI')
    new_data = FixedStationData(epochtime = int(time.time()),
               fixed_station_id=fixed_station_id1,
               beacon_id=beacon_id1,
               RSSI=RSSI1)
    db.session.add(new_data)
    db.session.commit()
    return''' 
            <h1>The language value is: {}</h1>
            <h1>The framework value is: {}</h1>
            <h1>The website value is: {}'''.format(fixed_station_id1,beacon_id1,RSSI1)

#Route for viewing Contact Tracing Application Menu
#Navigate to different URLs based on User input
@app.route("/Contact_Tracing_Application", methods=["GET", "POST"])
def Contact_Tracing_Application():
    if request.method == "GET":
        return render_template("Contact_Tracing_Application.html")
    elif request.method == "POST":

        if request.form['submit'] == 'Modify RSSI Threshold':
            return redirect(url_for('Modify_RSSI_Threshold'))
        
        elif request.form['submit'] == 'Decision Table: Fixed Station 1':
            return redirect(url_for('FixedStation1'))
        
        else:
            return redirect(url_for('login'))

#Route for Modifying RSSI thresholds (Delta RSSI and Sigma RSSI)
@app.route("/Modify_RSSI_Threshold", methods=["GET", "POST"])
def Modify_RSSI_Threshold():
    return render_template("Modify_RSSI_Threshold.html")