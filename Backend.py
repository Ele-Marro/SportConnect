import os
from time import time #importing time stamps

DATABASE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "SportConnect.db"
)

from flask import Flask, render_template, request, redirect, session, url_for  # type: ignore[reportMissingImports]
#gets tools to communicate with SQLite database
import sqlite3
#opens connection to the database file
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

# Initializes the app, creating the Flask application instance and setting up the database connection.
app = Flask(__name__)
app.secret_key = os.environ.get("SPORTCONNECT_SECRET_KEY") #a secret key is what Flask uses to protect the session data from being tampered with. It is used to sign the session cookies and ensure that they have not been modified by the client. The secret key should be kept secret and not shared with anyone, as it is used to protect sensitive information in the session data.


def cleanup_expired_activities():
    connection = sqlite3.connect("SportConnect.db")
    cursor = connection.cursor()

    try:
        cursor.execute("""
        DELETE FROM activity_participants
        WHERE activity_id IN (
            SELECT id
            FROM activity
            WHERE date < date ('now', 'localtime')
        )
        """)

        cursor.execute("""
            DELETE FROM activity
            WHERE date < date('now', 'localtime')
        """)

        connection.commit()
    finally:
        connection.close()


cleanup_expired_activities()

def init_db():
    connection = sqlite3.connect("SportConnect.db")

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_id INTEGER NOT NULL,
            sport TEXT NOT NULL,
            activity_name TEXT NOT NULL,
            date DATE NOT NULL,
            time TIME NOT NULL,
            description TEXT,
            location TEXT NOT NULL,
            participants INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (creator_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (activity_id, user_id),
            FOREIGN KEY (activity_id) REFERENCES activity(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users(id),
            FOREIGN KEY (receiver_id) REFERENCES users(id)
            )
        """)

    connection.commit()
    print("Database initialized successfully.")
    connection.close()

#self is the particular object that is being created from the class, and it allows you to access the attributes and methods of that object. In this case, self._messages is an attribute of the InMemoryMessageStore class that stores the messages in memory for the duration of the app's runtime.
#stores messages in memory for the duration of the app's runtime
#a class is like a blueprint for creating objects, and it defines the properties and behaviors that those objects will have. In this case, the InMemoryMessageStore class defines the properties and behaviors of a message store that stores messages in memory.
#an object is an instance of a class, and it represents a specific implementation of the properties and behaviors defined by that class. In this case, the message_store object is an instance of the InMemoryMessageStore class, and it represents a specific implementation of a message store that stores messages in memory.

# HOME PAGE
@app.get("/home")
def home():
    if "user_id" not in session:
        return redirect(url_for("intro"))

    user_id = session["user_id"]
    
    connection = sqlite3.connect("SportConnect.db")
    connection.row_factory = sqlite3.Row    # row factory allows a database row to be accessed as activity["activity_name"], rather than having to remember activity name is in position 3 in the row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            a.id,
            a.creator_id,
            a.sport,
            a.activity_name,
            a.date,
            a.time,
            a.location,
            a.participants,
            a.description,
            users.username AS creator_username,

            (
                SELECT COUNT(*)
                FROM activity_participants ap
                WHERE ap.activity_id = a.id
            ) AS joined_count

        FROM activity a
        JOIN users ON users.id = a.creator_id

        WHERE a.creator_id = ?

        ORDER BY a.date, a.time
    """, (user_id,))

    activities = cursor.fetchall()

    cursor.execute("""
        SELECT
            a.id,
            a.creator_id,
            a.sport,
            a.activity_name,
            a.date,
            a.time,
            a.location,
            a.description,
            a.participants AS max_players,
            users.username AS creator_username,
                        
            (
                SELECT COUNT(*)
                FROM activity_participants ap
                WHERE ap.activity_id = a.id
            ) AS joined,

            EXISTS (
                SELECT 1
                FROM activity_participants ap
                WHERE ap.activity_id = a.id
                    AND ap.user_id = ?
            ) AS has_joined

        FROM activity a
        JOIN users ON users.id = a.creator_id
        WHERE a.creator_id != ?
        ORDER BY a.created_at DESC, a.id DESC

        LIMIT 4
    """, (user_id, user_id))

    recommended = cursor.fetchall()
    connection.close()

    return render_template(
        "SportConnect.html",
        activities=activities,
        recommended=recommended
    )



@app.get("/")
def intro():
    return render_template("intro.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        if not email or not password:
            return redirect(url_for("incorrectdetails"))

        # Use the database file located alongside Backend.py
        database_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "SportConnect.db"
        )

        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()



        try:

            cursor.execute(
                "SELECT id, username, email FROM users"
            )
            users = cursor.fetchall()

            cursor.execute(
                "SELECT id, username, password_hash FROM users WHERE email = ?",
                (email,)
            )
            user = cursor.fetchone()


        finally:
            connection.close()

        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            return redirect(url_for("home"))

        return redirect(url_for("incorrectdetails"))

        

    return render_template("login.html")


@app.route("/incorrectdetails")
def incorrectdetails():
    return render_template("incorrectdetails.html")


@app.route("/createaccount", methods=["GET", "POST"])
def createaccount():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        if not username or not email or not password:
            return "Please fill in all required fields.", 400

        password_hash = generate_password_hash(password)

        connection = sqlite3.connect("SportConnect.db")
        cursor = connection.cursor()

        
        cursor.execute("SELECT id, username FROM users")


        try:
            cursor.execute("""
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
            """, (username, email, password_hash))

            connection.commit()

            session["user_id"] = cursor.lastrowid

            return redirect(url_for("home"))

        except sqlite3.IntegrityError:
            connection.rollback()
            return "That username or email may already be registered.", 400

        except sqlite3.Error as e:
            connection.rollback()
            app.logger.exception("Database error during account creation")
            return "An error occurred while creating your account.", 500

        finally:
            connection.close()

    return render_template("createaccount.html")




@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = sqlite3.connect("SportConnect.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip()

        # Check that both fields have been completed
        if not username or not email:
            cursor.execute(
                "SELECT username, email FROM users WHERE id = ?",
                (user_id,)
            )
            current_settings = cursor.fetchone()
            connection.close()

            return render_template(
                "settings.html",
                settings=current_settings,
                error="Username and email cannot be empty."
            ), 400

        # Check whether another user has the same username
        cursor.execute("""
            SELECT id FROM users
            WHERE username = ? AND id != ?
        """, (username, user_id))

        if cursor.fetchone():
            cursor.execute(
                "SELECT username, email FROM users WHERE id = ?",
                (user_id,)
            )
            current_settings = cursor.fetchone()
            connection.close()

            return render_template(
                "settings.html",
                settings=current_settings,
                error="That username is already taken."
            ), 400

        # Check whether another user has the same email
        cursor.execute("""
            SELECT id FROM users
            WHERE email = ? AND id != ?
        """, (email, user_id))

        if cursor.fetchone():
            cursor.execute(
                "SELECT username, email FROM users WHERE id = ?",
                (user_id,)
            )
            current_settings = cursor.fetchone()
            connection.close()

            return render_template(
                "settings.html",
                settings=current_settings,
                error="That email address is already in use."
            ), 400

        # Update both fields for the logged-in user
        cursor.execute("""
            UPDATE users
            SET username = ?, email = ?
            WHERE id = ?
        """, (username, email, user_id))

        connection.commit()
        connection.close()

        return redirect(url_for("settings"))

    # Display the current settings
    cursor.execute(
        "SELECT username, email FROM users WHERE id = ?",
        (user_id,)
    )
    current_settings = cursor.fetchone()
    connection.close()

    return render_template(
        "settings.html",
        settings=current_settings,
        error=None
    )



@app.get("/logout")
def logout():
    session.pop("user_id", None) #wipes out entire session data when the user logs out
    return redirect(url_for("intro"))

@app.get("/discover")
def discover():
    if "user_id" not in session:
        return redirect(url_for("intro"))
    
    user_id = session["user_id"]

    connection = sqlite3.connect("SportConnect.db")
    connection.row_factory = sqlite3.Row    # row factory allows a database row to be accessed as activity["activity_name"], rather than having to remember activity name is in position 3 in the row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            a.id,
            a.creator_id,
            a.sport,
            a.activity_name,
            a.date,
            a.time,
            a.location,
            a.participants,
            a.description,
            users.username AS creator_username,
            
            (
                SELECT COUNT(*)
                FROM activity_participants ap
                WHERE ap.activity_id = a.id
            ) AS joined,

            EXISTS (
                SELECT 1
                FROM activity_participants ap
                WHERE ap.activity_id = a.id
                    AND ap.user_id = ?
            ) AS has_joined

        FROM activity a
        JOIN users ON users.id = a.creator_id
        WHERE a.creator_id != ?
        ORDER BY a.created_at DESC, a.id DESC
    """, (user_id, user_id)) 

    activities = cursor.fetchall()
    connection.close()

    return render_template("discover.html", activities=activities)


@app.get("/joined")
def joined():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = sqlite3.connect("SportConnect.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            a.id,
            a.sport,
            a.activity_name,
            a.date,
            a.time,
            a.location,
            a.description,
            a.participants AS max_players,
            u.username AS creator_username,
            (
                SELECT COUNT(*)
                FROM activity_participants AS ap
                WHERE ap.activity_id = a.id
            ) AS joined_count
        FROM activity AS a
        JOIN activity_participants AS p
            ON p.activity_id = a.id
        JOIN users AS u
            ON u.id = a.creator_id
        WHERE p.user_id = ?
          AND a.creator_id != ?
        ORDER BY a.date, a.time
    """, (user_id, user_id))

    activities = cursor.fetchall()
    connection.close()

    return render_template("joined.html", activities=activities)



@app.route("/search_users", methods=["GET", "POST"])
def search_users():
    if "user_id" not in session:
        return redirect(url_for("intro"))

    search_query = request.form.get("username", "").strip()

    connection = sqlite3.connect("SportConnect.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, username
        FROM users
        WHERE username LIKE ?
            AND id != ?
        ORDER BY username
        LIMIT 10
    """, (f"%{search_query}%", session["user_id"]))

    users = cursor.fetchall()
    connection.close()

    return render_template(
        "messages.html",
        users=users,
        search_query=search_query,
        messages=[]
    )

@app.get("/messages")
def messages():
    if "user_id" not in session:
        return redirect(url_for("intro"))

    current_user_id = session["user_id"]
    connection = sqlite3.connect("SportConnect.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("""
        SELECT
            u.id,
            u.username,
            (
                SELECT m.content
                FROM messages AS m
                WHERE
                    (m.sender_id = u.id AND m.receiver_id = ?)
                    OR
                    (m.sender_id = ? AND m.receiver_id = u.id)
                ORDER BY m.created_at DESC, m.id DESC
                LIMIT 1
            ) AS latest_message,
            (
                SELECT m.created_at
                FROM messages AS m
                WHERE
                    (m.sender_id = u.id AND m.receiver_id = ?)
                    OR
                    (m.sender_id = ? AND m.receiver_id = u.id)
                ORDER BY m.created_at DESC, m.id DESC
                LIMIT 1
            ) AS latest_message_time
        FROM users AS u
        WHERE u.id IN (
            SELECT sender_id FROM messages WHERE receiver_id = ?            
            UNION
            SELECT receiver_id FROM messages WHERE sender_id = ?
        )
        ORDER BY latest_message_time DESC
    """, (
        current_user_id,
        current_user_id,
        current_user_id,
        current_user_id,
        current_user_id,
        current_user_id
    ))

    contacts = cursor.fetchall()
    connection.close()

    return render_template(
        "messages.html",
        messages=[],
        other_user=None,
        contacts=contacts,
        users=[],
        search_query=""
    )



@app.route("/messages/<int:user_id>", methods=["GET", "POST"]) #<...> is a dynamic route. This allows for variables to be passed within <..>
# this allows my application to identify which resource my user wants
def conversation(user_id):
    if "user_id" not in session:
            return redirect(url_for("intro"))
    current_user_id = session["user_id"]

    if current_user_id == user_id:
        return redirect(url_for("messages"))

    connection = sqlite3.connect("SportConnect.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id, username FROM users WHERE id = ?",
        (user_id,)
    )
    other_user = cursor.fetchone()

    if other_user is None:
        connection.close()
        return redirect(url_for("messages"))


    if request.method == "POST":
        content = request.form.get("message", "").strip()

        if content:
            cursor.execute("""
                INSERT INTO messages (sender_id, receiver_id, content)
                VALUES (?, ?, ?)
            """, (current_user_id, user_id, content))

            connection.commit()
        connection.close()
        return redirect(url_for("conversation", user_id=user_id))

    cursor.execute("""
    SELECT id, sender_id, receiver_id, content, created_at
    FROM messages
    WHERE (sender_id = ? AND receiver_id = ?)
        OR (sender_id = ? AND receiver_id = ?)
        ORDER BY created_at, id
""", (current_user_id, user_id, user_id, current_user_id))


    conversation_messages = cursor.fetchall()

    # Get everyone the current user has exchanged messages with
    cursor.execute("""
        SELECT
            u.id,
            u.username,
            (
                SELECT m.content
                FROM messages AS m
                WHERE
                    (m.sender_id = u.id AND m.receiver_id = ?)
                    OR
                    (m.sender_id = ? AND m.receiver_id = u.id)
                ORDER BY m.created_at DESC, m.id DESC
                LIMIT 1
            ) AS latest_message,
            (
                SELECT m.created_at
                FROM messages AS m
                WHERE
                    (m.sender_id = u.id AND m.receiver_id = ?)
                    OR
                    (m.sender_id = ? AND m.receiver_id = u.id)
                ORDER BY m.created_at DESC, m.id DESC
                LIMIT 1
            ) AS latest_message_time
        FROM users AS u
        WHERE u.id IN (
            SELECT sender_id
            FROM messages
            WHERE receiver_id = ?

            UNION

            SELECT receiver_id
            FROM messages
            WHERE sender_id = ?
        )
        ORDER BY latest_message_time DESC
    """, (
        current_user_id,
        current_user_id,
        current_user_id,
        current_user_id,
        current_user_id,
        current_user_id
    ))

    contacts = cursor.fetchall()
    connection.close()

    return render_template(
        "messages.html",
        messages=conversation_messages,
        other_user=other_user,
        contacts=contacts
    )



# CREATE ACTIVITY
@app.route("/createactivity", methods=["GET", "POST"])
def createactivity():
    if "user_id" not in session:
        return redirect(url_for("intro"))

    current_user_id = session["user_id"]

    if request.method == "POST":
            
            print("FORM DATA:", request.form)

            sport = request.form.get("sport")
            activity_name = request.form.get("activity_name")

            print("ACTIVITY NAME", activity_name)

            date = request.form.get("date")
            time = request.form.get("time")
            location = request.form.get("location")
            participants = request.form.get("participants")
            description = request.form.get("description")
            creator_id = session["user_id"]

            connection = sqlite3.connect("SportConnect.db")
            cursor = connection.cursor()

            
            cursor.execute("PRAGMA table_info(activity)") #PRAGMA is a tool to query database metadata
            # in this case, we are checking the table activity's metadata to find out data such as which columns exist/data types of columns
            # in this case, it is good to have as a temporary database debugger to catch "Table/Column not found errors"
            # these errors could happen, as we need to match form fields (sport, date, time) to column names in sqlite 
            print("ACTIVITY TABLE:", cursor.fetchall())
            

            cursor.execute("""
                        INSERT INTO activity (creator_id, sport, activity_name, date, time, location, participants, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (creator_id, sport, activity_name, date, time, location, participants, description))

            connection.commit()

            cursor.execute("SELECT * FROM activity")
            print("ACTIVITIES IN DATABASE:", cursor.fetchall())
            connection.close()

            return redirect(url_for("home"))

    return render_template("createactivity.html")




@app.post("/join/<int:activity_id>")
def join_activity(activity_id):
    if "user_id" not in session:
        return redirect(url_for("intro"))

    user_id = session["user_id"]

    connection = sqlite3.connect("SportConnect.db")
    cursor = connection.cursor()

    # Check that the activity exists and get its capacity
    cursor.execute("""
        SELECT participants
        FROM activity
        WHERE id = ?
    """, (activity_id,))

    activity = cursor.fetchone()

    if activity is None:
        connection.close()
        return redirect(url_for("home"))

    max_players = activity[0]

    # Check whether this user has already joined
    cursor.execute("""
        SELECT 1
        FROM activity_participants
        WHERE activity_id = ? AND user_id = ?
    """, (activity_id, user_id))

    if cursor.fetchone() is not None:
        connection.close()
        return redirect(url_for("home"))

    # Count the current participants
    cursor.execute("""
        SELECT COUNT(*)
        FROM activity_participants
        WHERE activity_id = ?
    """, (activity_id,))

    joined_count = cursor.fetchone()[0]

    if joined_count >= max_players:
        connection.close()
        return redirect(url_for("home"))

    # Record the user's registration
    cursor.execute("""
        INSERT INTO activity_participants (activity_id, user_id)
        VALUES (?, ?)
    """, (activity_id, user_id))

    connection.commit()
    connection.close()

    return redirect(url_for("home"))



# START FLASK
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
