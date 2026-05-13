import os
import random

QUESTIONS_DIR = "questions"


def choose_quiz_file():
    """
    Let user choose a quiz file from questions directory.
    """

    try:
        files = [
            f for f in os.listdir(QUESTIONS_DIR)
            if os.path.isfile(os.path.join(QUESTIONS_DIR, f))
        ]

    except FileNotFoundError:
        print(f"Directory '{QUESTIONS_DIR}' not found.")
        return None

    if not files:
        print(f"No quiz files found in '{QUESTIONS_DIR}'.")
        return None

    print("\nAvailable Quiz Files:")

    for index, file in enumerate(files, start=1):
        print(f"{index}. {file}")

    while True:
        choice = input("\nChoose a file number: ").strip()

        try:
            choice = int(choice)

            if 1 <= choice <= len(files):
                selected_file = os.path.join(
                    QUESTIONS_DIR,
                    files[choice - 1]
                )

                print(f"\nLoaded: {files[choice - 1]}")
                return selected_file

            else:
                print("Invalid choice.")

        except ValueError:
            print("Please enter a valid number.")


def load_questions(filename):
    questions = []

    try:
        with open(filename, "r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                line = line.strip()

                # Skip empty lines
                if not line:
                    continue

                # Validate separator
                if "$$$$$" not in line:
                    print(f"Skipping malformed line {line_number}: {line}")
                    continue

                parts = line.split("$$$$$", 1)

                if len(parts) != 2:
                    print(f"Skipping malformed line {line_number}: {line}")
                    continue

                question = parts[0].strip()
                answer = parts[1].strip()

                questions.append((question, answer))

    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")

    return questions


def list_questions(questions):
    print("\n--- All Questions ---")

    for i, (question, answer) in enumerate(questions, start=1):
        print(f"{i}. {question}")
        print(f"   Answer: {answer}\n")


def start_quiz(questions):
    def print_mastered():
        # Progress summary
        mastered = sum(
            1 for q in progress.values() if q["mastered"]
        )

        total = len(questions)

        print("\n===== Progress =====")
        print(f"Mastered: {mastered}/{total}")
        print("====================\n")

    if not questions:
        print("No questions loaded.")
        return

    print("\n--- Quiz Mode ---")
    print("Type:")
    print("  y = I got it right")
    print("  n = I did not get it right\n")

    # Track state per question
    progress = {}

    for question, _ in questions:
        progress[question] = {
            "first_attempt_done": False,
            "mastered": False,
            "consecutive_correct": 0
        }

    while True:

        # Only ask non-mastered questions
        remaining_questions = [
            (q, a) for q, a in questions
            if not progress[q]["mastered"]
        ]

        if not remaining_questions:
            print("\n🎉 Congratulations! You mastered all questions.")
            break

        random.shuffle(remaining_questions)

        for question, answer in remaining_questions:

            state = progress[question]

            print("\n--------------------------------")
            print(f"Question: {question}")

            _ = input("Press Enter to show answer...")

            print(f"Answer: {answer}")

            while True:
                result = input(
                    "Did you get it right? (y/n): "
                ).strip().lower()

                if result not in ("y", "n"):
                    print("Please enter 'y' or 'n'.")
                    continue

                # FIRST ATTEMPT LOGIC
                if not state["first_attempt_done"]:

                    state["first_attempt_done"] = True

                    # Got first attempt correct => instantly mastered
                    if result == "y":
                        state["mastered"] = True
                        print("✅ Mastered on first attempt!")

                    else:
                        state["consecutive_correct"] = 0
                        print(
                            "❌ You'll now need "
                            "2 consecutive correct answers."
                        )
                    print_mastered()
                    break

                # AFTER FIRST FAILURE LOGIC
                else:

                    if result == "y":
                        state["consecutive_correct"] += 1

                        remaining = (
                            2 - state["consecutive_correct"]
                        )

                        if remaining <= 0:
                            state["mastered"] = True
                            print(
                                "✅ Mastered with "
                                "2 consecutive correct answers!"
                            )
                        else:
                            print(
                                f"Good! Need {remaining} more "
                                "consecutive correct answer(s)."
                            )

                    else:
                        # Reset streak on wrong answer
                        state["consecutive_correct"] = 0
                        print(
                            "❌ Streak reset. Need "
                            "2 consecutive correct answers."
                        )
                    # Progress summary
                    print_mastered()
                    break


def main():

    selected_file = choose_quiz_file()

    if not selected_file:
        return

    questions = load_questions(selected_file)

    while True:
        print("\nQuiz Trainer")
        print("1. List all questions")
        print("2. Take a quiz")
        print("3. Choose another quiz file")
        print("4. Reload current file")
        print("5. Exit")

        choice = input("Choose an option: ")

        if choice == "1":
            list_questions(questions)

        elif choice == "2":
            start_quiz(questions)

        elif choice == "3":

            selected_file = choose_quiz_file()

            if selected_file:
                questions = load_questions(selected_file)

        elif choice == "4":
            questions = load_questions(selected_file)
            print("Questions reloaded.")

        elif choice == "5":
            print("Goodbye!")
            break

        else:
            print("Invalid choice, try again.")


if __name__ == "__main__":
    main()