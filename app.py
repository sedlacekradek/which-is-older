from flask import Flask, render_template, session
import csv
import random
import time
import statistics
import secrets

# - - - FLASK INITIATION - - -
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)


# - - - HELPER FUNCTIONS - - -
def load_file():
    """"
    reads csv file of given category and returns list (name, date, picture path),
    takes file path from session variable
    """
    loaded_file = []
    with open(session["data_file"], 'r') as file:
        reader = csv.DictReader(file, skipinitialspace=True)
        for row in reader:
            loaded_file.append(row)
    return loaded_file


def calc_average():
    """"
    returns average score from scores.csv
    """
    with open("static/database/scores.csv", 'r') as file:
        reader = csv.DictReader(file, skipinitialspace=True)
        scores = [int(row["score"]) for row in reader]
    if len(scores) != 0:
        average_score = round(statistics.mean(scores), 2)  # rounded to 2 decimal numbers
        return average_score
    else:
        return 0  # edge case, returns 0 if no scores found


def convert_date(string_date):
    """
    converts string to date object, takes input of string dd/mm/yyyy
    """
    date = time.strptime(string_date, "%d/%m/%Y")
    return date


def append_score(score):
    """
    updates score file with current score + current date after game over
    """
    with open('static/database/scores.csv', 'a') as file:
        file.write(f"\n{score}")


def is_repeated(item1, item2, recent):
    if len(recent) > 5:
        session["recent"].pop(0)
        session["recent"].pop(0)
    if item1 in recent or item2 in recent:
        return True
    else:
        session["recent"].append(item1)
        session["recent"].append(item2)
        return False


def load_pics():
    """
    randomly picks 2 different items and updates session variables
    """
    session["guess_list"] = load_file()  # loads database of items according to the category
    session["item1"] = random.choice(session["guess_list"])
    session["item2"] = random.choice(session["guess_list"])
    # makes sure 2 different random items are picked and pictures have not been shown recently
    if session["item1"] == session["item2"] or is_repeated(session["item1"], session["item2"], session["recent"]) is True:
        return load_pics()
    else:
        # relative file path to the picture
        session[
            "pic1"] = f"{session['image_dir']}/{session['item1']['picture']}"  # image_dir = f"/static/images/{category}"
        session["pic2"] = f"{session['image_dir']}/{session['item2']['picture']}"
        # concert date from string to object
        session["date1"] = convert_date(session["item1"]["date"])
        session["date2"] = convert_date(session["item2"]["date"])
        # saves name of the item in session data
        session["name1"] = session['item1']["name"]
        session["name2"] = session['item2']["name"]
        # sets the correct answer
        if session["date1"] < session["date2"]:
            session["correct_answer"] = 1  # pic 1 is older
        if session["date1"] > session["date2"]:
            session["correct_answer"] = 2  # pic 2 is older
        if session["date1"] == session["date2"]:
            session["correct_answer"] = 3  # both pics are same -> both answers are correct


def caption(show_caption=False):
    """
    shows or hides picture caption
    """
    if show_caption:  # caption inserted in html with "|safe" tag to correctly show <br>
        session["caption1"] = f"{session['item1']['name']}<br>{session['item1']['date']}"
        session["caption2"] = f"{session['item2']['name']}<br>{session['item2']['date']}"
    else:
        session["caption1"] = ""
        session["caption2"] = ""


@app.route("/go-home")
def go_home():
    """
    redirects to the homepage
    """
    return render_template("/snippets/go-home.html")


@app.route("/close-modal")
def close_modal():
    """
    closes modal window
    """
    return render_template("/snippets/close-modal.html")


@app.route("/timer-animation")
def timer_animation():
    """
    triggers animation of timer going down, takes 2.8s
    """
    return render_template("/snippets/timer-animation.html")


@app.route("/wheel-animation")
def wheel_animation():
    """
    triggers animation when user spins the wheel, takes 6s; wheel spins 3 times and stops at random result determined by spin_wheel()
    """
    return render_template("snippets/wheel-animation.html", rotation=f"{session['result'] + 1080}deg")


@app.route("/win-message")
def win_message():
    """
    defines message shown to user in modal if an extra life was won
    """
    return render_template("/snippets/win-message.html")


@app.route("/loss-message")
def loss_message():
    """
    defines message shown to user in modal if game over
    """
    return render_template("/snippets/loss-message.html", score=session["score"])


@app.route("/enable-button")
def enable_button():
    """
    enables spin button
    """
    return render_template("/snippets/enable-button.html")


#  - - -GAME FLOW FUNCTIONS - - -
@app.route("/")
def home():
    return render_template("index.html", average=calc_average())


@app.route("/play/<category>")
def play(category):
    session["score"] = 0
    session["data_file"] = f"static/database/{category}.csv"  # sets data file based on category
    session["image_dir"] = f"/static/images/{category}"  # sets image path based on category
    session["correct_answer"] = 0  # answer checked against this (0 for empty, 1 upper pic, 2 lower pic, 3 same date)
    session["date1"] = None  # dates in dd/mm/yyyy format
    session["date2"] = None
    session["name1"] = ""
    session["name2"] = ""
    session["pic1"] = ""
    session["pic2"] = ""
    session["caption1"] = ""
    session["caption2"] = ""
    session["recent"] = []
    return render_template("play.html", show_modal="False")


@app.route("/modal")
def show_modal():
    """
    pops up the modal window
    """
    return render_template("snippets/modal.html", pic1=session['pic1'], caption1=session['caption1'],
                           pic2=session['pic2'], caption2=session['caption2'],
                           score=session['score'])


@app.route("/check-answer/<answer>")
def check_answer(answer):
    """
    checks if user answer is correct and triggers subsequent functions
    """
    if int(answer) == session["correct_answer"] or session["correct_answer"] == 3:
        # correct answer
        session["score"] += 1
        caption(show_caption=True)
        return render_template("snippets/check-answer.html", pic1=session['pic1'], caption1=session['caption1'],
                               pic2=session['pic2'], caption2=session['caption2'],
                               score=session['score'])
    else:
        # wrong answer
        caption(show_caption=True)
        return show_modal()


@app.route("/spin-wheel")
def spin_wheel():
    """
    spin the wheel and evaluate the result
    """
    possible_results = [22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5]
    winning_numbers = [22.5, 112.5, 202.5, 292.5]
    session["result"] = random.choice(possible_results)
    if session["result"] in winning_numbers:
        return render_template("snippets/spin-wheel-win.html")
    else:
        # if not a winning number
        append_score(session["score"])  # adds score to the csv score file
        return render_template("snippets/spin-wheel-loss.html")


@app.route("/change-pics")
def change_pics():
    """
    shows 2 new pictures to user
    """
    load_pics()
    caption(show_caption=False)
    return render_template("snippets/change-pics.html", pic1=session['pic1'], caption1=session['caption1'],
                           pic2=session['pic2'], caption2=session['caption2'],
                           score=session['score'])


# - - - TO TEST LOCALLY - - -
if __name__ == "__main__":
    from waitress import serve
    print("localhost:8080")
    serve(app, host='0.0.0.0', port=8080)