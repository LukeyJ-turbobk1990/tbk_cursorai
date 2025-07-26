import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import json
import os
import re
import smtplib
from email.message import EmailMessage

CONFIG_FILE = 'config.json'
ADMIN_USER = 'admin'
ADMIN_PASS = 'pass1234!'

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = 'your_gmail@gmail.com'  # Set your sending email here
SMTP_PASS = 'your_app_password'      # Set your app password here

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

        # Component management
        comp_frame = tk.Frame(frame)
        comp_frame.pack(pady=10)
        tk.Label(comp_frame, text='Manage Components', font=('Arial', 12)).pack()
        cat_var = tk.StringVar(value='CPU')
        cat_menu = ttk.Combobox(comp_frame, textvariable=cat_var, values=list(self.config['components'].keys()), state='readonly')
        cat_menu.pack(pady=5)

        list_frame = tk.Frame(comp_frame)
        list_frame.pack()
        comp_listbox = tk.Listbox(list_frame, width=40)
        comp_listbox.pack(side='left')
        scrollbar = tk.Scrollbar(list_frame, orient='vertical', command=comp_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        comp_listbox.config(yscrollcommand=scrollbar.set)

        def refresh_list():
            comp_listbox.delete(0, tk.END)
            for comp in self.config['components'][cat_var.get()]:
                comp_listbox.insert(tk.END, f"{comp['name']} (${comp['price']})")
        def on_cat_change(event=None):
            refresh_list()
        cat_menu.bind('<<ComboboxSelected>>', on_cat_change)

        # Add/Edit/Delete
        entry_frame = tk.Frame(comp_frame)
        entry_frame.pack(pady=5)
        name_var = tk.StringVar()
        price_var = tk.StringVar()
        tk.Label(entry_frame, text='Name:').grid(row=0, column=0)
        tk.Entry(entry_frame, textvariable=name_var, width=15).grid(row=0, column=1)
        tk.Label(entry_frame, text='Price:').grid(row=0, column=2)
        tk.Entry(entry_frame, textvariable=price_var, width=8).grid(row=0, column=3)
        def add_component():
            name = name_var.get().strip()
            try:
                price = float(price_var.get())
            except ValueError:
                messagebox.showerror('Error', 'Invalid price!')
                return
            if not name:
                messagebox.showerror('Error', 'Name required!')
                return
            self.config['components'][cat_var.get()].append({'name': name, 'price': price})
            save_config(self.config)
            name_var.set('')
            price_var.set('')
            refresh_list()
        def edit_component():
            sel = comp_listbox.curselection()
            if not sel:
                messagebox.showerror('Error', 'Select a component to edit!')
                return
            idx = sel[0]
            name = name_var.get().strip()
            try:
                price = float(price_var.get())
            except ValueError:
                messagebox.showerror('Error', 'Invalid price!')
                return
            if not name:
                messagebox.showerror('Error', 'Name required!')
                return
            self.config['components'][cat_var.get()][idx] = {'name': name, 'price': price}
            save_config(self.config)
            refresh_list()
        def delete_component():
            sel = comp_listbox.curselection()
            if not sel:
                messagebox.showerror('Error', 'Select a component to delete!')
                return
            idx = sel[0]
            del self.config['components'][cat_var.get()][idx]
            save_config(self.config)
            refresh_list()
        tk.Button(entry_frame, text='Add', command=add_component).grid(row=0, column=4, padx=5)
        tk.Button(entry_frame, text='Edit', command=edit_component).grid(row=0, column=5, padx=5)
        tk.Button(entry_frame, text='Delete', command=delete_component).grid(row=0, column=6, padx=5)
        def on_list_select(event):
            sel = comp_listbox.curselection()
            if sel:
                comp = self.config['components'][cat_var.get()][sel[0]]
                name_var.set(comp['name'])
                price_var.set(str(comp['price']))
        comp_listbox.bind('<<ListboxSelect>>', on_list_select)
        refresh_list()

        tk.Button(frame, text='Logout', command=self.show_login).pack(pady=10)

    def show_user_panel(self):
        self.clear_window()
        frame = tk.Frame(self.root)
        frame.pack(padx=20, pady=20)
        tk.Label(frame, text='PC Builder - User', font=('Arial', 16)).pack(pady=10)
        # Component selection
        selections = {}
        option_vars = {}
        row = 1
        for cat, items in self.config['components'].items():
            tk.Label(frame, text=cat+':').grid(row=row, column=0, sticky='e')
            var = tk.StringVar()
            option_vars[cat] = var
            options = [f"{c['name']} (${c['price']})" for c in items]
            cb = ttk.Combobox(frame, textvariable=var, values=options, state='readonly', width=30)
            cb.grid(row=row, column=1, pady=2)
            row += 1
        total_var = tk.StringVar(value='Total: $0.00')
        tk.Label(frame, textvariable=total_var, font=('Arial', 12)).grid(row=row, column=0, columnspan=2, pady=10)
        def update_total(*args):
            total = 0
            for cat, var in option_vars.items():
                val = var.get()
                if val:
                    price = float(val.split('$')[-1].replace(')','').strip())
                    total += price
            total_var.set(f'Total: ${total:.2f}')
        for var in option_vars.values():
            var.trace_add('write', update_total)
        def check_compatibility():
            # Get all selected components
            cpu = option_vars['CPU'].get()
            mobo = option_vars['Motherboard'].get()
            ram = option_vars['RAM'].get()
            gpu = option_vars['GPU'].get()
            psu = option_vars['PSU'].get()
            case = option_vars['Case'].get()
            
            import re
            
            # 1. CPU and Motherboard socket compatibility
            cpu_socket = None
            mobo_socket = None
            cpu_match = re.search(r'\(([^)]+)\)', cpu)
            mobo_match = re.search(r'\(([^)]+)\)', mobo)
            if cpu_match:
                cpu_socket = cpu_match.group(1)
            if mobo_match:
                mobo_socket = mobo_match.group(1)
            if cpu_socket and mobo_socket and cpu_socket != mobo_socket:
                return False, f'CPU socket ({cpu_socket}) does not match Motherboard socket ({mobo_socket})!'
            
            # 2. Case and Motherboard form factor compatibility
            case_size = None
            mobo_form = None
            # Extract case size (ATX, mATX, ITX, etc.)
            case_match = re.search(r'(ATX|mATX|ITX|E-ATX|mini-ITX)', case, re.IGNORECASE)
            if case_match:
                case_size = case_match.group(1).upper()
            # Extract motherboard form factor
            mobo_match = re.search(r'(ATX|mATX|ITX|E-ATX|mini-ITX)', mobo, re.IGNORECASE)
            if mobo_match:
                mobo_form = mobo_match.group(1).upper()
            
            if case_size and mobo_form:
                # Compatibility matrix
                compatible_sizes = {
                    'ATX': ['ATX', 'mATX', 'ITX', 'mini-ITX'],
                    'mATX': ['mATX', 'ITX', 'mini-ITX'],
                    'ITX': ['ITX', 'mini-ITX'],
                    'mini-ITX': ['mini-ITX'],
                    'E-ATX': ['E-ATX', 'ATX', 'mATX', 'ITX', 'mini-ITX']
                }
                if case_size in compatible_sizes and mobo_form not in compatible_sizes[case_size]:
                    return False, f'Case ({case_size}) is too small for Motherboard ({mobo_form})!'
            
            # 3. RAM type and speed compatibility
            ram_type = None
            ram_speed = None
            mobo_ram_type = None
            mobo_ram_speed = None
            
            # Extract RAM type (DDR4, DDR5, etc.)
            ram_match = re.search(r'(DDR[45])', ram, re.IGNORECASE)
            if ram_match:
                ram_type = ram_match.group(1).upper()
            # Extract RAM speed
            ram_speed_match = re.search(r'(\d{3,4})\s*MHz', ram)
            if ram_speed_match:
                ram_speed = int(ram_speed_match.group(1))
            
            # Extract motherboard RAM support
            mobo_ram_match = re.search(r'(DDR[45])', mobo, re.IGNORECASE)
            if mobo_ram_match:
                mobo_ram_type = mobo_ram_match.group(1).upper()
            mobo_speed_match = re.search(r'(\d{3,4})\s*MHz', mobo)
            if mobo_speed_match:
                mobo_ram_speed = int(mobo_speed_match.group(1))
            
            if ram_type and mobo_ram_type and ram_type != mobo_ram_type:
                return False, f'RAM type ({ram_type}) is not compatible with Motherboard ({mobo_ram_type})!'
            
            if ram_speed and mobo_ram_speed and ram_speed > mobo_ram_speed:
                return False, f'RAM speed ({ram_speed}MHz) exceeds Motherboard maximum ({mobo_ram_speed}MHz)!'
            
            # 4. PSU wattage requirements
            psu_watt = None
            psu_match = re.search(r'(\d{3,4})\s*W', psu)
            if psu_match:
                psu_watt = int(psu_match.group(1))
            
            if psu_watt is not None:
                # Calculate estimated power requirements
                estimated_wattage = 0
                
                # Base system power (CPU, motherboard, RAM, storage)
                estimated_wattage += 150  # Base system
                
                # CPU power (estimate based on common ranges)
                if 'i9' in cpu or 'Ryzen 9' in cpu:
                    estimated_wattage += 125
                elif 'i7' in cpu or 'Ryzen 7' in cpu:
                    estimated_wattage += 95
                elif 'i5' in cpu or 'Ryzen 5' in cpu:
                    estimated_wattage += 65
                elif 'i3' in cpu or 'Ryzen 3' in cpu:
                    estimated_wattage += 50
                else:
                    estimated_wattage += 75  # Default estimate
                
                # GPU power (estimate based on common ranges)
                if gpu:
                    if 'RTX 4090' in gpu or 'RTX 4080' in gpu:
                        estimated_wattage += 320
                    elif 'RTX 4070' in gpu or 'RTX 3080' in gpu:
                        estimated_wattage += 220
                    elif 'RTX 3060' in gpu or 'RTX 4060' in gpu:
                        estimated_wattage += 170
                    elif 'GTX 1660' in gpu or 'RTX 3050' in gpu:
                        estimated_wattage += 120
                    else:
                        estimated_wattage += 150  # Default GPU estimate
                
                # Add 20% buffer for safety
                required_wattage = int(estimated_wattage * 1.2)
                
                if psu_watt < required_wattage:
                    return False, f'PSU ({psu_watt}W) may be insufficient. Estimated requirement: {required_wattage}W'
            
            # 5. Additional checks can be added here
            # - GPU length vs case clearance
            # - CPU cooler height vs case clearance
            # - Storage drive compatibility
            # - etc.
            
            return True, ''
        def submit_build():
            # Check all selections made
            for cat, var in option_vars.items():
                if not var.get():
                    messagebox.showerror('Error', f'Please select a {cat}.')
                    return
            compatible, msg = check_compatibility()
            if not compatible:
                messagebox.showerror('Compatibility Error', msg)
                return
            # Prepare build summary
            build = {cat: var.get() for cat, var in option_vars.items()}
            total = total_var.get()
            # Ask for user email
            user_email = simpledialog.askstring('Your Email', 'Enter your email address (for reply):')
            if not user_email:
                messagebox.showerror('Error', 'Email address required!')
                return
            # Send email
            try:
                msg = EmailMessage()
                msg['Subject'] = 'New PC Build Submission'
                msg['From'] = SMTP_USER
                msg['To'] = self.config.get('email', '')
                msg['Reply-To'] = user_email
                body = 'PC Build Submission:\n\n'
                for cat, val in build.items():
                    body += f'{cat}: {val}\n'
                body += f'\n{total}\nUser Email: {user_email}\n'
                msg.set_content(body)
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                    server.starttls()
                    server.login(SMTP_USER, SMTP_PASS)
                    server.send_message(msg)
                messagebox.showinfo('Submitted', 'Your build has been submitted!')
            except Exception as e:
                messagebox.showerror('Error', f'Failed to send email: {e}')
        tk.Button(frame, text='Submit Build', command=submit_build).grid(row=row+1, column=0, columnspan=2, pady=10)
        tk.Button(frame, text='Logout', command=self.show_login).grid(row=row+2, column=0, columnspan=2, pady=5)

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

def main():
    root = tk.Tk()
    app = PCBuilderApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()