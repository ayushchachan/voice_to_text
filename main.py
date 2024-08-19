from database import init_db
from gui import VoiceToTextApp
import tkinter as tk

def main():
    init_db()  # Initialize the database
    root = tk.Tk()
    app = VoiceToTextApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
