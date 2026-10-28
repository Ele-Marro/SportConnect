import sqlite3

connection = sqlite3.connect("SportConnect.db")
cursor = connection.cursor()

cursor.execute("ALTER TABLE users ADD column liked_sports TEXT")

connection.commit()
connection.close()

print("settings columns added.")