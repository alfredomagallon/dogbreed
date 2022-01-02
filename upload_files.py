import psycopg2
import os
from datetime import datetime

# Upload images and breeds to the database
# The script deletes the existing data, but is somehow prepared to only append new data instead, with slight modifications

start_time = datetime.now()
print("Connecting to PostgreSQL database ...")

conn = psycopg2.connect('host=' + str(os.environ.get("DOGBREEDDB_ADDR")) +' port=' + str(os.environ.get("DOGBREEDDB_PORT")) +
                        ' dbname=dogbreed' + 
                        ' user=' + str(os.environ.get("DOGBREEDDB_USER")) + ' password=' + str(os.environ.get("DOGBREEDDB_PASS")))

end_time = datetime.now()
print('... connected in {}.'.format(end_time-start_time))

cursor = conn.cursor()

start_time = datetime.now()
print("Deleting current breed names and pictures ...")

sql = "DELETE FROM pictures"
cursor.execute(sql)

sql = "DELETE FROM breeds"
cursor.execute(sql)

conn.commit()

end_time = datetime.now()
print('... deletion complete in {}.'.format(end_time-start_time))

start_time = datetime.now()
print("Scanning pictures folder to upload breed names ...")

for dirpath, dirnames, filenames in os.walk("./images"):
        
    for dirname in sorted(dirnames):

        sql = "SELECT id FROM breeds WHERE name='" + dirname + "'"
        cursor.execute(sql)

        result = cursor.fetchall()

        if len(result) == 0:

            sql = "SELECT max(id)+1 AS nextid FROM breeds"
            cursor.execute(sql)
            result = cursor.fetchall()
            if result[0][0] == None:
                nextid = 0
            else:
                nextid = result[0][0]

            print ("Uploading", dirname)
            sql = "INSERT INTO breeds (id, name) VALUES (" + str(nextid) + ",'" + dirname + "')"
            cursor.execute(sql)

conn.commit()

end_time = datetime.now()
print('... breed names uploaded in {}.'.format(end_time-start_time))

start_time = datetime.now()
print("Scanning pictures folder to upload pictures...")

for dirpath, dirnames, filenames in sorted(os.walk("./images")):

    for filename in sorted(filenames):

        if (filename!=".DS_Store") and ("_resized" in filename):
        
            breed_name = dirpath.rsplit("/",1)[1]

            sql = "SELECT id FROM breeds WHERE name='" + breed_name + "'"
            cursor.execute(sql)

            breed_id = cursor.fetchall()[0][0]

            sql = "SELECT id FROM pictures WHERE breed_id=" + str(breed_id) + " AND name='" + filename + "'"

            cursor.execute(sql)
            result = cursor.fetchall()

            if len(result) == 0:
                sql = "SELECT MAX(id)+1 FROM pictures WHERE breed_id=" + str(breed_id)
                cursor.execute(sql)
                result = cursor.fetchall()
                if result[0][0] == None:
                    nextid = 0
                else:
                    nextid = result[0][0]
                f = open(os.path.join(dirpath, filename),'rb')
                filedata = f.read()
                print ("Uploading", dirpath + "/" + filename)
                sql = "INSERT INTO pictures (breed_id, id, name, picture) VALUES (" + str(breed_id) + "," + str(nextid) + ",'" + filename + "',%s)"
                cursor.execute(sql, [filedata])

conn.commit()

end_time = datetime.now()
print('... pictures uploaded in {}.'.format(end_time-start_time))

start_time = datetime.now()

print("Disconnecting from PostgreSQL database")

cursor.close()
conn.close()

end_time = datetime.now()
print('... disconnected in {}.'.format(end_time-start_time))
