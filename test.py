from flask import Flask, redirect, url_for, render_template, request, flash

app = Flask("test")


# Route for handling the login page logic
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form["username"] != "admin" or request.form["password"] != "admin":
            error = "Please enter correct credentials."
        else:
            return redirect(url_for("Contact_Tracing_Application"))
    return render_template("login.html", error=error)


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


@app.route("/Modify_RSSI_Threshold", methods=["GET", "POST"])
def Modify_RSSI_Threshold():
    return render_template("Modify_RSSI_Threshold.html")

@app.route("/FixedStation1")
def FixedStation1():
    return "In Fixed Station 1"
