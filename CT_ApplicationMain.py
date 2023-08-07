# Import all required classes
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy import *
from flask import Flask, redirect, url_for, render_template, session, request, flash
import time
import mysql.connector
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_svg import FigureCanvasSVG
import tkinter as tk
import CT_Config


mydb = mysql.connector.connect(
    host="localhost",
    user="admin",
    password="password",
    database="ContactTracingDatabase",
    autocommit=True,
)
mycursor = mydb.cursor()

mycursor.close()
mydb.close()

mydb = mysql.connector.connect(
    host="localhost",
    user="admin",
    password="password",
    database="ContactTracingDatabase",
    autocommit=True,
)
mycursor = mydb.cursor()
# Reopen the connection

app = Flask("CT_ApplicationMain")


# Login interface to validate users
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if (
            request.form["username"] != CT_Config.username
            or request.form["password"] != CT_Config.password
        ):
            error = "Please enter correct credentials."
        else:
            return redirect(url_for("Contact_Tracing_Application"))

    return render_template("CT_Login.html", error=error)


# Push data URL for ESP-32
# URL format: http://127.0.0.1:5000/PushData?fixed_station_id=101&beacon_id=201&RSSI=-30
@app.route("/PushData", methods=["GET", "POST"])
def PushData():
    if request.method == "POST" or request.method == 'GET':
        fixed_station_id1 = request.args.get("fixed_station_id")
        beacon_id1 = request.args.get("beacon_id")
        RSSI1 = request.args.get("RSSI")

        sql = "INSERT INTO FixedStationData (epochtime, fixed_station_id, beacon_id, RSSI ) VALUES (%s, %s, %s, %s)"
        val = (int(time.time()), fixed_station_id1, beacon_id1, RSSI1)
        mycursor.execute(sql, val)

        mydb.commit()
        return """ 
                <h1>Fixed Station ID: {}</h1>
                <h1>Beacon ID: {}</h1>
                <h1>RSSI: {}""".format(fixed_station_id1, beacon_id1, RSSI1),200


# Route for viewing Contact Tracing Application Menu
# Navigate to different URLs based on User input
@app.route("/Contact_Tracing_Application", methods=["GET", "POST"])
def Contact_Tracing_Application():
    if request.method == "GET":
        return render_template("CT_Menu.html")
    elif request.method == "POST":
        if request.form["submit"] == "Modify RSSI Threshold":
            return redirect(url_for("Modify_RSSI_Threshold"))

        elif request.form["submit"] == "View Fixed Station Data":
            return redirect(url_for("FixedStation101"))

        elif request.form["submit"] == "Decision Table: Final":
            return redirect(url_for("DecisionTable"))

        elif request.form["submit"] == "Proximity Network Graph":
            return redirect(url_for("ContactGraph"))

        elif request.form["submit"] == "Trace Beacon":
            return redirect(url_for("BeaconSpecificGraph"))

        else:
            return redirect(url_for("login"))


# Route for Modifying RSSI thresholds (Delta RSSI and Sigma RSSI)
@app.route("/Modify_RSSI_Threshold", methods=["GET", "POST"])
def Modify_RSSI_Threshold():
    if request.method == "GET":
        return render_template("CT_ModifyThreshold.html")
    elif request.method == "POST":
        CT_Config.sigma_RSSI = float(request.form["sigma_RSSI"])
        CT_Config.delta_RSSI = float(request.form["delta_RSSI"])
        print(CT_Config.sigma_RSSI)
        print(CT_Config.delta_RSSI)
        return render_template("CT_ModifyThreshold.html")


# Route for Displaying Fixed Station 101 Data
@app.route("/FixedStation101", methods=["GET", "POST"])
def FixedStation101():
    mycursor.execute(
        "SELECT DISTINCT fixed_station_id from FixedStationData ORDER BY fixed_station_id"
    )
    unique_fixed_station = mycursor.fetchall()

    mycursor.execute("SELECT * FROM FixedStationData")
    FixedStation101 = mycursor.fetchall()

    if request.method == "POST":
        # if request.form['submit'] == 'submit':
        selected_fixed_station_id = int(request.form["selected_item"])
        query = "SELECT * FROM FixedStationData WHERE fixed_station_id =%s"
        value = (selected_fixed_station_id,)
        mycursor.execute(query, value)
        FixedStation101 = mycursor.fetchall()

    # Render the HTML template with the graph image
    return render_template(
        "CT_DisplayTable.html",
        data=unique_fixed_station,
        title="Fixed Station",
        fixstationdata=FixedStation101,
    )


# Route for Displaying Final Decision Table
@app.route("/DecisionTable", methods=["GET", "POST"])
def DecisionTable():
    mycursor.execute(
        "SELECT DISTINCT beacon_id from FixedStationData ORDER BY beacon_id"
    )
    unique_beacon_id = mycursor.fetchall()
    unique_beacon_id.append(["All"])

    mycursor.execute("SELECT * FROM DecisionTable")
    DecisionTable = mycursor.fetchall()

    if request.method == "POST":
        selected_beacon_id = request.form["selected_item"]
        if selected_beacon_id == "All":
            mycursor.execute("SELECT * FROM  DecisionTable")
        else:
            query = "SELECT * FROM DecisionTable WHERE beacon1 = %s or beacon2 = %s"
            value = (
                selected_beacon_id,
                selected_beacon_id,
            )
            mycursor.execute(query, value)

        DecisionTable = mycursor.fetchall()
    # Render the HTML template with the graph image
    return render_template(
        "CT_DisplayDecisionTable.html",
        data=unique_beacon_id,
        title="Decision Table",
        DecisionData=DecisionTable,
    )


# Route for displaying Contact Graph
@app.route("/ContactGraph", methods=["GET", "POST"])
def ContactGraph():
    mycursor.execute(
        "SELECT DISTINCT beacon_id from FixedStationData ORDER BY beacon_id"
    )
    unique_beacon = mycursor.fetchall()


    mycursor.execute("SELECT beacon1, beacon2, sumofvotes FROM DecisionTable")
    rows = mycursor.fetchall()

    graph = nx.Graph()

    for row in unique_beacon:
        graph.add_node(row[0])

    for row in rows:
        beacon1, beacon2, sumofvotes = row
        # graph.add_node(beacon1)
        # graph.add_node(beacon2)
        if sumofvotes > 0:  # Change the condition based on your proximity criteria
            graph.add_edge(beacon1, beacon2)

    plt.clf()
    # Generate graph visualization
    pos = nx.spring_layout(graph)  # Layout algorithm (you can change it if needed)

    nodes_with_edges = [
        node for node, degree in dict(graph.degree()).items() if degree > 0
    ]
    nodes_without_edges = [
        node for node, degree in dict(graph.degree()).items() if degree == 0
    ]

    # Get the screen resolution
    root = tk.Tk()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.destroy()

    # Calculate the figure size based on the screen resolution
    width = screen_width / 150.0
    height = screen_height / 150.0
    figsize = (width, height)

    # Set the figure size
    fig, ax = plt.subplots(figsize=figsize)

    # Color for nodes without edges
    nx.draw_networkx(
        graph,
        pos=pos,
        with_labels=True,
        node_color="red",
        edge_color="black",
        node_size=1000,
        width=2,
        font_size=10,
        alpha=0.7,
        nodelist=nodes_with_edges,
    )

    # Color for nodes without edges
    nx.draw_networkx(
        graph,
        pos=pos,
        with_labels=True,
        node_color="green",
        edge_color="black",
        node_size=1000,
        width=2,
        font_size=10,
        alpha=0.7,
        nodelist=nodes_without_edges,
    )

    plt.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)

    # Save the graph as an image
    plt.savefig("static/proximity_network_graph.png")

    # Render the HTML template with the graph image
    return render_template("CT_Graph.html", data=unique_beacon)


@app.route("/BeaconList", methods=["GET", "POST"])
def BeaconSpecificGraph():
    # Execute query to fetch the parameters from the table
    mycursor.execute(
        "SELECT DISTINCT beacon_id from FixedStationData ORDER BY beacon_id"
    )
    unique_beacon = mycursor.fetchall()
    if request.method == "POST":
        # if request.form['submit'] == 'submit':
        beacon_id = request.form["selected_item"]
        plot_graph(beacon_id)
        return redirect(url_for("BeaconSpecificGraph"))

    # Render the HTML template with the graph image
    return render_template("CT_BeaconList.html", data=unique_beacon)


def plot_graph(beacon_id):
    if beacon_id is None:
        mycursor.execute("SELECT beacon1, beacon2, sumofvotes FROM DecisionTable")
        mycursor.fetchall()
    else:
        query = "SELECT beacon1, beacon2, sumofvotes FROM DecisionTable WHERE beacon1 = %s OR beacon2 = %s"
        value = (beacon_id, beacon_id)
        mycursor.execute(query, value)
        rows = mycursor.fetchall()
    
    mycursor.execute(
        "SELECT DISTINCT beacon_id from FixedStationData ORDER BY beacon_id"
    )
    unique_beacon = mycursor.fetchall()
    
    graph = nx.Graph()

    for row in unique_beacon:
        graph.add_node(row[0])

    for row in rows:
        beacon1, beacon2, sumofvotes = row
        # graph.add_node(beacon1)
        # graph.add_node(beacon2)
        if sumofvotes > 0:  # Change the condition based on your proximity criteria
            graph.add_edge(beacon1, beacon2)

    plt.clf()
    # Generate graph visualization
    pos = nx.spring_layout(
        graph, k=0.75
    )  # Layout algorithm (you can change it if needed)

    nodes_with_edges = [
        node for node, degree in dict(graph.degree()).items() if degree > 0
    ]
    nodes_without_edges = [
        node for node, degree in dict(graph.degree()).items() if degree == 0
    ]

    # Get the screen resolution
    root = tk.Tk()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.destroy()

    # Calculate the figure size based on the screen resolution
    width = screen_width / 150.0
    height = screen_height / 150.0
    figsize = (width, height)

    # Set the figure size
    fig, ax = plt.subplots(figsize=figsize)

    # Color for nodes without edges
    nx.draw_networkx(
        graph,
        pos=pos,
        with_labels=True,
        node_color="red",
        edge_color="black",
        node_size=1000,
        width=2,
        font_size=10,
        alpha=0.7,
        nodelist=nodes_with_edges,
    )

    # Color for nodes without edges
    nx.draw_networkx(
        graph,
        pos=pos,
        with_labels=True,
        node_color="green",
        edge_color="black",
        node_size=1000,
        width=2,
        font_size=10,
        alpha=0.7,
        nodelist=nodes_without_edges,
    )

    plt.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)

    # Save the graph as an image
    plt.savefig("static/beacon_network_graph.png")
