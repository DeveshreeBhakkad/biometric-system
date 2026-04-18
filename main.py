"""
main.py
Biometric KYC System — Main Application
Jalgaon People's Co-operative Bank Ltd.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import platform
import subprocess
import io
from PIL import Image, ImageTk
import datetime

from database import create_tables, save_customer, save_loan, \
    get_customer_by_id, get_all_fingerprints, save_payment, \
    get_payment_history, get_total_paid, search_customers
from fingerprint_handler import FingerprintHandler
from camera_handler import CameraHandler
from receipt_generator import generate_kyc_card

# ─────────────────────────────────────────
#  COLORS & FONTS
# ─────────────────────────────────────────
BG_DARK    = "#1a1a2e"
BG_PANEL   = "#16213e"
BG_INPUT   = "#0f3460"
ACCENT     = "#00d4ff"
ACCENT2    = "#7209b7"
SUCCESS    = "#00ff88"
WARNING    = "#ffd700"
DANGER     = "#ff6b6b"
TEXT_MAIN  = "#ffffff"
TEXT_MUTED = "#a0a0c0"
FONT_MAIN  = ("Segoe UI", 10)
FONT_BOLD  = ("Segoe UI", 10, "bold")
FONT_HEAD  = ("Segoe UI", 13, "bold")
FONT_TITLE = ("Segoe UI", 18, "bold")


# ─────────────────────────────────────────
#  HELPER — make consistent button
# ─────────────────────────────────────────
def make_btn(parent, text, color, command, width=16):
    return tk.Button(
        parent, text=text, command=command,
        bg=color, fg=TEXT_MAIN, font=FONT_BOLD,
        relief=tk.FLAT, cursor="hand2",
        width=width, padx=6, pady=5,
        activebackground=color, activeforeground=TEXT_MAIN
    )


# ─────────────────────────────────────────
#  ENROLLMENT WINDOW
# ─────────────────────────────────────────
class EnrollmentWindow:
    def __init__(self, parent, fp_handler, cam_handler, on_done=None):
        self.parent     = parent
        self.fp_handler = fp_handler
        self.cam_handler= cam_handler
        self.on_done    = on_done

        self.photo_bytes       = None
        self.fingerprint_bytes = None
        self.camera_pil        = None
        self.camera_running    = False
        self.cap               = None
        self._live_frame       = None

        self.win = tk.Toplevel(parent)
        self.win.title("New Customer Enrollment")
        self.win.geometry("1100x700")
        self.win.configure(bg=BG_DARK)
        self.win.grab_set()
        self._build_ui()

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.win, bg=BG_PANEL, pady=8)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="NEW CUSTOMER KYC ENROLLMENT",
                 font=FONT_TITLE, fg=ACCENT, bg=BG_PANEL).pack()
        tk.Label(hdr, text="Jalgaon People's Co-operative Bank Ltd.",
                 font=FONT_MAIN, fg=TEXT_MUTED, bg=BG_PANEL).pack()

        body = tk.Frame(self.win, bg=BG_DARK)
        body.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        self._build_form(body)
        self._build_capture(body)
        self._build_bottom()

    def _build_form(self, parent):
        frame = tk.LabelFrame(parent, text="  Customer & Loan Details  ",
                              font=FONT_BOLD, fg=ACCENT, bg=BG_PANEL,
                              relief=tk.GROOVE, bd=2)
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        fields = [
            ("Full Name *",      "name"),
            ("Mobile Number *",  "mobile"),
            ("Account Number *", "account_no"),
            ("Loan Amount (Rs.)*","loan_amount"),
        ]
        self.entries = {}
        for i, (label, key) in enumerate(fields):
            tk.Label(frame, text=label, font=FONT_BOLD,
                     fg=TEXT_MUTED, bg=BG_PANEL).grid(
                row=i, column=0, sticky="w", padx=12, pady=8)
            e = tk.Entry(frame, font=FONT_MAIN, width=28,
                         bg=BG_INPUT, fg=TEXT_MAIN,
                         insertbackground=TEXT_MAIN,
                         relief=tk.FLAT, bd=4)
            e.grid(row=i, column=1, padx=12, pady=8, sticky="ew")
            self.entries[key] = e

        # Loan type dropdown
        tk.Label(frame, text="Loan Type *", font=FONT_BOLD,
                 fg=TEXT_MUTED, bg=BG_PANEL).grid(
            row=len(fields), column=0, sticky="w", padx=12, pady=8)
        self.loan_type_var = tk.StringVar(value="Gold Loan")
        ttk.Combobox(frame, textvariable=self.loan_type_var,
                     width=26, font=FONT_MAIN,
                     values=["Gold Loan", "Housing Loan", "Personal Loan",
                             "Vehicle Loan", "Education Loan",
                             "Business Loan", "Other"]).grid(
            row=len(fields), column=1, padx=12, pady=8, sticky="ew")

    def _build_capture(self, parent):
        frame = tk.Frame(parent, bg=BG_DARK)
        frame.pack(side=tk.RIGHT, fill=tk.BOTH)

        # Photo
        cam_f = tk.LabelFrame(frame, text="  Customer Photo  ",
                              font=FONT_BOLD, fg=ACCENT,
                              bg=BG_PANEL, relief=tk.GROOVE)
        cam_f.pack(fill=tk.X, pady=(0, 8))

        self.cam_label = tk.Label(cam_f, text="[ Camera Preview ]",
                                  bg="#0a0a1a", fg="#555577",
                                  width=36, height=9)
        self.cam_label.pack(padx=8, pady=8)

        btn_row = tk.Frame(cam_f, bg=BG_PANEL)
        btn_row.pack(pady=4)
        self.btn_cam = make_btn(btn_row, "▶ Start Camera",
                                "#0077b6", self.start_camera, 14)
        self.btn_cam.pack(side=tk.LEFT, padx=3)
        self.btn_capture = make_btn(btn_row, "📸 Capture",
                                    "#00b4d8", self.capture_photo, 10)
        self.btn_capture.pack(side=tk.LEFT, padx=3)
        self.btn_capture.config(state=tk.DISABLED)
        make_btn(btn_row, " Upload", "#023e8a",
                 self.upload_photo, 8).pack(side=tk.LEFT, padx=3)

        self.cam_status = tk.Label(cam_f, text="❌ No photo",
                                   fg=DANGER, bg=BG_PANEL, font=("Segoe UI", 8))
        self.cam_status.pack(pady=2)

        # Fingerprint
        fp_f = tk.LabelFrame(frame, text="  Fingerprint  ",
                              font=FONT_BOLD, fg=ACCENT,
                              bg=BG_PANEL, relief=tk.GROOVE)
        fp_f.pack(fill=tk.X)

        self.fp_label = tk.Label(fp_f, text="[ Fingerprint Preview ]",
                                 bg="#0a0a1a", fg="#555577",
                                 width=36, height=9)
        self.fp_label.pack(padx=8, pady=8)

        fp_btn = tk.Frame(fp_f, bg=BG_PANEL)
        fp_btn.pack(pady=4)
        make_btn(fp_btn, " Scan Fingerprint",
                 ACCENT2, self.scan_fingerprint, 18).pack(side=tk.LEFT, padx=3)
        make_btn(fp_btn, "🗑 Clear", "#560bad",
                 self.clear_fp, 7).pack(side=tk.LEFT, padx=3)

        self.fp_status = tk.Label(fp_f, text="❌ No fingerprint",
                                  fg=DANGER, bg=BG_PANEL,
                                  font=("Segoe UI", 8))
        self.fp_status.pack(pady=2)

    def _build_bottom(self):
        btn_frame = tk.Frame(self.win, bg=BG_PANEL, pady=8)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        make_btn(btn_frame, "✅  Save & Enroll Customer",
                 "#006400", self.save_enroll, 26).pack(side=tk.LEFT, padx=15)
        make_btn(btn_frame, "✖ Cancel",
                 "#8b0000", self.win.destroy, 12).pack(side=tk.LEFT, padx=5)

    # ── Camera ──
    def start_camera(self):
        if self.camera_running:
            self._stop_camera()
            return
        self.cap = self.cam_handler.open_camera()
        if self.cap is None:
            messagebox.showerror("Camera Error",
                                 "No camera detected. Connect a webcam.")
            return
        self.camera_running = True
        self.btn_cam.config(text="⏹ Stop Camera")
        self.btn_capture.config(state=tk.NORMAL)
        self._update_feed()

    def _update_feed(self):
        if not self.camera_running:
            return
        pil = self.cam_handler.read_frame()
        if pil:
            self._live_frame = pil
            preview = pil.resize((280, 180))
            imgtk = ImageTk.PhotoImage(preview)
            self.cam_label.config(image=imgtk, text="")
            self.cam_label.image = imgtk
        self.win.after(30, self._update_feed)

    def _stop_camera(self):
        self.camera_running = False
        self.cam_handler.release()
        self.btn_cam.config(text="▶ Start Camera")
        self.btn_capture.config(state=tk.DISABLED)

    def capture_photo(self):
        if self._live_frame:
            self.camera_pil = self._live_frame
            self.photo_bytes = self.cam_handler.pil_to_bytes(self.camera_pil)
            preview = self.camera_pil.resize((280, 180))
            imgtk = ImageTk.PhotoImage(preview)
            self.cam_label.config(image=imgtk, text="")
            self.cam_label.image = imgtk
            self.cam_status.config(text="✅ Photo captured!", fg=SUCCESS)
            self._stop_camera()
        else:
            messagebox.showwarning("No Frame", "Start camera first.")

    def upload_photo(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp")])
        if path:
            pil = Image.open(path).convert("RGB")
            self.camera_pil = pil
            self.photo_bytes = self.cam_handler.pil_to_bytes(pil)
            preview = pil.resize((280, 180))
            imgtk = ImageTk.PhotoImage(preview)
            self.cam_label.config(image=imgtk, text="")
            self.cam_label.image = imgtk
            self.cam_status.config(text="✅ Photo uploaded!", fg=SUCCESS)

    # ── Fingerprint ──
    def scan_fingerprint(self):
        def do_scan():
            pil, fp_bytes = self.fp_handler.capture_fingerprint()
            self.win.after(0, lambda: self._on_fp_done(pil, fp_bytes))

        threading.Thread(target=do_scan, daemon=True).start()

    def _on_fp_done(self, pil, fp_bytes):
        if pil and fp_bytes:
            self.fingerprint_bytes = fp_bytes
            preview = pil.resize((280, 180))
            imgtk = ImageTk.PhotoImage(preview)
            self.fp_label.config(image=imgtk, text="")
            self.fp_label.image = imgtk
            self.fp_status.config(text="✅ Fingerprint scanned!", fg=SUCCESS)
        else:
            messagebox.showerror("Scan Failed",
                                 "Fingerprint scan failed. Try again.")

    def clear_fp(self):
        self.fingerprint_bytes = None
        self.fp_label.config(image="", text="[ Fingerprint Preview ]",
                             fg="#555577")
        self.fp_label.image = None
        self.fp_status.config(text="❌ No fingerprint", fg=DANGER)

    # ── Save ──
    def save_enroll(self):
        name       = self.entries["name"].get().strip()
        mobile     = self.entries["mobile"].get().strip()
        account_no = self.entries["account_no"].get().strip()
        loan_amt   = self.entries["loan_amount"].get().strip()
        loan_type  = self.loan_type_var.get()

        # Validation
        errors = []
        if not name:         errors.append("Full Name is required.")
        if not mobile:       errors.append("Mobile Number is required.")
        if not account_no:   errors.append("Account Number is required.")
        if not loan_amt:     errors.append("Loan Amount is required.")
        else:
            try:
                float(loan_amt)
            except ValueError:
                errors.append("Loan Amount must be a number.")
        if not self.photo_bytes:
            errors.append("Customer photo is required.")
        if not self.fingerprint_bytes:
            errors.append("Fingerprint scan is required.")

        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return

        try:
            customer_id = save_customer(
                name, mobile, self.photo_bytes, self.fingerprint_bytes)
            save_loan(customer_id, loan_type,
                      float(loan_amt), account_no)

            # Generate KYC card
            card_data = {
                "customer_id"   : customer_id,
                "full_name"     : name,
                "mobile"        : mobile,
                "loan_type"     : loan_type,
                "loan_amount"   : loan_amt,
                "account_number": account_no,
                "enrolled_date" : datetime.date.today().strftime("%d %b %Y"),
            }
            card_path = generate_kyc_card(
                card_data, self.photo_bytes, self.fingerprint_bytes)

            result = messagebox.askyesno(
                "Enrollment Successful",
                f"✅ Customer enrolled!\n\n"
                f"Customer ID: JPCB-{str(customer_id).zfill(5)}\n"
                f"Name: {name}\n\n"
                f"KYC Card generated. Open it now?"
            )
            if result:
                _open_file(card_path)

            if self.on_done:
                self.on_done()
            self.win.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Enrollment failed:\n{e}")


# ─────────────────────────────────────────
#  PAYMENT WINDOW
# ─────────────────────────────────────────
class PaymentWindow:
    def __init__(self, parent, fp_handler):
        self.parent     = parent
        self.fp_handler = fp_handler
        self.matched_customer = None
        self.fingerprint_bytes = None

        self.win = tk.Toplevel(parent)
        self.win.title("Record Payment")
        self.win.geometry("900x650")
        self.win.configure(bg=BG_DARK)
        self.win.grab_set()
        self._build_ui()

    def _build_ui(self):
        hdr = tk.Frame(self.win, bg=BG_PANEL, pady=8)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="RECORD LOAN PAYMENT",
                 font=FONT_TITLE, fg=ACCENT, bg=BG_PANEL).pack()

        body = tk.Frame(self.win, bg=BG_DARK)
        body.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # Left — scan
        left = tk.LabelFrame(body, text="  Step 1 — Scan Fingerprint  ",
                             font=FONT_BOLD, fg=ACCENT,
                             bg=BG_PANEL, relief=tk.GROOVE)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.fp_label = tk.Label(left, text="[ Fingerprint Preview ]",
                                 bg="#0a0a1a", fg="#555577",
                                 width=32, height=10)
        self.fp_label.pack(padx=8, pady=8)

        make_btn(left, "👆 Scan Fingerprint",
                 ACCENT2, self.scan_fingerprint, 20).pack(pady=6)

        self.scan_status = tk.Label(left, text="Place finger on scanner",
                                    fg=WARNING, bg=BG_PANEL,
                                    font=FONT_BOLD, wraplength=260)
        self.scan_status.pack(pady=4)

        # Right — customer info + payment
        right = tk.Frame(body, bg=BG_DARK)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Customer card
        self.info_frame = tk.LabelFrame(
            right, text="  Step 2 — Customer Details  ",
            font=FONT_BOLD, fg=ACCENT, bg=BG_PANEL, relief=tk.GROOVE)
        self.info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self.photo_label = tk.Label(self.info_frame, text="",
                                    bg=BG_PANEL)
        self.photo_label.pack(pady=8)

        self.info_text = tk.Label(
            self.info_frame,
            text="Scan fingerprint to identify customer",
            fg=TEXT_MUTED, bg=BG_PANEL, font=FONT_MAIN,
            justify=tk.CENTER, wraplength=300)
        self.info_text.pack(pady=4)

        # Payment entry
        pay_frame = tk.LabelFrame(
            right, text="  Step 3 — Enter Payment  ",
            font=FONT_BOLD, fg=ACCENT, bg=BG_PANEL, relief=tk.GROOVE)
        pay_frame.pack(fill=tk.X)

        tk.Label(pay_frame, text="Amount Paid (Rs.):",
                 font=FONT_BOLD, fg=TEXT_MUTED, bg=BG_PANEL).pack(
            side=tk.LEFT, padx=12, pady=10)
        self.amount_entry = tk.Entry(
            pay_frame, font=("Segoe UI", 14), width=14,
            bg=BG_INPUT, fg=TEXT_MAIN,
            insertbackground=TEXT_MAIN, relief=tk.FLAT, bd=4)
        self.amount_entry.pack(side=tk.LEFT, padx=8, pady=10)
        make_btn(pay_frame, "✅ Record",
                 "#006400", self.record_payment, 10).pack(
            side=tk.LEFT, padx=8)

    def scan_fingerprint(self):
        self.scan_status.config(text="⏳ Scanning...", fg=WARNING)

        def do_scan():
            pil, fp_bytes = self.fp_handler.capture_fingerprint()
            self.win.after(0, lambda: self._on_fp_done(pil, fp_bytes))

        threading.Thread(target=do_scan, daemon=True).start()

    def _on_fp_done(self, pil, fp_bytes):
        if not pil or not fp_bytes:
            self.scan_status.config(
                text="❌ Scan failed. Try again.", fg=DANGER)
            return

        self.fingerprint_bytes = fp_bytes

        # Show fingerprint preview
        preview = pil.resize((230, 160))
        imgtk = ImageTk.PhotoImage(preview)
        self.fp_label.config(image=imgtk, text="")
        self.fp_label.image = imgtk

        self.scan_status.config(text="✅ Fingerprint captured!", fg=SUCCESS)

        # For now — manual customer search since we're not doing auto-match yet
        # Show a dialog to select customer
        self._open_customer_search()

    def _open_customer_search(self):
        """Let staff search and select customer manually."""
        search_win = tk.Toplevel(self.win)
        search_win.title("Find Customer")
        search_win.geometry("500x400")
        search_win.configure(bg=BG_DARK)
        search_win.grab_set()

        tk.Label(search_win, text="Search Customer by Name:",
                 font=FONT_BOLD, fg=TEXT_MUTED, bg=BG_DARK).pack(
            padx=15, pady=(15, 5), anchor="w")

        search_var = tk.StringVar()
        search_entry = tk.Entry(search_win, textvariable=search_var,
                                font=FONT_MAIN, bg=BG_INPUT, fg=TEXT_MAIN,
                                insertbackground=TEXT_MAIN,
                                relief=tk.FLAT, bd=4, width=35)
        search_entry.pack(padx=15, pady=5)
        search_entry.focus()

        cols = ("ID", "Name", "Mobile", "Loan Type")
        tree = ttk.Treeview(search_win, columns=cols,
                            show="headings", height=8)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=110)
        tree.pack(padx=15, pady=8, fill=tk.BOTH, expand=True)

        def do_search(*_):
            for row in tree.get_children():
                tree.delete(row)
            results = search_customers(search_var.get())
            for r in results:
                tree.insert("", tk.END, values=(
                    f"JPCB-{str(r['customer_id']).zfill(5)}",
                    r["full_name"], r["mobile"],
                    r.get("loan_type", "")
                ), tags=(r["customer_id"],))

        search_var.trace("w", do_search)
        do_search()

        def select_customer():
            selected = tree.focus()
            if not selected:
                messagebox.showwarning("Select", "Please select a customer.")
                return
            tags = tree.item(selected, "tags")
            if tags:
                customer_id = int(tags[0])
                customer = get_customer_by_id(customer_id)
                if customer:
                    self.matched_customer = customer
                    self._show_customer_info(customer)
                    search_win.destroy()

        make_btn(search_win, "✅ Select Customer",
                 "#006400", select_customer, 20).pack(pady=8)

    def _show_customer_info(self, customer):
        """Display matched customer's details."""
        # Show photo if available
        if customer.get("photo"):
            try:
                pil = Image.open(
                    io.BytesIO(customer["photo"])).convert("RGB")
                pil = pil.resize((100, 120))
                imgtk = ImageTk.PhotoImage(pil)
                self.photo_label.config(image=imgtk)
                self.photo_label.image = imgtk
            except Exception:
                pass

        total = get_total_paid(customer["customer_id"])
        info = (
            f"Name:    {customer['full_name']}\n"
            f"Mobile:  {customer['mobile']}\n"
            f"Loan:    {customer.get('loan_type', '')} — "
            f"Rs. {customer.get('loan_amount', '')}\n"
            f"A/C No:  {customer.get('account_number', '')}\n"
            f"Total Paid So Far:  Rs. {total}"
        )
        self.info_text.config(text=info, fg=SUCCESS,
                              font=FONT_MAIN, justify=tk.LEFT)

    def record_payment(self):
        if not self.matched_customer:
            messagebox.showwarning(
                "No Customer", "Please scan fingerprint and select customer first.")
            return

        amount_str = self.amount_entry.get().strip()
        if not amount_str:
            messagebox.showwarning("Amount", "Please enter amount paid.")
            return
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Amount",
                                 "Please enter a valid positive amount.")
            return

        try:
            save_payment(
                self.matched_customer["customer_id"],
                amount,
                self.fingerprint_bytes
            )
            now = datetime.datetime.now()
            messagebox.showinfo(
                "Payment Recorded",
                f"✅ Payment recorded successfully!\n\n"
                f"Customer: {self.matched_customer['full_name']}\n"
                f"Amount:   Rs. {amount:,.0f}\n"
                f"Date:     {now.strftime('%d %b %Y')}\n"
                f"Time:     {now.strftime('%I:%M %p')}"
            )
            self.win.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to record payment:\n{e}")


# ─────────────────────────────────────────
#  HISTORY WINDOW
# ─────────────────────────────────────────
class HistoryWindow:
    def __init__(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title("Payment History")
        self.win.geometry("900x600")
        self.win.configure(bg=BG_DARK)
        self.win.grab_set()
        self._build_ui()

    def _build_ui(self):
        hdr = tk.Frame(self.win, bg=BG_PANEL, pady=8)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="PAYMENT HISTORY",
                 font=FONT_TITLE, fg=ACCENT, bg=BG_PANEL).pack()

        # Search bar
        search_frame = tk.Frame(self.win, bg=BG_DARK)
        search_frame.pack(fill=tk.X, padx=15, pady=10)

        tk.Label(search_frame, text="Search Customer:",
                 font=FONT_BOLD, fg=TEXT_MUTED, bg=BG_DARK).pack(
            side=tk.LEFT, padx=(0, 8))
        self.search_var = tk.StringVar()
        tk.Entry(search_frame, textvariable=self.search_var,
                 font=FONT_MAIN, bg=BG_INPUT, fg=TEXT_MAIN,
                 insertbackground=TEXT_MAIN,
                 relief=tk.FLAT, bd=4, width=30).pack(side=tk.LEFT)
        make_btn(search_frame, "🔍 Search",
                 "#0077b6", self.do_search, 10).pack(
            side=tk.LEFT, padx=8)

        # Customer list (top)
        cust_frame = tk.LabelFrame(self.win, text="  Customers  ",
                                   font=FONT_BOLD, fg=ACCENT,
                                   bg=BG_PANEL, relief=tk.GROOVE)
        cust_frame.pack(fill=tk.X, padx=15)

        cust_cols = ("ID", "Name", "Mobile", "Loan Type", "Enrolled")
        self.cust_tree = ttk.Treeview(cust_frame, columns=cust_cols,
                                      show="headings", height=4)
        for col in cust_cols:
            self.cust_tree.heading(col, text=col)
            self.cust_tree.column(col, width=140)
        self.cust_tree.pack(padx=8, pady=8, fill=tk.X)
        self.cust_tree.bind("<<TreeviewSelect>>", self.on_customer_select)

        # Payment history (bottom)
        pay_frame = tk.LabelFrame(self.win, text="  Payment Records  ",
                                  font=FONT_BOLD, fg=ACCENT,
                                  bg=BG_PANEL, relief=tk.GROOVE)
        pay_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=8)

        pay_cols = ("Payment ID", "Date", "Time", "Amount Paid (Rs.)")
        self.pay_tree = ttk.Treeview(pay_frame, columns=pay_cols,
                                     show="headings", height=8)
        for col in pay_cols:
            self.pay_tree.heading(col, text=col)
            self.pay_tree.column(col, width=170)
        self.pay_tree.pack(padx=8, pady=8, fill=tk.BOTH, expand=True)

        self.total_label = tk.Label(pay_frame, text="",
                                    font=FONT_BOLD, fg=SUCCESS,
                                    bg=BG_PANEL)
        self.total_label.pack(pady=4)

        self.do_search()

    def do_search(self):
        for row in self.cust_tree.get_children():
            self.cust_tree.delete(row)
        results = search_customers(self.search_var.get())
        for r in results:
            self.cust_tree.insert("", tk.END, values=(
                f"JPCB-{str(r['customer_id']).zfill(5)}",
                r["full_name"], r["mobile"],
                r.get("loan_type", ""),
                r.get("enrolled_date", "")
            ), tags=(r["customer_id"],))

    def on_customer_select(self, _event):
        selected = self.cust_tree.focus()
        if not selected:
            return
        tags = self.cust_tree.item(selected, "tags")
        if not tags:
            return
        customer_id = int(tags[0])

        for row in self.pay_tree.get_children():
            self.pay_tree.delete(row)

        history = get_payment_history(customer_id)
        for p in history:
            self.pay_tree.insert("", tk.END, values=(
                p["payment_id"],
                p["payment_date"],
                p["payment_time"],
                f"Rs. {p['amount_paid']:,.0f}"
            ))

        total = get_total_paid(customer_id)
        self.total_label.config(
            text=f"Total Paid:  Rs. {total:,.0f}")


# ─────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────
class BiometricKYCApp:
    def __init__(self, root):
        self.root        = root
        self.fp_handler  = FingerprintHandler()
        self.cam_handler = CameraHandler()

        root.title("Biometric KYC System — Jalgaon People's Co-operative Bank")
        root.geometry("800x500")
        root.configure(bg=BG_DARK)
        root.resizable(True, True)

        self._build_ui()
        self._check_device()

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg=BG_PANEL, pady=14)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="🏦  JALGAON PEOPLE'S CO-OPERATIVE BANK LTD.",
                 font=FONT_TITLE, fg=ACCENT, bg=BG_PANEL).pack()
        tk.Label(hdr, text="Biometric KYC & Loan Payment System",
                 font=FONT_MAIN, fg=TEXT_MUTED, bg=BG_PANEL).pack()

        # Status bar
        status_bar = tk.Frame(self.root, bg="#0f3460", pady=4)
        status_bar.pack(fill=tk.X)
        self.status_label = tk.Label(
            status_bar, text="⏳ Initializing...",
            font=("Segoe UI", 9), fg=WARNING, bg="#0f3460")
        self.status_label.pack(side=tk.LEFT, padx=10)
        self.clock_label = tk.Label(
            status_bar, text="",
            font=("Segoe UI", 9, "bold"), fg=SUCCESS, bg="#0f3460")
        self.clock_label.pack(side=tk.RIGHT, padx=10)
        self._update_clock()

        # Main buttons
        btn_area = tk.Frame(self.root, bg=BG_DARK)
        btn_area.pack(fill=tk.BOTH, expand=True, pady=40)

        btn_data = [
            ("👤  New Customer\nEnrollment",
             "#1565C0", self.open_enrollment),
            ("💰  Record\nPayment",
             "#2E7D32", self.open_payment),
            ("📋  Payment\nHistory",
             "#6A1B9A", self.open_history),
        ]
        for text, color, cmd in btn_data:
            tk.Button(
                btn_area, text=text, command=cmd,
                bg=color, fg=TEXT_MAIN,
                font=("Segoe UI", 14, "bold"),
                relief=tk.FLAT, cursor="hand2",
                width=18, height=4,
                activebackground=color,
                activeforeground=TEXT_MAIN
            ).pack(side=tk.LEFT, padx=30, expand=True)

        # Footer
        footer = tk.Frame(self.root, bg=BG_PANEL, pady=6)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        tk.Label(footer, text="v1.0  |  Offline Mode ✅  |  All data stored locally",
                 font=("Segoe UI", 8), fg="#888", bg=BG_PANEL).pack()

    def _check_device(self):
        def check():
            connected = self.fp_handler.check_device()
            msg = ("✅ MFS100 Scanner Ready" if connected
                   else "⚠ Scanner not detected — simulation mode")
            color = SUCCESS if connected else WARNING
            self.status_label.config(text=msg, fg=color)
        threading.Thread(target=check, daemon=True).start()

    def _update_clock(self):
        now = datetime.datetime.now().strftime(" %d %b %Y  |   %I:%M:%S %p")
        self.clock_label.config(text=now)
        self.root.after(1000, self._update_clock)

    def open_enrollment(self):
        EnrollmentWindow(self.root, self.fp_handler, self.cam_handler)

    def open_payment(self):
        PaymentWindow(self.root, self.fp_handler)

    def open_history(self):
        HistoryWindow(self.root)


# ─────────────────────────────────────────
#  UTILS
# ─────────────────────────────────────────
def _open_file(path):
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.call(["open", path])
    else:
        subprocess.call(["xdg-open", path])


# ─────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────
if __name__ == "__main__":
    create_tables()
    root = tk.Tk()
    app = BiometricKYCApp(root)
    root.mainloop()