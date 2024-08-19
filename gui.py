import tkinter as tk
from tkinter import messagebox
from database import *
import threading
import speech_recognition as sr
from datetime import datetime
import wave
import pyaudio

class VoiceToTextApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Offline Voice to Text Converter")

        # Chat-like GUI components with scrollbar
        self.chat_box = tk.Text(root, height=20, width=50, wrap=tk.WORD)
        self.chat_box.pack(pady=10, padx=10)
        scrollbar = tk.Scrollbar(root, command=self.chat_box.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_box.config(yscrollcommand=scrollbar.set)

        # Button layout in a frame
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)

        self.start_button = tk.Button(button_frame, text="Start Recording", command=self.start_recording)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(button_frame, text="Stop Recording", command=self.stop_recording, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.history_button = tk.Button(button_frame, text="Show History", command=self.show_history)
        self.history_button.pack(side=tk.LEFT, padx=5)

        # Initialize Recognizer and other variables
        self.recognizer = sr.Recognizer()
        self.is_recording = False
        self.audio_thread = None
        self.mic = None  # Placeholder for the Microphone object
        self.frames = []  # List to store audio frames
        self.transcriptions = []  # List to store transcriptions
        self.start_time = None  # Variable to store start time of recording

        # Ensure microphone is released on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Check microphone access
        self.check_microphone()

        # Allow navigation and selection, but prevent text modification
        self.chat_box.bind("<Key>", self.handle_key_event)
        self.chat_box.bind("<Button-1>", self.hide_context_menu)  # Hide context menu on left click
        self.chat_box.bind("<Button-3>", self.hide_context_menu)  # Hide context menu on right click

        # Enable right-click and copy functionality
        self.chat_box.bind("<Button-3>", self.show_context_menu)

        # Define tags for styling
        self.chat_box.tag_configure("user", foreground="blue", justify="left")
        self.chat_box.tag_configure("system", foreground="green", justify="right")

    def check_microphone(self):
        try:
            self.mic = sr.Microphone()
            with self.mic as source:
                self.recognizer.adjust_for_ambient_noise(source)  # Adjust for ambient noise
        except OSError as e:
            if "No Default Input Device Available" in str(e):
                messagebox.showerror("Microphone Error", "No microphone detected. Please connect a microphone and try again.")
                self.start_button.config(state=tk.DISABLED)
            else:
                messagebox.showerror("Microphone Error", f"Error accessing microphone: {e}")
                self.start_button.config(state=tk.DISABLED)

    def start_recording(self):
        self.is_recording = True
        self.start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Capture the start time
        self.start_button.config(state=tk.DISABLED, bg='red', text='Recording...')
        self.stop_button.config(state=tk.NORMAL)
        self.display_text("Recording started...", is_system=True)

        # Clear previous frames and transcriptions
        self.frames = []
        self.transcriptions = []

        # Start background thread for recording
        self.audio_thread = threading.Thread(target=self.record_audio)
        self.audio_thread.start()

    def stop_recording(self):
        self.is_recording = False
        self.start_button.config(state=tk.NORMAL, bg=self.root.cget('bg'), text='Start Recording')
        self.stop_button.config(state=tk.DISABLED)

        # Combine all transcriptions into a single string and display them
        combined_transcription = " ".join(self.transcriptions)  # Combine all transcriptions
        self.display_text(combined_transcription, is_system=False)
        
        stop_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Save the combined transcription with the start and stop times
        save_transcription(combined_transcription, self.start_time, stop_time)

        # Append the "Recording stopped" message only after displaying the combined transcription
        self.display_text("Recording stopped.", is_system=True)


    def record_audio(self):
        self.audio_file = "recording.wav"  # Save the recording as 'recording.wav'
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)

        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source)  # Adjust for ambient noise
            while self.is_recording:
                data = stream.read(1024)
                self.frames.append(data)

        stream.stop_stream()
        stream.close()
        p.terminate()

        # Save the recorded audio to a .wav file
        with wave.open(self.audio_file, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(44100)
            wf.writeframes(b''.join(self.frames))

        # Perform speech recognition on the entire recording after it's finished
        with sr.AudioFile(self.audio_file) as source:
            audio = self.recognizer.record(source)  # Record the entire file
            try:
                text = self.recognizer.recognize_google(audio)
                self.transcriptions.append(text)  # Store the transcription
                self.display_text(text, is_system=False)
            except sr.UnknownValueError:
                self.display_text("Could not understand audio.", is_system=True)
            except sr.RequestError as e:
                self.display_text(f"Could not request results from the speech recognition service; {e}", is_system=True)
            except Exception as e:
                self.display_text(f"An error occurred: {e}", is_system=True)


    def display_text(self, text, is_system=False):
        """Display text in the chat box with different colors and alignment."""
        if is_system:
            timestamp = datetime.now().strftime("%H:%M:%S")
            message = f"{timestamp} - {text}\n"
            self.chat_box.insert(tk.END, message, "system")
        else:
            message = f"{text}\n"
            self.chat_box.insert(tk.END, message, "user")
        
        # Limit the chat box to last 100 lines
        if int(self.chat_box.index('end-1c').split('.')[0]) > 100:
            self.chat_box.delete('1.0', '2.0')

        self.chat_box.see(tk.END)

    def show_history(self):
        history_window = tk.Toplevel(self.root)
        history_window.title("Transcription History")

        history_text = tk.Text(history_window, height=20, width=60)
        history_text.pack(pady=10)

        # Fetch and sort records in ascending order by timestamp
        records = fetch_history()
        records = sorted(records, key=lambda record: record[0])  # Assuming the first element is the timestamp

        # Display each record with start and stop timestamps
        for i, record in enumerate(records):
            start_time = record[0]  # Assuming the timestamp is the first element
            transcription = record[1]  # Assuming the transcription is the second element

            # Format the display with timestamps and transcription
            history_text.insert(tk.END, f"Recording {i+1}:\n")
            history_text.insert(tk.END, f"Start Time: {start_time}\n")
            history_text.insert(tk.END, f"Transcription:\n{transcription}\n\n")
        
        # Enable scrolling
        scrollbar = tk.Scrollbar(history_window, command=history_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        history_text.config(yscrollcommand=scrollbar.set)

    def on_closing(self):
        # Stop recording if still active
        if self.is_recording:
            self.is_recording = False
            if self.audio_thread is not None:
                self.audio_thread.join()  # Wait for the thread to finish

        # Ensure microphone is released
        if self.mic is not None:
            self.mic = None

        # Clean up resources and close the application
        self.root.destroy()

    def handle_key_event(self, event):
        """Handle key events to allow navigation and selection but prevent modification."""
        allowed_keys = ["Left", "Right", "Up", "Down", "Shift_L", "Shift_R"]
        if event.keysym not in allowed_keys:
            return "break"  # Prevent modification keys (e.g., Backspace, Delete)

    def show_context_menu(self, event):
        """Display a context menu for copying text."""
        self.hide_context_menu(event)  # Ensure any existing context menu is hidden first
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Copy", command=self.copy_selection)
        self.context_menu.post(event.x_root, event.y_root)

    def copy_selection(self):
        """Copy the selected text to the clipboard."""
        try:
            selected_text = self.chat_box.selection_get()
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
        except tk.TclError:
            pass  # No text selected
        self.context_menu.unpost()  # Hide the context menu after copying

    def hide_context_menu(self, event):
        """Hide the context menu if it is displayed."""
        if hasattr(self, 'context_menu'):
            self.context_menu.unpost()

if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceToTextApp(root)
    root.mainloop()
