#!/usr/bin/env python3
# PC Builder Application - Standalone Version
# This file contains the complete application

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import json
import os
import re
import smtplib
from email.message import EmailMessage
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# Constants
CONFIG_FILE = 'config.json'
ADMIN_USER = 'admin'
ADMIN_PASS = 'pass1234!'
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = 'your_gmail@gmail.com'  # Set your sending email here
SMTP_PASS = 'your_app_password'      # Set your app password here

# Component categories
COMPONENT_CATEGORIES = ['CPU', 'Motherboard', 'RAM', 'GPU', 'PSU', 'Case']

# Naming convention examples
NAMING_EXAMPLES = {
    'CPU': 'Examples:\n• Intel i5-12400 (LGA1700, 165mm cooler)\n• AMD Ryzen 5 5600X (AM4, 159mm cooler)\n• Intel i9-13900K (LGA1700, 170mm cooler)\n\nInclude: Socket type, cooler height if known',
    'Motherboard': 'Examples:\n• MSI B660M (LGA1700, DDR4, 3200MHz, mATX)\n• ASUS B550 (AM4, DDR4, 3600MHz, ATX)\n• Gigabyte Z690 (LGA1700, DDR5, 6000MHz, ATX)\n\nInclude: Socket, RAM type, max speed, form factor',
    'RAM': 'Examples:\n• Corsair Vengeance 16GB (DDR4, 3200MHz)\n• G.Skill Ripjaws 32GB (DDR5, 6000MHz)\n• Kingston Fury 8GB (DDR4, 2666MHz)\n\nInclude: Capacity, RAM type, speed',
    'GPU': 'Examples:\n• NVIDIA RTX 4070 (280mm, 1x8-pin)\n• AMD RX 6700 XT (267mm, 1x8-pin)\n• NVIDIA RTX 4090 (304mm, 1x16-pin)\n\nInclude: Length, power connector requirements',
    'PSU': 'Examples:\n• Corsair RM750x (750W, 2x8-pin PCIe, 1x6-pin PCIe)\n• EVGA 650W (650W, 1x8-pin PCIe)\n• Seasonic 850W (850W, 2x8-pin PCIe, 2x6-pin PCIe)\n\nInclude: Wattage, PCIe connectors',
    'Case': 'Examples:\n• NZXT H510 (ATX, 360mm GPU clearance, 165mm CPU cooler clearance)\n• Fractal Design Meshify C (ATX, 315mm GPU, 170mm cooler)\n• Cooler Master NR200 (mini-ITX, 330mm GPU, 155mm cooler)\n\nInclude: Form factor, GPU clearance, CPU cooler clearance'
}

# Compatibility matrices
CASE_COMPATIBILITY = {
    'ATX': ['ATX', 'mATX', 'ITX', 'mini-ITX'],
    'mATX': ['mATX', 'ITX', 'mini-ITX'],
    'ITX': ['ITX', 'mini-ITX'],
    'mini-ITX': ['mini-ITX'],
    'E-ATX': ['E-ATX', 'ATX', 'mATX', 'ITX', 'mini-ITX']
}

@dataclass
class Component:
    name: str
    price: float

@dataclass
class BuildSubmission:
    components: Dict[str, str]
    total_price: str
    user_email: str

class ConfigManager:
    """Handles configuration loading and saving"""
    
    @staticmethod
    def load_config() -> Dict:
        if not os.path.exists(CONFIG_FILE):
            return {
                "email": "your@email.com",
                "components": {cat: [] for cat in COMPONENT_CATEGORIES}
            }
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {
                "email": "your@email.com",
                "components": {cat: [] for cat in COMPONENT_CATEGORIES}
            }
    
    @staticmethod
    def save_config(config: Dict) -> None:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)

class ComponentValidator:
    """Handles component naming validation"""
    
    @staticmethod
    def validate_component_name(name: str, category: str) -> Optional[str]:
        """Validate component naming convention"""
        warnings = []
        
        validation_rules = {
            'CPU': [
                (r'\([^)]+\)', "CPU should include socket type in parentheses (e.g., LGA1700, AM4)"),
                (r'\d+mm', "Consider adding cooler height if known (e.g., 165mm)")
            ],
            'Motherboard': [
                (r'\([^)]+\)', "Motherboard should include socket, RAM type, and form factor"),
                (r'DDR[45]', "Include RAM type (DDR4, DDR5)"),
                (r'(ATX|mATX|ITX|mini-ITX)', "Include form factor (ATX, mATX, ITX, mini-ITX)")
            ],
            'RAM': [
                (r'DDR[45]', "Include RAM type (DDR4, DDR5)"),
                (r'\d{3,4}MHz', "Include RAM speed (e.g., 3200MHz)")
            ],
            'GPU': [
                (r'\(\d+mm', "Include GPU length in parentheses (e.g., 280mm)"),
                (r'\d+x\d+-pin', "Include power connector requirements (e.g., 1x8-pin)")
            ],
            'PSU': [
                (r'\(\d+W', "Include wattage in parentheses (e.g., 750W)"),
                (r'\d+x\d+-pin', "Include PCIe connectors if available (e.g., 2x8-pin)")
            ],
            'Case': [
                (r'(ATX|mATX|ITX|mini-ITX)', "Include form factor (ATX, mATX, ITX, mini-ITX)"),
                (r'\d+mm.*GPU', "Include GPU clearance (e.g., 360mm GPU clearance)"),
                (r'\d+mm.*CPU.*cooler', "Include CPU cooler clearance (e.g., 165mm CPU cooler clearance)")
            ]
        }
        
        for pattern, warning in validation_rules.get(category, []):
            if not re.search(pattern, name, re.IGNORECASE):
                warnings.append(warning)
        
        return '\n'.join(warnings) if warnings else None

class CompatibilityChecker:
    """Handles component compatibility validation"""
    
    @staticmethod
    def check_compatibility(selections: Dict[str, str]) -> Tuple[bool, str]:
        """Check compatibility between selected components"""
        
        # Extract component information
        cpu = selections.get('CPU', '')
        mobo = selections.get('Motherboard', '')
        ram = selections.get('RAM', '')
        gpu = selections.get('GPU', '')
        psu = selections.get('PSU', '')
        case = selections.get('Case', '')
        
        # 1. CPU and Motherboard socket compatibility
        cpu_socket = CompatibilityChecker._extract_socket(cpu)
        mobo_socket = CompatibilityChecker._extract_socket(mobo)
        if cpu_socket and mobo_socket and cpu_socket != mobo_socket:
            return False, f'CPU socket ({cpu_socket}) does not match Motherboard socket ({mobo_socket})!'
        
        # 2. Case and Motherboard form factor compatibility
        case_size = CompatibilityChecker._extract_form_factor(case)
        mobo_form = CompatibilityChecker._extract_form_factor(mobo)
        if case_size and mobo_form:
            # Check if the case can fit the motherboard
            # ATX case can fit ATX, mATX, ITX, mini-ITX
            # mATX case can fit mATX, ITX, mini-ITX
            # mini-ITX case can only fit mini-ITX
            if case_size in CASE_COMPATIBILITY:
                if mobo_form not in CASE_COMPATIBILITY[case_size]:
                    return False, f'Case ({case_size}) is too small for Motherboard ({mobo_form})!'
        
        # 3. RAM type and speed compatibility
        ram_type = CompatibilityChecker._extract_ram_type(ram)
        ram_speed = CompatibilityChecker._extract_ram_speed(ram)
        mobo_ram_type = CompatibilityChecker._extract_ram_type(mobo)
        mobo_ram_speed = CompatibilityChecker._extract_ram_speed(mobo)
        
        if ram_type and mobo_ram_type and ram_type != mobo_ram_type:
            return False, f'RAM type ({ram_type}) is not compatible with Motherboard ({mobo_ram_type})!'
        
        if ram_speed and mobo_ram_speed and ram_speed > mobo_ram_speed:
            return False, f'RAM speed ({ram_speed}MHz) exceeds Motherboard maximum ({mobo_ram_speed}MHz)!'
        
        # 4. PSU wattage requirements
        psu_watt = CompatibilityChecker._extract_psu_wattage(psu)
        if psu_watt is not None:
            required_wattage = CompatibilityChecker._calculate_required_wattage(cpu, gpu)
            if psu_watt < required_wattage:
                return False, f'PSU ({psu_watt}W) may be insufficient. Estimated requirement: {required_wattage}W'
        
        # 5. GPU length vs case clearance
        gpu_length = CompatibilityChecker._extract_gpu_length(gpu)
        case_gpu_clearance = CompatibilityChecker._extract_case_gpu_clearance(case)
        if gpu_length and case_gpu_clearance and gpu_length > case_gpu_clearance:
            return False, f'GPU length ({gpu_length}mm) exceeds case clearance ({case_gpu_clearance}mm)!'
        
        # 6. CPU cooler height vs case clearance
        cooler_height = CompatibilityChecker._extract_cooler_height(cpu)
        case_cooler_clearance = CompatibilityChecker._extract_case_cooler_clearance(case)
        if cooler_height and case_cooler_clearance and cooler_height > case_cooler_clearance:
            return False, f'CPU cooler height ({cooler_height}mm) exceeds case clearance ({case_cooler_clearance}mm)!'
        
        # 7. Storage drive compatibility
        # Check if case supports the storage drives (assuming common 2.5" and 3.5" drives)
        # This is more of a general check since most modern cases support both
        storage_support = True
        if 'mini-ITX' in case_size or 'ITX' in case_size:
            # Small cases might have limited storage options
            if '3.5"' in case and '2.5"' not in case:
                # Case only supports 3.5" drives
                pass  # Could add specific storage checks here
        
        # 8. Motherboard PCIe slot compatibility with GPU
        # Check if motherboard has enough PCIe slots for the GPU
        # Most modern motherboards have at least one PCIe x16 slot
        pcie_slots = 1  # Default assumption
        if 'ATX' in mobo_form:
            pcie_slots = 3  # ATX typically has 3+ PCIe slots
        elif 'mATX' in mobo_form:
            pcie_slots = 2  # mATX typically has 2 PCIe slots
        elif 'ITX' in mobo_form or 'mini-ITX' in mobo_form:
            pcie_slots = 1  # ITX typically has 1 PCIe slot
        
        # If user wants to add multiple GPUs, this would be relevant
        # For now, assume single GPU builds
        
        # 9. Memory channel compatibility
        # Check if RAM configuration matches motherboard memory channels
        ram_channels = 2  # Default dual-channel
        if 'ITX' in mobo_form or 'mini-ITX' in mobo_form:
            ram_channels = 2  # ITX boards are typically dual-channel
        elif 'ATX' in mobo_form or 'mATX' in mobo_form:
            ram_channels = 2  # Most modern boards are dual-channel (some are quad)
        
        # 10. Power connector compatibility
        # Check if PSU has required connectors for GPU
        psu_connectors = []
        gpu_connectors = []
        
        # Extract PSU connector info (assume format like "Corsair RM750x (750W, 2x8-pin PCIe)")
        psu_connector_match = re.search(r'(\d+)x(\d+)-pin', psu)
        if psu_connector_match:
            count = int(psu_connector_match.group(1))
            pins = int(psu_connector_match.group(2))
            psu_connectors.append(f"{count}x{pins}-pin")
        
        # Extract GPU connector requirements (assume format like "RTX 4070 (1x8-pin)" or "RTX 4090 (1x16-pin)")
        gpu_connector_match = re.search(r'(\d+)x(\d+)-pin', gpu)
        if gpu_connector_match:
            count = int(gpu_connector_match.group(1))
            pins = int(gpu_connector_match.group(2))
            gpu_connectors.append(f"{count}x{pins}-pin")
        
        # Basic connector check (simplified)
        if gpu_connectors and not psu_connectors:
            return False, 'PSU connector information not available for GPU requirements!'
        
        return True, ''
    
    @staticmethod
    def _extract_socket(component: str) -> Optional[str]:
        # Look for socket patterns like LGA1700, AM4, etc.
        socket_patterns = [
            r'LGA\d+',  # Intel sockets
            r'AM\d+',   # AMD sockets
            r'Socket\s+\d+',  # Generic socket
        ]
        for pattern in socket_patterns:
            match = re.search(pattern, component, re.IGNORECASE)
            if match:
                return match.group(0).upper()
        return None
    
    @staticmethod
    def _extract_form_factor(component: str) -> Optional[str]:
        match = re.search(r'(ATX|mATX|ITX|E-ATX|mini-ITX)', component, re.IGNORECASE)
        if match:
            form_factor = match.group(1)
            # Normalize to the format used in the compatibility matrix
            if form_factor.upper() == 'MATX':
                return 'mATX'
            elif form_factor.upper() == 'MINI-ITX':
                return 'mini-ITX'
            else:
                return form_factor.upper()
        return None
    
    @staticmethod
    def _extract_ram_type(component: str) -> Optional[str]:
        match = re.search(r'(DDR[45])', component, re.IGNORECASE)
        return match.group(1).upper() if match else None
    
    @staticmethod
    def _extract_ram_speed(component: str) -> Optional[int]:
        match = re.search(r'(\d{3,4})\s*MHz', component)
        return int(match.group(1)) if match else None
    
    @staticmethod
    def _extract_psu_wattage(component: str) -> Optional[int]:
        match = re.search(r'(\d{3,4})\s*W', component)
        return int(match.group(1)) if match else None
    
    @staticmethod
    def _extract_gpu_length(component: str) -> Optional[int]:
        # Look for patterns like (280mm) or 280mm
        match = re.search(r'\(?(\d{2,3})\s*mm\)?', component)
        return int(match.group(1)) if match else None
    
    @staticmethod
    def _extract_case_gpu_clearance(component: str) -> Optional[int]:
        # Look for patterns like "360mm GPU clearance" or "360mm GPU"
        match = re.search(r'(\d{2,3})\s*mm.*GPU', component, re.IGNORECASE)
        return int(match.group(1)) if match else None
    
    @staticmethod
    def _extract_cooler_height(component: str) -> Optional[int]:
        # Look for patterns like (165mm cooler) or 165mm cooler
        match = re.search(r'\(?(\d{2,3})\s*mm.*cooler\)?', component, re.IGNORECASE)
        return int(match.group(1)) if match else None
    
    @staticmethod
    def _extract_case_cooler_clearance(component: str) -> Optional[int]:
        # Look for patterns like "165mm CPU cooler clearance"
        match = re.search(r'(\d{2,3})\s*mm.*CPU.*cooler', component, re.IGNORECASE)
        return int(match.group(1)) if match else None
    
    @staticmethod
    def _calculate_required_wattage(cpu: str, gpu: str) -> int:
        estimated_wattage = 150  # Base system
        
        # CPU power estimation
        if 'i9' in cpu or 'Ryzen 9' in cpu:
            estimated_wattage += 125
        elif 'i7' in cpu or 'Ryzen 7' in cpu:
            estimated_wattage += 95
        elif 'i5' in cpu or 'Ryzen 5' in cpu:
            estimated_wattage += 65
        elif 'i3' in cpu or 'Ryzen 3' in cpu:
            estimated_wattage += 50
        else:
            estimated_wattage += 75
        
        # GPU power estimation
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
                estimated_wattage += 150
        
        return int(estimated_wattage * 1.2)  # 20% buffer

class EmailService:
    """Handles email sending functionality"""
    
    @staticmethod
    def send_build_submission(build: BuildSubmission, recipient_email: str) -> bool:
        """Send build submission via email"""
        try:
            msg = EmailMessage()
            msg['Subject'] = 'New PC Build Submission'
            msg['From'] = SMTP_USER
            msg['To'] = recipient_email
            msg['Reply-To'] = build.user_email
            
            body = 'PC Build Submission:\n\n'
            for category, component in build.components.items():
                body += f'{category}: {component}\n'
            body += f'\n{build.total_price}\nUser Email: {build.user_email}\n'
            msg.set_content(body)
            
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Email error: {e}")
            return False

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