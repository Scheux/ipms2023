import tkinter as tk
from tkinter import filedialog
import json, sys, os


class SecureTk(tk.Tk):
    def applicationSupportsSecureRestorableState(self):
        return True

# Function to handle file selection
def select_file():
    try:
        file_path = filedialog.askopenfilename()
        # Validate the selected file
        if not os.path.isfile(file_path):
            tk.messagebox.showerror("Error", "Invalid file selected")
            return
        # Set the path in settings.json
        settings = {"serverconfig_file": file_path, "default_config_file": "default_servers.json"}
        with open("settings.json", "w") as file:
            json.dump(settings, file)
        tk.messagebox.showinfo("Success", "File selected successfully")
    except Exception as e:
        tk.messagebox.showerror("Error", str(e))

# Function to handle saving settings
def save_settings():
    # Add your code to save the settings here
    pass

# Function to exit the program
def exit_program():
    sys.exit()

# Create the main window
window = SecureTk()

# Set the window title
window.title("Settings Menu")

# Set the window size
window.geometry("200x100")

# Create the file select button
file_select_button = tk.Button(window, text="Select File", command=select_file)
file_select_button.pack()

# Create the exit button
exit_button = tk.Button(window, text="Exit", command=exit_program)
exit_button.pack()

# Run the main loop
window.mainloop()
