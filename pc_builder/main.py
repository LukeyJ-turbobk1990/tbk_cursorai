import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

# Import core functionality
from core import (
    ConfigManager, ComponentValidator, CompatibilityChecker, 
    EmailService, BuildSubmission, Component, COMPONENT_CATEGORIES,
    NAMING_EXAMPLES, CASE_COMPATIBILITY
)

class LoginWindow:
    """Handles login interface"""
    
    def __init__(self, parent, on_admin_login, on_user_login):
        self.parent = parent
        self.on_admin_login = on_admin_login
        self.on_user_login = on_user_login
        self.create_widgets()
    
    def create_widgets(self):
        self.frame = tk.Frame(self.parent)
        self.frame.pack(padx=20, pady=20)
        
        tk.Label(self.frame, text='Login', font=('Arial', 16)).grid(row=0, column=0, columnspan=2, pady=10)
        tk.Label(self.frame, text='Username:').grid(row=1, column=0, sticky='e')
        tk.Label(self.frame, text='Password:').grid(row=2, column=0, sticky='e')
        
        self.username_entry = tk.Entry(self.frame)
        self.password_entry = tk.Entry(self.frame, show='*')
        self.username_entry.grid(row=1, column=1)
        self.password_entry.grid(row=2, column=1)
        
        tk.Button(self.frame, text='Login', command=self.login).grid(row=3, column=0, columnspan=2, pady=10)
    
    def login(self):
        user = self.username_entry.get()
        pw = self.password_entry.get()
        if user == 'admin' and pw == 'pass1234!':
            self.on_admin_login()
        else:
            self.on_user_login()
    
    def destroy(self):
        self.frame.destroy()

class AdminPanel:
    """Handles admin interface"""
    
    def __init__(self, parent, config, on_logout):
        self.parent = parent
        self.config = config
        self.on_logout = on_logout
        self.create_widgets()
    
    def create_widgets(self):
        self.frame = tk.Frame(self.parent)
        self.frame.pack(padx=20, pady=20)
        
        tk.Label(self.frame, text='Admin Panel', font=('Arial', 16)).pack(pady=10)
        
        # Email configuration
        self.create_email_section()
        
        # Component management
        self.create_component_section()
        
        tk.Button(self.frame, text='Logout', command=self.on_logout).pack(pady=10)
    
    def create_email_section(self):
        email_frame = tk.Frame(self.frame)
        email_frame.pack(pady=5)
        
        tk.Label(email_frame, text='Destination Email:').pack(side='left')
        self.email_var = tk.StringVar(value=self.config.get('email', ''))
        email_entry = tk.Entry(email_frame, textvariable=self.email_var, width=30)
        email_entry.pack(side='left')
        
        tk.Button(email_frame, text='Save', command=self.save_email).pack(side='left', padx=5)
    
    def create_component_section(self):
        comp_frame = tk.Frame(self.frame)
        comp_frame.pack(pady=10)
        
        tk.Label(comp_frame, text='Manage Components', font=('Arial', 12)).pack()
        
        # Category selection
        self.cat_var = tk.StringVar(value='CPU')
        cat_menu = ttk.Combobox(comp_frame, textvariable=self.cat_var, 
                               values=COMPONENT_CATEGORIES, state='readonly')
        cat_menu.pack(pady=5)
        
        # Component list
        list_frame = tk.Frame(comp_frame)
        list_frame.pack()
        
        self.comp_listbox = tk.Listbox(list_frame, width=40)
        self.comp_listbox.pack(side='left')
        
        scrollbar = tk.Scrollbar(list_frame, orient='vertical', command=self.comp_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.comp_listbox.config(yscrollcommand=scrollbar.set)
        
        # Input fields
        entry_frame = tk.Frame(comp_frame)
        entry_frame.pack(pady=5)
        
        tk.Label(entry_frame, text='Name:').grid(row=0, column=0)
        self.name_var = tk.StringVar()
        name_entry = tk.Entry(entry_frame, textvariable=self.name_var, width=30)
        name_entry.grid(row=0, column=1)
        
        tk.Label(entry_frame, text='Price:').grid(row=0, column=2)
        self.price_var = tk.StringVar()
        price_entry = tk.Entry(entry_frame, textvariable=self.price_var, width=8)
        price_entry.grid(row=0, column=3)
        
        # Helper text
        helper_frame = tk.Frame(comp_frame)
        helper_frame.pack(pady=5)
        self.helper_text = tk.Text(helper_frame, height=8, width=60, wrap=tk.WORD)
        self.helper_text.pack()
        
        # Buttons
        button_frame = tk.Frame(entry_frame)
        button_frame.grid(row=0, column=4, padx=5)
        
        tk.Button(button_frame, text='Add', command=self.add_component).pack(side='left', padx=2)
        tk.Button(button_frame, text='Edit', command=self.edit_component).pack(side='left', padx=2)
        tk.Button(button_frame, text='Delete', command=self.delete_component).pack(side='left', padx=2)
        
        # Bind events
        cat_menu.bind('<<ComboboxSelected>>', lambda e: self.update_helper_text())
        self.comp_listbox.bind('<<ListboxSelect>>', self.on_list_select)
        
        self.update_helper_text()
        self.refresh_list()
    
    def update_helper_text(self):
        category = self.cat_var.get()
        self.helper_text.delete(1.0, tk.END)
        self.helper_text.insert(1.0, NAMING_EXAMPLES.get(category, 'Select a category for naming examples'))
    
    def refresh_list(self):
        self.comp_listbox.delete(0, tk.END)
        for comp in self.config['components'][self.cat_var.get()]:
            self.comp_listbox.insert(tk.END, f"{comp['name']} (${comp['price']})")
    
    def on_list_select(self, event):
        sel = self.comp_listbox.curselection()
        if sel:
            comp = self.config['components'][self.cat_var.get()][sel[0]]
            self.name_var.set(comp['name'])
            self.price_var.set(str(comp['price']))
    
    def save_email(self):
        self.config['email'] = self.email_var.get()
        ConfigManager.save_config(self.config)
        messagebox.showinfo('Saved', 'Email address updated!')
    
    def add_component(self):
        name = self.name_var.get().strip()
        try:
            price = float(self.price_var.get())
        except ValueError:
            messagebox.showerror('Error', 'Invalid price!')
            return
        
        if not name:
            messagebox.showerror('Error', 'Name required!')
            return
        
        # Validate naming convention
        category = self.cat_var.get()
        validation_msg = ComponentValidator.validate_component_name(name, category)
        if validation_msg:
            result = messagebox.askyesno('Naming Convention Warning', 
                f'{validation_msg}\n\nDo you want to continue anyway?')
            if not result:
                return
        
        self.config['components'][category].append({'name': name, 'price': price})
        ConfigManager.save_config(self.config)
        self.name_var.set('')
        self.price_var.set('')
        self.refresh_list()
    
    def edit_component(self):
        sel = self.comp_listbox.curselection()
        if not sel:
            messagebox.showerror('Error', 'Select a component to edit!')
            return
        
        idx = sel[0]
        name = self.name_var.get().strip()
        try:
            price = float(self.price_var.get())
        except ValueError:
            messagebox.showerror('Error', 'Invalid price!')
            return
        
        if not name:
            messagebox.showerror('Error', 'Name required!')
            return
        
        self.config['components'][self.cat_var.get()][idx] = {'name': name, 'price': price}
        ConfigManager.save_config(self.config)
        self.refresh_list()
    
    def delete_component(self):
        sel = self.comp_listbox.curselection()
        if not sel:
            messagebox.showerror('Error', 'Select a component to delete!')
            return
        
        idx = sel[0]
        del self.config['components'][self.cat_var.get()][idx]
        ConfigManager.save_config(self.config)
        self.refresh_list()
    
    def destroy(self):
        self.frame.destroy()

class UserPanel:
    """Handles user interface"""
    
    def __init__(self, parent, config, on_logout):
        self.parent = parent
        self.config = config
        self.on_logout = on_logout
        self.create_widgets()
    
    def create_widgets(self):
        self.frame = tk.Frame(self.parent)
        self.frame.pack(padx=20, pady=20)
        
        tk.Label(self.frame, text='PC Builder - User', font=('Arial', 16)).pack(pady=10)
        
        # Component selection
        self.option_vars = {}
        row = 1
        
        for cat in COMPONENT_CATEGORIES:
            tk.Label(self.frame, text=f'{cat}:').grid(row=row, column=0, sticky='e')
            var = tk.StringVar()
            self.option_vars[cat] = var
            
            items = self.config['components'].get(cat, [])
            options = [f"{c['name']} (${c['price']})" for c in items]
            
            cb = ttk.Combobox(self.frame, textvariable=var, values=options, state='readonly', width=30)
            cb.grid(row=row, column=1, pady=2)
            row += 1
        
        # Total price
        self.total_var = tk.StringVar(value='Total: $0.00')
        tk.Label(self.frame, textvariable=self.total_var, font=('Arial', 12)).grid(row=row, column=0, columnspan=2, pady=10)
        
        # Buttons
        tk.Button(self.frame, text='Submit Build', command=self.submit_build).grid(row=row+1, column=0, columnspan=2, pady=10)
        tk.Button(self.frame, text='Logout', command=self.on_logout).grid(row=row+2, column=0, columnspan=2, pady=5)
        
        # Bind total update
        for var in self.option_vars.values():
            var.trace_add('write', self.update_total)
    
    def update_total(self, *args):
        total = 0
        for var in self.option_vars.values():
            val = var.get()
            if val:
                try:
                    price = float(val.split('$')[-1].replace(')', '').strip())
                    total += price
                except (ValueError, IndexError):
                    continue
        self.total_var.set(f'Total: ${total:.2f}')
    
    def submit_build(self):
        # Check all selections made
        for cat, var in self.option_vars.items():
            if not var.get():
                messagebox.showerror('Error', f'Please select a {cat}.')
                return
        
        # Check compatibility
        selections = {cat: var.get() for cat, var in self.option_vars.items()}
        compatible, msg = CompatibilityChecker.check_compatibility(selections)
        if not compatible:
            messagebox.showerror('Compatibility Error', msg)
            return
        
        # Ask for user email
        user_email = simpledialog.askstring('Your Email', 'Enter your email address (for reply):')
        if not user_email:
            messagebox.showerror('Error', 'Email address required!')
            return
        
        # Prepare build submission
        build = BuildSubmission(
            components=selections,
            total_price=self.total_var.get(),
            user_email=user_email
        )
        
        # Send email
        if EmailService.send_build_submission(build, self.config.get('email', '')):
            messagebox.showinfo('Submitted', 'Your build has been submitted!')
        else:
            messagebox.showerror('Error', 'Failed to send email. Please check your email configuration.')
    
    def destroy(self):
        self.frame.destroy()

class PCBuilderApp:
    """Main application class"""
    
    def __init__(self, root):
        self.root = root
        self.root.title('PC Builder')
        self.config = ConfigManager.load_config()
        self.current_panel = None
        self.show_login()
    
    def show_login(self):
        self.clear_window()
        self.current_panel = LoginWindow(
            self.root,
            on_admin_login=self.show_admin_panel,
            on_user_login=self.show_user_panel
        )
    
    def show_admin_panel(self):
        self.clear_window()
        self.current_panel = AdminPanel(
            self.root,
            self.config,
            on_logout=self.show_login
        )
    
    def show_user_panel(self):
        self.clear_window()
        self.current_panel = UserPanel(
            self.root,
            self.config,
            on_logout=self.show_login
        )
    
    def clear_window(self):
        if self.current_panel:
            self.current_panel.destroy()
        for widget in self.root.winfo_children():
            widget.destroy()

def main():
    root = tk.Tk()
    app = PCBuilderApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()