import sqlite3
import os, sys

path_to_db = os.path.dirname(os.path.abspath(__file__))
conn = sqlite3.connect(f"{path_to_db}/paths.db") 
cursor = conn.cursor()

try:
    param = sys.argv[1]
except:
    param = None

if param == "users":
    cursor.execute("SELECT DISTINCT user FROM paths")
    print(len(cursor.fetchall()))
elif param == "files":
    cursor.execute("SELECT COUNT(path) FROM paths")
    print(cursor.fetchall()[0][0])
elif param == "good":
    cursor.execute("SELECT COUNT(path) FROM paths WHERE result == ''")
    print(cursor.fetchall()[0][0])
elif param == "bad":
    cursor.execute("SELECT COUNT(path) FROM paths WHERE result != ''")
    print(cursor.fetchall()[0][0])
else:
    print("no parametr")
