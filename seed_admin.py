from flask_bcrypt import Bcrypt
import mysql.connector

conn = mysql.connector.connect(user="root", password="Marc0s.2o2%+", database="topics")
cursor = conn.cursor()
bcrypt = Bcrypt()

hashed_pw = bcrypt.generate_password_hash("Mila.2017").decode("utf-8")

cursor.execute("""
    INSERT INTO auth_users (email, password_hash, first_name, last_name, role)
    VALUES (%s, %s, %s, %s, %s)
""", ("admin@example.com", hashed_pw, "System", "Admin", "admin"))
conn.commit()
cursor.close()
conn.close()
