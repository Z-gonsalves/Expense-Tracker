import tkinter as tk
from tkinter import messagebox
import os
import sys
import sqlite3
from tkinter import ttk
import tkinter.font as tkfont
import subprocess
from PIL import Image, ImageTk  # Add PIL for better image handling

# Use a database path relative to this script's directory
DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")  # stores users in workspace directory

# Create/connect to database
def init_database():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users
            (username TEXT PRIMARY KEY,
            password TEXT NOT NULL)''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

# Add this custom message box class
class CustomMessageBox:
    def __init__(self, title, message, type_="info"):
        self.popup = tk.Toplevel()
        self.popup.title(title)
        
        # Calculate position for center of screen
        window_width = 300
        window_height = 150
        screen_width = self.popup.winfo_screenwidth()
        screen_height = self.popup.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.popup.geometry(f'{window_width}x{window_height}+{x}+{y}')
        
        # Configure style
        self.popup.configure(bg='#f0f0f0')
        self.popup.grab_set()  # Make window modal
        
        # Icon and colors based on message type
        if type_ == "error":
            icon = "❌"
            color = "#ff4d4d"
        elif type_ == "warning":
            icon = "⚠️"
            color = "#ffa500"
        else:  # info/success
            icon = "✅"
            color = "#32cd32"
            
        # Create and pack widgets
        frame = tk.Frame(self.popup, bg='#f0f0f0')
        frame.pack(expand=True, fill='both', padx=20, pady=10)
        
        # Icon label
        icon_font = tkfont.Font(size=30)
        icon_label = tk.Label(frame, text=icon, font=icon_font, bg='#f0f0f0')
        icon_label.pack(pady=(5, 10))
        
        # Message label
        message_font = tkfont.Font(size=10)
        msg_label = tk.Label(frame, text=message, wraplength=250, 
                           font=message_font, bg='#f0f0f0')
        msg_label.pack(pady=5)
        
        # OK button
        style = ttk.Style()
        style.configure('Custom.TButton', padding=5)
        ok_button = ttk.Button(frame, text="OK", style='Custom.TButton',
                             command=self.popup.destroy)
        ok_button.pack(pady=10)
        
        # Add hover effect to button
        ok_button.bind('<Enter>', lambda e: ok_button.configure(style='Custom.TButton'))
        ok_button.bind('<Leave>', lambda e: ok_button.configure(style='Custom.TButton'))

# Function to register a new user
def register():
    username = entry_username.get()
    password = entry_password.get()
    
    if not username or not password:
        CustomMessageBox("Warning", "Please enter both username and password.", "warning")
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        CustomMessageBox("Success", "Your account has been created! You can now log in.")
        entry_username.delete(0, tk.END)
        entry_password.delete(0, tk.END)
    except sqlite3.IntegrityError:
        CustomMessageBox("Error", "This username is already taken. Please choose another.", "error")
    finally:
        conn.close()

# Function to login
def login():
    username = entry_username.get()
    password = entry_password.get()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        CustomMessageBox("Success", f"Welcome back, {username}! You have successfully logged in.")
        root.withdraw()  # Hide login window
        try:
            # Launch the expense tracker using the same Python interpreter
            expense_tracker_path = os.path.join(os.path.dirname(__file__), "expence(again).py")
            subprocess.Popen([sys.executable, expense_tracker_path])
        except Exception as e:
            CustomMessageBox("Error", f"Failed to launch expense tracker: {str(e)}", "error")
            root.deiconify()  # Show login window again if there's an error
    else:
        CustomMessageBox("Error", "Incorrect username or password. Please try again.", "error")

# GUI setup
root = tk.Tk()
root.title("Login/Register")
root.geometry("1275x745")  # Reduced size
root.configure(bg="#FFFFFF")

# Background Frame
bg_frame = tk.Frame(root, width=550, height=832)
bg_frame.place(x=0, y=0)

# Load background image using PIL
try:
    background_img_path = os.path.join(os.path.dirname(__file__), "leaf.png")
    if os.path.exists(background_img_path):
        # Open image with PIL
        pil_image = Image.open(background_img_path)
        # Resize image if needed
        pil_image = pil_image.resize((550, 832), Image.Resampling.LANCZOS)
        # Convert to PhotoImage
        background_img = ImageTk.PhotoImage(pil_image)
        bg_label = tk.Label(bg_frame, image=background_img)
        bg_label.place(relwidth=1, relheight=1)
        # Keep a reference to prevent garbage collection
        bg_label.image = background_img
    else:
        print(f"Warning: Background image not found at {background_img_path}")
except Exception as e:
    print(f"Error loading background image: {str(e)}")

# Main Frame
frame = tk.Frame(root, bg="#FFFFFF", width=720, height=745)
frame.place(x=550, y=0)

# Title
label_title = tk.Label(frame, text="Hello, Guys!", font=("Istok Web", 50, "bold"), fg="#7A999C", bg="#FFFFFF")
label_title.place(x=105, y=56)

# Login Label
login_label = tk.Label(frame, text="Login/Register", font=("Istok Web", 28, "bold"), fg="#5F7C8D", bg="#FFFFFF")
login_label.place(x=262, y=178)

# Input Fields
username_label = tk.Label(frame, text="Enter your username", font=("Istok Web", 19), fg="#5F7C8D", bg="#FFFFFF")
username_label.place(x=173, y=336)
entry_username = tk.Entry(frame, font=("Istok Web", 19), width=25, bg="#FFFFFF", bd=0)
entry_username.place(x=173, y=382)
tk.Frame(frame, width=427, height=2, bg="#5F7C8D").place(x=133, y=415)

password_label = tk.Label(frame, text="Enter Password", font=("Istok Web", 19), fg="#5F7C8D", bg="#FFFFFF")
password_label.place(x=173, y=443)
entry_password = tk.Entry(frame, font=("Istok Web", 19), width=25, bg="#FFFFFF", bd=0, show="*")
entry_password.place(x=173, y=485)
tk.Frame(frame, width=427, height=2, bg="#5F7C8D").place(x=133, y=515)

# Login Button
btn_login = tk.Button(frame, text="Login", font=("Istok Web", 19, "bold"), bg="#5F7C8D", fg="white", width=15, height=1, command=login)
btn_login.place(x=173, y=546)

# Register Button
btn_register = tk.Button(frame, text="Register", font=("Istok Web", 19, "bold"), bg="#7A999C", fg="white", width=15, height=1, command=register)
btn_register.place(x=173, y=615)

# Exit Button
btn_exit = tk.Button(frame, text="Exit", font=("Istok Web", 19, "bold"), bg="#c0392b", fg="white", width=15, height=1, command=root.destroy)
btn_exit.place(x=173, y=680)

# Add this line before root.mainloop()
init_database()

root.mainloop()
