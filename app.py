import os
import random

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from flask_session import Session

app = Flask(__name__)

app.secret_key = "super-secret-key"

# -----------------------------------------
# SERVER SIDE SESSION STORAGE
# -----------------------------------------

app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False

Session(app)

QUESTIONS_DIR = "questions"


# ---------------------------------------------------
# Load Available Quiz Files
# ---------------------------------------------------

def get_quiz_files():

    if not os.path.exists(QUESTIONS_DIR):
        return []

    return [
        f for f in os.listdir(QUESTIONS_DIR)
        if os.path.isfile(os.path.join(QUESTIONS_DIR, f))
    ]


# ---------------------------------------------------
# Load Questions
# ---------------------------------------------------

def load_questions(filename):

    questions = []

    filepath = os.path.join(
        QUESTIONS_DIR,
        filename
    )

    try:

        with open(
            filepath,
            "r",
            encoding="utf-8"
        ) as file:

            lines = file.readlines()

        i = 0

        while i < len(lines):

            line = lines[i].rstrip()

            # skip empty
            if not line.strip():
                i += 1
                continue

            # ---------------------------------
            # OLD FORMAT
            # question $$$$$ answer
            # ---------------------------------

            if "$$$$$" in line:

                parts = line.split(
                    "$$$$$",
                    1
                )

                question = parts[0].strip()
                answer = parts[1].strip()

                questions.append({
                    "question": question,
                    "answer": answer
                })

                i += 1
                continue

            # ---------------------------------
            # NEW FORMAT
            # question
            # $$$$$
            # multiline answer
            # ---------------------------------

            question = line

            i += 1

            if i >= len(lines):
                break

            if lines[i].strip() != "$$$$$":
                continue

            i += 1

            answer_lines = []

            while i < len(lines):

                current = lines[i]

                # blank line ends multiline answer
                if not current.strip():
                    break

                answer_lines.append(
                    current.rstrip()
                )

                i += 1

            answer = "\n".join(
                answer_lines
            ).strip()

            questions.append({
                "question": question,
                "answer": answer
            })

            i += 1

    except FileNotFoundError:
        pass

    return questions


# ---------------------------------------------------
# Home Page
# ---------------------------------------------------

@app.route("/")
def index():

    files = get_quiz_files()

    return render_template(
        "index.html",
        files=files
    )


# ---------------------------------------------------
# All Questions Page
# ---------------------------------------------------

@app.route("/all")
def all_questions():

    qa_list = []

    filename = session.get("filename")

    if not filename:
        return redirect(url_for("index"))

    questions = load_questions(filename)

    random.shuffle(questions)

    for q in questions:

        qa_list.append({
            "question": q["question"],
            "answer": q["answer"]
        })

    return render_template(
        "all.html",
        qa_list=qa_list
    )


# ---------------------------------------------------
# Start Quiz
# ---------------------------------------------------

@app.route("/start/<path:filename>")
def start_quiz(filename):

    questions = load_questions(filename)

    random.shuffle(questions)

    progress = {}

    for idx, q in enumerate(questions):

        progress[str(idx)] = {
            "first_attempt_done": False,
            "mastered": False,
            "consecutive_correct": 0
        }

    # store lightweight session data
    session["filename"] = filename
    session["progress"] = progress
    session["question_order"] = questions
    session["current_index"] = 0

    return redirect(url_for("quiz"))


# ---------------------------------------------------
# Quiz Page
# ---------------------------------------------------

@app.route("/quiz", methods=["GET", "POST"])
def quiz():

    filename = session.get("filename")

    if not filename:
        return redirect(url_for("index"))

    questions = session.get("question_order", [])

    progress = session.get("progress", {})

    current_index = session.get("current_index", 0)

    if not questions:
        return redirect(url_for("index"))

    # Filter non-mastered questions
    remaining_questions = []

    for idx, q in enumerate(questions):

        if not progress[str(idx)]["mastered"]:

            remaining_questions.append({
                "idx": idx,
                "question": q
            })

    if not remaining_questions:
        return redirect(url_for("result"))

    # Reset index if needed
    if current_index >= len(remaining_questions):
        current_index = 0

    current = remaining_questions[current_index]

    q_idx = str(current["idx"])

    current_question = current["question"]

    question_text = current_question["question"]
    answer_text = current_question["answer"]

    state = progress[q_idx]

    message = ""

    if request.method == "POST":

        result = request.form.get("result")

        # FIRST ATTEMPT
        if not state["first_attempt_done"]:

            state["first_attempt_done"] = True

            if result == "y":

                state["mastered"] = True

                message = (
                    "✅ Mastered on first attempt!"
                )

            else:

                state["consecutive_correct"] = 0

                message = (
                    "❌ Need 2 consecutive correct answers."
                )

        else:

            if result == "y":

                state["consecutive_correct"] += 1

                remaining = (
                    2 - state["consecutive_correct"]
                )

                if remaining <= 0:

                    state["mastered"] = True

                    message = (
                        "✅ Mastered with 2 consecutive correct answers!"
                    )

                else:

                    message = (
                        f"Good! Need {remaining} more consecutive correct."
                    )

            else:

                state["consecutive_correct"] = 0

                message = (
                    "❌ Streak reset. Need 2 consecutive correct answers."
                )

        session["progress"] = progress
        session["current_index"] = current_index + 1

        return render_template(
            "quiz.html",
            question=question_text,
            answer=answer_text,
            show_answer=True,
            message=message,
            mastered_count=sum(
                1 for x in progress.values()
                if x["mastered"]
            ),
            total_count=len(questions)
        )

    return render_template(
        "quiz.html",
        question=question_text,
        answer=answer_text,
        show_answer=False,
        message=message,
        mastered_count=sum(
            1 for x in progress.values()
            if x["mastered"]
        ),
        total_count=len(questions)
    )


# ---------------------------------------------------
# Result Page
# ---------------------------------------------------

@app.route("/result")
def result():

    filename = session.get("filename")

    if not filename:
        return redirect(url_for("index"))

    questions = load_questions(filename)

    return render_template(
        "result.html",
        total=len(questions)
    )


# ---------------------------------------------------
# Main
# ---------------------------------------------------

if __name__ == "__main__":

    app.run(
        debug=True,
        use_reloader=False,
        host="0.0.0.0",
        port=5000
    )