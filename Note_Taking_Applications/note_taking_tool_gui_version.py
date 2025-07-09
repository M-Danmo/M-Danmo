import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
import datetime
import json 
import os
import time
import wikipedia
import nltk
from nltk.corpus import wordnet
nltk.download('wordnet')

# ───────────────── GUI SETUP ─────────────────
class FlashcardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Flashcard App")

        # title label
        self.label = tk.Label(root, text="Flashcard App", font=("Helvetica", 18, "bold"))
        self.label.pack(pady=10)

        # button to add new flashcard
        self.add_button = tk.Button(root, text="➕ Add Flashcard", width=20, command=self.make_flashcard)
        self.add_button.pack(pady=5)

        # button to review existing flashcards
        self.review_button = tk.Button(root, text="🧠 Review Flashcards", width=20, command=self.review_flashcards)
        self.review_button.pack(pady=5)

        # quit button
        self.quit_button = tk.Button(root, text="❌ Exit", width=20, command=root.quit)
        self.quit_button.pack(pady=20)

        # search feature
        self.search_button = tk.Button(root, text="🔍 Search Flashcards", width=20, command=self.search_flashcards)
        self.search_button.pack(pady=5)

        # edit flashcard feature
        self.edit_button = tk.Button(root, text="✏️ Edit Flashcard", width=20, command=self.edit_flashcard_prompt)
        self.edit_button.pack(pady=5)

        # delete flashcard feature
        self.delete_button = tk.Button(root, text="🗑️ Delete Flashcard", width=20, command=self.delete_flashcard_prompt)
        self.delete_button.pack(pady=5)

        # check info about a term (uses wordnet and wikipedia)
        self.info_button = tk.Button(root, text="❓ Check Term Info", width=20, command=self.check_term_info)
        self.info_button.pack(pady=5)

    def search_flashcards(self):
        # ask for term and search flashcards
        term = simpledialog.askstring("Search", "Enter a term to search in questions or answers:")
        if not term:
            return
        matches = []
        for fc in GetFlashcards():
            if term.lower() in fc.get_flashcard_question().lower() or term.lower() in fc.get_flashcard_answer().lower():
                matches.append(f"Q: {fc.get_flashcard_question()}\nA: {fc.get_flashcard_answer()}")
        if matches:
            messagebox.showinfo("Matches Found", "\n\n".join(matches))
        else:
            messagebox.showinfo("No Match", "No matching flashcards found.")

    def edit_flashcard_prompt(self):
        # edit a flashcard by entering its question
        flashcards = GetFlashcards()
        questions = [fc.get_flashcard_question() for fc in flashcards]
        target = simpledialog.askstring("Edit Flashcard", f"Enter the exact question to edit:\n\nAvailable:\n" + "\n".join(questions))
        if not target:
            return
        for fc in flashcards:
            if fc.get_flashcard_question().strip().lower() == target.strip().lower():
                new_q = simpledialog.askstring("Edit", "Enter new question (leave blank to keep current):") or fc.get_flashcard_question()
                new_a = simpledialog.askstring("Edit", "Enter new answer (leave blank to keep current):") or fc.get_flashcard_answer()
                fc.flashcard_question = new_q
                fc.flashcard_answer = new_a
                SaveAllFlashcards(flashcards)
                messagebox.showinfo("Updated", "Flashcard updated successfully.")
                return
        messagebox.showwarning("Not Found", "No flashcard with that question found.")

    def delete_flashcard_prompt(self):
        # delete a flashcard by entering its question
        flashcards = GetFlashcards()
        questions = [fc.get_flashcard_question() for fc in flashcards]
        target = simpledialog.askstring("Delete Flashcard", f"Enter the exact question to delete:\n\nAvailable:\n" + "\n".join(questions))
        if not target:
            return
        for fc in flashcards:
            if fc.get_flashcard_question().strip().lower() == target.strip().lower():
                flashcards.remove(fc)
                SaveAllFlashcards(flashcards)
                messagebox.showinfo("Deleted", "Flashcard deleted successfully.")
                return
        messagebox.showwarning("Not Found", "No flashcard with that question found.")

    def check_term_info(self):
        # check definition and wiki summary
        term = simpledialog.askstring("Term Info", "Enter the term you'd like to check:")
        if not term:
            return
        try:
            meaning = wordnet.synsets(term)
            definition = meaning[0].definition() if meaning else "Definition not found."

            try:
                summary = wikipedia.summary(term, sentences=2)
                messagebox.showinfo("Definition & Wikipedia", f"{definition}\n\nWikipedia:\n{summary}")
            except wikipedia.exceptions.DisambiguationError as e:
                options = e.options[:5]
                messagebox.showinfo("Ambiguous Term", f"{definition}\n\nPlease be more specific. Options:\n" + "\n".join(options))
            except wikipedia.exceptions.PageError:
                messagebox.showinfo("Definition Only", f"{definition}\n\nNo Wikipedia page found.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to find info: {e}")

    def make_flashcard(self):
        # create and save a new flashcard
        question = simpledialog.askstring("Question", "Enter the flashcard question:")
        if not question:
            return
        answer = simpledialog.askstring("Answer", "Enter the flashcard answer:")
        if not answer:
            return
        confirm = messagebox.askyesno("Save Flashcard", "Would you like to save this flashcard?")
        if confirm:
            flashcard = Flashcard(answer, question)
            flashcard.SaveFlashCard()
            messagebox.showinfo("Saved", "Flashcard saved successfully.")

    def review_flashcards(self):
        # start review session
        flashcards = GetFlashcards()
        if not flashcards:
            messagebox.showwarning("No Cards", "No flashcards available to review.")
            return

        sorted_cards = sorted(flashcards, key=lambda fc: (datetime.datetime.now() - fc.get_last_used()).days, reverse=True)
        self.review_index = 0
        self.review_cards = sorted_cards

        self.review_window = tk.Toplevel(self.root)
        self.review_window.title("Review Flashcards")

        self.question_label = tk.Label(self.review_window, text="", font=("Helvetica", 14, "bold"), wraplength=400)
        self.question_label.pack(pady=10)

        self.answer_label = tk.Label(self.review_window, text="", font=("Helvetica", 12), wraplength=400)
        self.answer_label.pack(pady=10)

        self.next_button = tk.Button(self.review_window, text="Next", command=self.show_next_flashcard)
        self.next_button.pack(pady=10)

        self.show_next_flashcard()

    def show_next_flashcard(self):
        # show question first, then delay, then show answer
        if self.review_index >= len(self.review_cards):
            messagebox.showinfo("Done", "No more flashcards to review.")
            self.review_window.destroy()
            return

        current_card = self.review_cards[self.review_index]
        self.question_label.config(text=f"Q: {current_card.get_flashcard_question()}")
        self.answer_label.config(text="(Thinking...)")

        delay = {"high": 10, "medium": 5, "low": 3}.get(current_card.get_priority(), 3)
        self.review_index += 1

        threading.Thread(target=self.delayed_show_answer, args=(current_card, delay)).start()

    def delayed_show_answer(self, flashcard, delay):
        # waits then shows the answer
        time.sleep(delay)
        flashcard.use_flashcard()
        self.answer_label.config(text=f"A: {flashcard.get_flashcard_answer()}")

# ─────────────── Flashcard Object ───────────────
class Flashcard:
    def __init__(self, flashcard_answer, flashcard_question):
        self.last_used = datetime.datetime.now()
        self.date_created = datetime.datetime.now()
        self.flashcard_answer = flashcard_answer
        self.flashcard_question = flashcard_question

    def get_last_used(self):
        return self.last_used

    def get_date_created(self):
        return self.date_created

    def get_flashcard_answer(self):
        return self.flashcard_answer

    def get_flashcard_question(self):
        return self.flashcard_question

    def use_flashcard(self):
        self.last_used = datetime.datetime.now()
        return [self.flashcard_answer, self.flashcard_question]

    def get_priority(self):
        delta_days = (datetime.datetime.now() - self.last_used).days
        if delta_days >= 10:
            return "high"
        elif delta_days >= 5:
            return "medium"
        else:
            return "low"

    @staticmethod
    def from_dict(data):
        fc = Flashcard(data["flashcard_answer"], data["flashcard_question"])
        fc.last_used = datetime.datetime.fromisoformat(data["last_used"])
        fc.date_created = datetime.datetime.fromisoformat(data["date_created"])
        return fc

    def SaveFlashCard(self):
        flashcard = {
            "flashcard_question": self.get_flashcard_question(),
            "flashcard_answer": self.get_flashcard_answer(),
            "last_used": self.get_last_used().isoformat(),
            "date_created": self.get_date_created().isoformat()
        }

        FILE_PATH = "storage.json"

        if os.path.exists(FILE_PATH):
            with open(FILE_PATH, "r") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []
        else:
            data = []

        data.append(flashcard)
        with open(FILE_PATH, "w") as f:
            json.dump(data, f, indent=2)

        print("Flashcard saved successfully.")

# ─────────────── Storage Functions ───────────────
def SaveAllFlashcards(flashcard_list):
    FILE_PATH = "storage.json"
    data = []
    for fc in flashcard_list:
        data.append({
            "flashcard_question": fc.get_flashcard_question(),
            "flashcard_answer": fc.get_flashcard_answer(),
            "last_used": fc.get_last_used().isoformat(),
            "date_created": fc.get_date_created().isoformat()
        })
    with open(FILE_PATH, "w") as f:
        json.dump(data, f, indent=2)

def GetFlashcards():
    FILE_PATH = "storage.json"
    flashcards = []

    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r") as f:
            try:
                data = json.load(f)
                for item in data:
                    flashcard = Flashcard.from_dict(item)
                    flashcards.append(flashcard)
            except json.JSONDecodeError:
                print("Error loading flashcards — file may be corrupted or empty.")

    return flashcards

# ─────────────── Run the App ───────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = FlashcardApp(root)
    root.mainloop()
