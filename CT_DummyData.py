import mysql.connector
import time
import random

mydb = mysql.connector.connect(
  host="localhost",
  user="admin",
  password="password",
  database="ContactTracingDatabase"
)

mycursor = mydb.cursor()
while True:
  sql = "INSERT INTO FixedStationData (epochtime, fixed_station_id, beacon_id, RSSI) VALUES (%s, %s, %s, %s)"
  val = (int(time.time()), random.randrange(101, 103), random.randrange(901,910), random.randrange(-90,-60))
  time.sleep(1)
  mycursor.execute(sql, val)
  mydb.commit()
  print("Data inserted")
  


