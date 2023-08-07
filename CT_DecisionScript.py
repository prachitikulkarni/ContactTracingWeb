import mysql.connector
import time
import random
import networkx as nx
import matplotlib.pyplot as plt
from datetime import datetime
import CT_Config

mydb = mysql.connector.connect(
  host="localhost",
  user="admin",
  password="password",
  database="ContactTracingDatabase"
)

end_epoch = int(time.time())
start_epoch = end_epoch - 120
sigma_RSSI = CT_Config.sigma_RSSI
delta_RSSI = CT_Config.delta_RSSI


mycursor = mydb.cursor()
mycursor.execute("DELETE FROM DecisionTemp")
mydb.commit()

mycursor.execute("SELECT DISTINCT beacon_id from FixedStationData ORDER BY beacon_id")
unique_beacon = mycursor.fetchall()

mycursor.execute("SELECT DISTINCT fixed_station_id from FixedStationData ORDER BY fixed_station_id")
unique_fixed_station = mycursor.fetchall()


stage1 = []
# Algorithm Stage 1
for station in unique_fixed_station: 
    for i in range(len(unique_beacon)):
        for j in range(i+1,len(unique_beacon)):
            if(unique_beacon[i][0] is not None and station[0] is not None):
                sql = "SELECT AVG(RSSI) FROM FixedStationData WHERE epochtime BETWEEN %s AND %s AND fixed_station_id = %s AND beacon_id=%s"
                print("station:",station[0]," unique beacon:",unique_beacon[i][0])
                value = (start_epoch,end_epoch,int(station[0]), int(unique_beacon[i][0]))
                mycursor.execute(sql, value)
                RSSI_1 = mycursor.fetchone()
                print("Beacon ID:",str(unique_beacon[i][0]),"RSSI = ",str(RSSI_1))
                
                sql = "SELECT AVG(RSSI) FROM FixedStationData WHERE epochtime BETWEEN %s AND %s AND fixed_station_id = %s AND beacon_id=%s"
                value = (start_epoch,end_epoch,int(station[0]), int(unique_beacon[j][0]))  
                mycursor.execute(sql, value)  
                RSSI_2 = mycursor.fetchone()
                print("Beacon ID:",str(unique_beacon[j][0]),"RSSI = ",str(RSSI_2))

                if (RSSI_1[0] is not None and RSSI_2[0] is not None):
                    if( float(RSSI_1[0]) >= sigma_RSSI or float(RSSI_2[0]) >= sigma_RSSI ):
                        if(abs(float(RSSI_1[0]) - float(RSSI_2[0])) <= delta_RSSI):
                            print("Station ",str(station[0]),"confirms ",str(unique_beacon[i][0])," and ",str(unique_beacon[j][0])," are in proximity")
                            vote = 1
                        else:
                            print("Station ",str(station[0]),"confirms ",str(unique_beacon[i][0])," and ",str(unique_beacon[j][0])," are not in proximity")
                            vote = -1
                    else:
                        print("Station ",str(station[0]),"cannot confirm proximity between ",str(unique_beacon[i][0])," and ",str(unique_beacon[j][0]))
                        vote = 0
                else:
                    print("Station ",str(station[0]),"cannot confirm proximity between ",str(unique_beacon[i][0])," and ",str(unique_beacon[j][0]))
                    vote = 0
                sql = "INSERT INTO DecisionTemp (fixed_station_id, beacon1, beacon2, vote) VALUES (%s, %s, %s, %s)"
                val = (station[0], unique_beacon[i][0], unique_beacon[j][0],vote)
                mycursor.execute(sql, val)
                mydb.commit()

# Algorithm Stage 2
mycursor.execute("SELECT beacon1, beacon2, SUM(vote) FROM DecisionTemp GROUP BY beacon1, beacon2")
get_decison = mycursor.fetchall()

for row in get_decison:
    if (row[2] > 0):
        str = "Yes"
    elif( row[2] < 0):
        str = "No"
    else:
        str = "Not able to Determine"

    sql = "INSERT INTO DecisionTable (timestamp, beacon1, beacon2, sumofvotes, proximity) VALUES (%s, %s, %s, %s, %s)"
    val = (datetime.fromtimestamp(start_epoch),row[0],row[1],row[2],str)
    mycursor.execute(sql, val)
    mydb.commit()


mycursor.execute("SELECT beacon1, beacon2, sumofvotes FROM DecisionTable")
rows = mycursor.fetchall()
graph = nx.Graph()

for row in rows:
    beacon1, beacon2,sumofvotes = row
    graph.add_node(beacon1)
    graph.add_node(beacon2)
    if sumofvotes > 0:  # Change the condition based on your proximity criteria
        graph.add_edge(beacon1, beacon2)

# Draw the graph
pos = nx.spring_layout(graph)
nx.draw_networkx(graph, pos=pos, with_labels=True)

# Show the graph
plt.show()



            










