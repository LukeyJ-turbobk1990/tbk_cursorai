#!/usr/bin/env python3
"""
PC Builder Application
----------------------
A simple desktop GUI application that lets customers assemble a custom PC build from a
pre-defined list of components. An admin panel (protected by hard-coded credentials)
allows maintaining the list of available components and their prices.

Core features
~~~~~~~~~~~~~
1. Admin login (username: ``admin``, password: ``pass1234!``) with a locked panel
   to manage components.
2. Customer panel with drop-downs for CPU, Motherboard, RAM, GPU, PSU, and Case.
3. Automatic compatibility checks (CPU ↔ Motherboard socket, RAM ↔ Motherboard RAM type).
4. Price calculation.
5. Order submission that stores a JSON file locally **and** sends an email (SMTP
   credentials configurable via *settings.json*).

Packaging
~~~~~~~~~
Run ``pip install pyinstaller`` and then:

    pyinstaller --onefile --noconsole pc_builder_app.py

A standalone executable will be created in the *dist/* directory.
"""
import json
import os
import sys
import smtplib
from email.message import EmailMessage
from pathlib import Path
from tkinter import (
    Tk,
    Toplevel,
    StringVar,
    IntVar,
    ttk,
    messagebox,
    simpledialog,
    END,
)

# ------------------------------------------------------------
#  Configuration helpers
# ------------------------------------------------------------

APP_NAME = "PC Builder"
COMPONENT_TYPES = [
    "CPU",
    "Motherboard",
    "RAM",
    "GPU",
    "PSU",
    "Case",
]
ADMIN_USER = "admin"
ADMIN_PASS = "pass1234!"

DEFAULT_COMPONENTS = {
    "CPU": [
        {
            "name": "Intel Core i5-12400F",
            "price": 180,
            "socket": "LGA1700",
        },
        {
            "name": "AMD Ryzen 5 5600X",
            "price": 200,
            "socket": "AM4",
        },
    ],
    "Motherboard": [
        {
            "name": "ASUS TUF Gaming B660M-PLUS",
            "price": 150,
            "socket": "LGA1700",
            "ram_type": "DDR4",
        },
        {
            "name": "MSI MAG B550M MORTAR",
            "price": 140,
            "socket": "AM4",
            "ram_type": "DDR4",
        },
    ],
    "RAM": [
        {"name": "Corsair Vengeance 16GB 3200 MHz", "price": 70, "ram_type": "DDR4"},
        {"name": "Kingston Fury Beast 16GB 3600 MHz", "price": 75, "ram_type": "DDR4"},
    ],
    "GPU": [
        {"name": "NVIDIA RTX 3060 12GB", "price": 340},
        {"name": "AMD Radeon RX 6700 XT 12GB", "price": 380},
    ],
    "PSU": [
        {"name": "Corsair CX650M 650 W", "price": 90, "wattage": 650},
        {"name": "Seasonic S12III 550 W", "price": 75, "wattage": 550},
    ],
    "Case": [
        {"name": "NZXT H510", "price": 75},
        {"name": "Fractal Design Pop Air", "price": 85},
    ],
}

DEFAULT_SETTINGS = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 465,
    "email_from": "your_company_email@example.com",
    "email_password": "APP_OR_EMAIL_PASSWORD",
    "email_to": "sales_inbox@example.com",
}


class _Paths:
    """Utility class that resolves user-writable paths whether we run frozen or not."""

    @staticmethod
    def base_dir() -> Path:
        if getattr(sys, "frozen", False):  # bundled by PyInstaller
            return Path(sys.executable).parent
        return Path(__file__).parent

    @staticmethod
    def components_file() -> Path:
        return _Paths.base_dir() / "components.json"

    @staticmethod
    def settings_file() -> Path:
        return _Paths.base_dir() / "settings.json"

    @staticmethod
    def orders_dir() -> Path:
        d = _Paths.base_dir() / "orders"
        d.mkdir(exist_ok=True)
        return d


# ------------------------------------------------------------
#  Persistence layer
# ------------------------------------------------------------


class DataManager:
    def __init__(self) -> None:
        self.data_path: Path = _Paths.components_file()
        self.components: dict[str, list[dict]] = {}
        self._ensure_file()
        self.load()

    # -------------------- Public API --------------------
    def load(self) -> None:
        with self.data_path.open("r", encoding="utf-8") as fp:
            self.components = json.load(fp)
            # ensure all expected keys exist
            for ctype in COMPONENT_TYPES:
                self.components.setdefault(ctype, [])

    def save(self) -> None:
        with self.data_path.open("w", encoding="utf-8") as fp:
            json.dump(self.components, fp, indent=2)

    def list_components(self, ctype: str) -> list[dict]:
        return self.components.get(ctype, [])

    def add_component(self, ctype: str, comp: dict) -> None:
        self.components.setdefault(ctype, []).append(comp)
        self.save()

    def delete_component(self, ctype: str, index: int) -> None:
        try:
            del self.components[ctype][index]
        except IndexError:
            pass
        self.save()

    # -------------------- Internals --------------------
    def _ensure_file(self):
        if not self.data_path.exists():
            with self.data_path.open("w", encoding="utf-8") as fp:
                json.dump(DEFAULT_COMPONENTS, fp, indent=2)


# ------------------------------------------------------------
#  Email helper
# ------------------------------------------------------------


def load_settings() -> dict:
    path = _Paths.settings_file()
    if not path.exists():
        with path.open("w", encoding="utf-8") as fp:
            json.dump(DEFAULT_SETTINGS, fp, indent=2)
        print(
            f"[INFO] Created default settings file at {path}.\n"
            "Please edit it with valid SMTP credentials to enable email sending."
        )
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def send_order_via_email(order_summary: str) -> None:
    settings = load_settings()
    try:
        msg = EmailMessage()
        msg["Subject"] = "New PC Build Order"
        msg["From"] = settings["email_from"]
        msg["To"] = settings["email_to"]
        msg.set_content(order_summary)

        with smtplib.SMTP_SSL(settings["smtp_server"], settings["smtp_port"]) as smtp:
            smtp.login(settings["email_from"], settings["email_password"])
            smtp.send_message(msg)
    except Exception as exc:
        # Log and alert user; do not crash the app
        print(f"[ERROR] Failed to send email: {exc}")
        messagebox.showwarning(
            "Email Failure",
            "Could not send email. Please verify your SMTP settings in settings.json.",
        )


# ------------------------------------------------------------
#  Compatibility checks
# ------------------------------------------------------------


def check_compatibility(selected: dict[str, dict]) -> tuple[bool, str]:
    """Return (is_compatible, message)."""
    cpu = selected.get("CPU")
    mobo = selected.get("Motherboard")
    ram = selected.get("RAM")

    if cpu and mobo:
        if cpu.get("socket") != mobo.get("socket"):
            return False, "CPU socket does not match motherboard socket."

    if ram and mobo:
        if ram.get("ram_type") != mobo.get("ram_type"):
            return False, "RAM type is not supported by the motherboard."

    return True, "All components are compatible."


# ------------------------------------------------------------
#  GUI components
# ------------------------------------------------------------


class AdminPanel(Toplevel):
    def __init__(self, master: Tk, data_manager: DataManager):
        super().__init__(master)
        self.title(f"{APP_NAME} — Admin Panel")
        self.geometry("600x400")
        self.data = data_manager

        # -- state
        self.ctype_var = StringVar(value=COMPONENT_TYPES[0])

        # -- widgets
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", pady=5)

        ttk.Label(top_frame, text="Component Type:").pack(side="left", padx=5)
        ctype_combo = ttk.Combobox(
            top_frame, textvariable=self.ctype_var, values=COMPONENT_TYPES, state="readonly"
        )
        ctype_combo.pack(side="left")
        ctype_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_list())

        self.listbox = ttk.Treeview(self, columns=("Price", "Attributes"), show="headings")
        self.listbox.heading("Price", text="Price ($)")
        self.listbox.heading("Attributes", text="Attributes")
        self.listbox.column("Price", width=80, anchor="center")
        self.listbox.pack(fill="both", expand=True, padx=10, pady=5)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="Add", command=self.add_component).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Delete", command=self.delete_selected).pack(side="left")

        self.refresh_list()

    # -------------------- Commands --------------------
    def refresh_list(self):
        self.listbox.delete(*self.listbox.get_children())
        comps = self.data.list_components(self.ctype_var.get())
        for idx, comp in enumerate(comps):
            attrs = {
                k: v for k, v in comp.items() if k not in {"name", "price"}
            }
            self.listbox.insert("", END, iid=str(idx), values=(comp["name"], comp["price"], json.dumps(attrs)))

    def add_component(self):
        ctype = self.ctype_var.get()
        name = simpledialog.askstring("Component Name", f"Enter {ctype} name:", parent=self)
        if not name:
            return
        try:
            price = float(
                simpledialog.askstring("Price", "Enter price ($):", parent=self)
            )
        except (TypeError, ValueError):
            messagebox.showerror("Invalid Input", "Price must be a number.")
            return
        # Ask for optional attributes JSON
        attr_str = simpledialog.askstring(
            "Attributes (optional)",
            "Enter extra attributes as JSON (e.g. {\"socket\": \"AM4\"}):",
            parent=self,
        )
        attrs = {}
        if attr_str:
            try:
                attrs = json.loads(attr_str)
            except json.JSONDecodeError as exc:
                messagebox.showerror(
                    "Invalid JSON", f"Could not parse attributes JSON: {exc.msg}"
                )
                return
        comp = {"name": name, "price": price, **attrs}
        self.data.add_component(ctype, comp)
        self.refresh_list()

    def delete_selected(self):
        sel = self.listbox.selection()
        if not sel:
            return
        idx = int(sel[0])
        ctype = self.ctype_var.get()
        self.data.delete_component(ctype, idx)
        self.refresh_list()


class CustomerPanel(Toplevel):
    def __init__(self, master: Tk, data_manager: DataManager):
        super().__init__(master)
        self.title(f"{APP_NAME} — Build Your PC")
        self.geometry("500x400")
        self.data = data_manager
        self.selected: dict[str, dict] = {}
        self.var_map: dict[str, StringVar] = {}

        # -- Widgets
        ttk.Label(self, text="Select your components", font=("TkDefaultFont", 13, "bold")).pack(pady=10)

        form = ttk.Frame(self)
        form.pack(pady=10, padx=20, fill="x")

        for ctype in COMPONENT_TYPES:
            row = ttk.Frame(form)
            row.pack(fill="x", pady=3)
            ttk.Label(row, text=f"{ctype}:", width=12).pack(side="left")
            var = StringVar()
            self.var_map[ctype] = var
            options = [c["name"] for c in self.data.list_components(ctype)]
            combo = ttk.Combobox(row, textvariable=var, values=options, state="readonly")
            combo.pack(side="left", fill="x", expand=True)

        # price + status
        self.status_var = StringVar(value="")
        status_lbl = ttk.Label(self, textvariable=self.status_var, foreground="blue")
        status_lbl.pack(pady=5)

        # buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Check & Price", command=self.check_and_price).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Submit Order", command=self.submit_order).pack(side="left", padx=5)

    # -------------------- Helpers --------------------
    def gather_selection(self):
        self.selected.clear()
        for ctype, var in self.var_map.items():
            name = var.get()
            if name:
                comp = next(
                    (c for c in self.data.list_components(ctype) if c["name"] == name), None
                )
                if comp:
                    self.selected[ctype] = comp

    def compute_price(self) -> float:
        return sum(comp["price"] for comp in self.selected.values())

    # -------------------- Commands --------------------
    def check_and_price(self):
        self.gather_selection()
        if len(self.selected) < len(COMPONENT_TYPES):
            self.status_var.set("Please select all components.")
            return
        ok, msg = check_compatibility(self.selected)
        price = self.compute_price()
        if ok:
            self.status_var.set(f"Total: ${price:.2f} — {msg}")
        else:
            self.status_var.set(f"Compatibility error: {msg}")

    def submit_order(self):
        self.check_and_price()
        if not self.status_var.get().startswith("Total"):
            messagebox.showwarning(
                "Cannot Submit", "Please resolve compatibility issues before submitting."
            )
            return
        # save order locally
        order = {
            "items": self.selected,
            "total_price": self.compute_price(),
        }
        order_file = _Paths.orders_dir() / f"order_{int(Path().stat().st_mtime_ns)}.json"
        with order_file.open("w", encoding="utf-8") as fp:
            json.dump(order, fp, indent=2)
        # send email
        summary_lines = ["New PC Build Order:\n"]
        for ctype, comp in self.selected.items():
            summary_lines.append(f"- {ctype}: {comp['name']} (${comp['price']})")
        summary_lines.append(f"\nTotal price: ${self.compute_price():.2f}\n")
        send_order_via_email("\n".join(summary_lines))
        messagebox.showinfo("Order Submitted", "Your order has been submitted. Thank you!")
        self.destroy()


# ------------------------------------------------------------
#  Main Application Shell
# ------------------------------------------------------------


def prompt_admin_login(root: Tk) -> bool:
    user = simpledialog.askstring("Admin Login", "Username:", parent=root)
    if user != ADMIN_USER:
        messagebox.showerror("Login Failed", "Incorrect username.")
        return False
    pwd = simpledialog.askstring(
        "Admin Login", "Password:", parent=root, show="*"
    )
    if pwd != ADMIN_PASS:
        messagebox.showerror("Login Failed", "Incorrect password.")
        return False
    return True


def main():
    root = Tk()
    root.title(APP_NAME)
    root.geometry("300x180")
    root.resizable(False, False)

    ttk.Label(root, text=APP_NAME, font=("TkDefaultFont", 16, "bold")).pack(pady=15)

    data_manager = DataManager()

    ttk.Button(
        root,
        text="Admin Login",
        command=lambda: AdminPanel(root, data_manager)
        if prompt_admin_login(root)
        else None,
    ).pack(pady=5, ipadx=10)

    ttk.Button(
        root,
        text="Build Your PC",
        command=lambda: CustomerPanel(root, data_manager),
    ).pack(pady=5, ipadx=10)

    ttk.Label(
        root,
        text="v1.0 — © 2025 Your Company",
        font=("TkDefaultFont", 8),
    ).pack(side="bottom", pady=5)

    root.mainloop()


if __name__ == "__main__":
    main()