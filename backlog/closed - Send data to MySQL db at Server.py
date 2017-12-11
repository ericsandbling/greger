# Send data to MySQL db @ Loopia (server)

#!/usr/bin/python

# Tutorial at:
# https://www.tutorialspoint.com/python/python_database_access.htm (droped this tutorial)
# http://raspberrywebserver.com/sql-databases/using-mysql-on-a-raspberry-pi.html

import os, sys, inspect, time
import MySQLdb

def sendToGreta(timestamp,temperature):
    
    tableName = 'table_name'

    # Open database connection
    mysql_host = "host"
    mysql_user = "usr"
    mysql_pwd = "pwd"
    mysql_database = "db"
    db = MySQLdb.connect(mysql_host,mysql_user,mysql_pwd,mysql_database )
    
    # prepare a cursor object using cursor() method
    cursor = db.cursor()
    
    sqlstr = 'INSERT INTO ' + tableName + ' VALUES('
    sqlstr = sqlstr + '\'' + timestamp + '\'' + ',' + temperature + ')'
    
    print sqlstr
    
    with db:
        #cursor.execute ("""INSERT INTO temp_test values(NOW(), 18.3)""")
        cursor.execute (sqlstr)
    
        db.commit()
        print "Data committed"
        
        
    # disconnect from server
    db.close()

def main():
    
    sensorPath = '/mnt/1wire/28.099F7A060000/'
    try:
      # Get sensor data
      with open(sensorPath + 'temperature', 'r') as f:
        raw = f.read()
        temperature = float(raw)
        f.close()
  
      print("temperature = " + str(temperature))
    
    except:
      print("Oops! Something went wrong!" + sys.exc_info()[0])
      temperature = 0
  
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S") # Nice
    
    sendToGreta(timestamp, str(temperature))
    

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print 'Interrupted!'
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

# General Issues:
# =================
# 1. Error code 1045
# 1045, "Access denied for user 'greger@s182384'@'c-cdfc70d5.025-21-67626721.cust.bredbandsbolaget.se' (using password: YES)"
#
# Issue solved: user address at server update (to any).
