import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import json
import os

CONFIG_FILE = 'config.json'
ADMIN_USER = 'admin'
ADMIN_PASS = 'pass1234!'

# Load config
def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"email": "your@email.com", "components": {"CPU": [], "Motherboard": [], "RAM": [], "GPU": [], "PSU": [], "Case": []}}
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

class PCBuilderApp:
    def __init__(self, root):
        self.root = root
        self.root.title('PC Builder')
        self.config = load_config()
        self.show_login()

    def show_login(self):
        self.clear_window()
        frame = tk.Frame(self.root)
        frame.pack(padx=20, pady=20)
        tk.Label(frame, text='Login', font=('Arial', 16)).grid(row=0, column=0, columnspan=2, pady=10)
        tk.Label(frame, text='Username:').grid(row=1, column=0, sticky='e')
        tk.Label(frame, text='Password:').grid(row=2, column=0, sticky='e')
        username_entry = tk.Entry(frame)
        password_entry = tk.Entry(frame, show='*')
        username_entry.grid(row=1, column=1)
        password_entry.grid(row=2, column=1)
        def login():
            user = username_entry.get()
            pw = password_entry.get()
            if user == ADMIN_USER and pw == ADMIN_PASS:
                self.show_admin_panel()
            else:
                self.show_user_panel()
        tk.Button(frame, text='Login', command=login).grid(row=3, column=0, columnspan=2, pady=10)

    def show_admin_panel(self):
        self.clear_window()
        frame = tk.Frame(self.root)
        frame.pack(padx=20, pady=20)
        tk.Label(frame, text='Admin Panel', font=('Arial', 16)).pack(pady=10)
        # Email config
        email_frame = tk.Frame(frame)
        email_frame.pack(pady=5)
        tk.Label(email_frame, text='Destination Email:').pack(side='left')
        email_var = tk.StringVar(value=self.config.get('email', ''))
        email_entry = tk.Entry(email_frame, textvariable=email_var, width=30)
        email_entry.pack(side='left')
        def save_email():
            self.config['email'] = email_var.get()
            save_config(self.config)
            messagebox.showinfo('Saved', 'Email address updated!')
        tk.Button(email_frame, text='Save', command=save_email).pack(side='left', padx=5)
        # TODO: Add component management UI here
        tk.Button(frame, text='Logout', command=self.show_login).pack(pady=10)

    def show_user_panel(self):
        self.clear_window()
        frame = tk.Frame(self.root)
        frame.pack(padx=20, pady=20)
        tk.Label(frame, text='PC Builder - User', font=('Arial', 16)).pack(pady=10)
        # TODO: Add component selection and build submission UI here
        tk.Button(frame, text='Logout', command=self.show_login).pack(pady=10)

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

def main():
    root = tk.Tk()
    app = PCBuilderApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()