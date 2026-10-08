from flask import Flask, render_template, request, redirect, url_for  # type: ignore[reportMissingImports]

# Initializes the app
app = Flask(__name__)

        )
    """)

    connection.commit()
    print("Database initialized successfully.")
    connection.close()


#self is the particular object that is being created from the class, and it allows you to access the attributes and methods of that object. In this case, self._messages is an attribute of the InMemoryMessageStore class that stores the messages in memory for the duration of the app's runtime.
#stores messages in memory for the duration of the app's runtime
class InMemoryMessageStore():
    def __init__(self):
        self._messages = [
            {"text": "Hey, how are you?", "type": "received"},
            {"text": "I'm good, thanks! How about you?", "type": "received"},
            {"text": "I'm doing well. Are you free to play basketball this weekend?", "type": "received"},
            {"text": "Yes, I am! Let's meet at the court on Saturday.", "type": "sent"}
        ]

    def get_messages(self):
        return list(self._messages)

    def add_message(self, text, message_type="sent"):
        # Add a new message to the store
        message = {"text": text, "type": message_type}

        self._messages.append(message)

        return message


message_store = InMemoryMessageStore()


# ACTIVITY STORAGE
class ActivityStore:
    def __init__(self):
        self._activities = []

    def add_activity(self, activity):
        self._activities.append(activity)

    def get_activities(self):
        return list(self._activities)


activity_store = ActivityStore()

recommended_activities = [
    {
        "id": 1,
        "sport": "Football",
        "date": "2026-10-03",
        "time": "18:00",
        "joined": 2,
        "max_players": 6,
        "has_joined": False
    },
    {
        "id": 2,
        "sport": "Badmington",
        "date": "2026-10-04",
        "time": "17:00",
        "joined": 3,
        "max_players": 4,
        "has_joined": False
    },
    {
        "id": 3,
        "sport": "Basketball",
        "date": "2026-10-05",
        "time": "19:00",
        "joined": 5,
        "max_players": 8,
        "has_joined": False
    }
]

# HOME PAGE
@app.get("/home")
def home():
    cursor.execute("""
        SELECT id, creator_id, sport, activity_name, date, time, location, participants, description
        """)

    activities = cursor.fetchall()
    connection.close()
    
    return render_template(
        "SportConnect.html",
        activities=activity_store.get_activities(),
        recommended=recommended_activities
    )

@app.get("/")
def intro():
    return render_template("intro.html")


@app.get("/login")
def login():

        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]    #this is 0 based indexing:
                                            #[0] is the first item (user's id)
            return redirect(url_for("home"))#how it works is that it takes the first value in the result

        return "Invalid email or password"
    

    return render_template("login.html")


@app.route("/createaccount", methods=["GET", "POST"])
def createaccount():

    if request.method == "POST":

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        print(username)
        print(email)
        cursor.execute("""
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        """, (username, email, password_hash))

        connection.commit()
        cursor.execute("SELECT * FROM users")

        return redirect(url_for("home"))

    return render_template("createaccount.html")

# MESSAGES
@app.get("/settings")
def settings():
    return render_template("settings.html")


def logout():
    session.pop("user_id", None)
    return redirect(url_for("intro"))

@app.get("/discover")
def discover():
    return render_template("discover.html")


@app.route("/messages", methods=["GET", "POST"])
def messages():

    if request.method == "POST":

        message = request.form.get("message", "")

        message_store.add_message(message, "sent")

        return redirect(url_for("messages"))

    return render_template(
        "messages.html",
        messages=message_store.get_messages()
    )

# CREATE ACTIVITY
@app.route("/createactivity", methods=["GET", "POST"])
def createactivity():

    if request.method == "POST":
            
            print("FORM DATA:", request.form)

            "participants": request.form.get("participants"),
            "description": request.form.get("description")
        }

        activity_store.add_activity(activity)

        return redirect(url_for("home"))
                    """, (creator_id, sport, activity_name, date, time, location, participants, description))

            connection.commit()

            cursor.execute("SELECT * FROM activity")
            print("ACTIVITIES IN DATABASE:", cursor.fetchall())
            connection.close()

            return redirect(url_for("home"))

    return render_template("createactivity.html")


@app.post("/join/<int:activity_id>")
def join_activity(activity_id):

    for activity in recommended_activities:

        if activity["id"] == activity_id:

            if not activity["has_joined"] and activity["joined"] < activity["max_players"]:
                activity["joined"] += 1
                activity["has_joined"] = True

            break

    return redirect(url_for("home"))



# START FLASK
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
