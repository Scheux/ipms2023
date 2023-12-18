import tkinter as tk
from tkinter import filedialog
import json


# Function to handle file selection
def select_file():
    file_path = filedialog.askopenfilename()
    # Add your code to handle the selected file here
    # Set the path in settings.json
    settings = {"serverconfig_file": file_path, "default_config_file": "default_servers.json"}  # Set the serverconfig_file key with the file_path value
    with open("settings.json", "w") as file:
        json.dump(settings, file)

# Function to handle saving settings
def save_settings():
    # Add your code to save the settings here
    pass

# Create the main window
window = tk.Tk()

# Set the window title
window.title("Settings Menu")

# Set the window size
window.geometry("200x50")

# Create the file select button
file_select_button = tk.Button(window, text="Select File", command=select_file)
file_select_button.pack()

# Run the main loop
window.mainloop()
