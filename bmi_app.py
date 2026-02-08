import tkinter as tk
from tkinter import messagebox, ttk
import datetime
import csv
import os

# Try to import fpdf to prevent errors if it's missing locally
try:
    from fpdf import FPDF 
except ImportError:
    print("PDF library not found. Run 'pip install fpdf' to enable reports.")

# --- Configuration & Styling ---
BG_COLOR = "#f4f7f6"
PRIMARY_COLOR = "#2c3e50"
ACCENT_COLOR = "#3498db"
SUCCESS_COLOR = "#27ae60"

class HealthApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ProHealth Management System v4.0")
        self.geometry("800x900")
        self.configure(bg=BG_COLOR)
        
        self.current_user = None
        self.users = {"admin": "password123"} 

        self.container = tk.Frame(self, bg=BG_COLOR)
        self.container.pack(side="top", fill="both", expand=True)

        self.frames = {}
        for F in (LoginPage, RegisterPage, DashboardPage, HistoryPage):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("LoginPage")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        if page_name == "HistoryPage":
            frame.load_history()

# --- PAGES ---
class LoginPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller
        tk.Label(self, text="USER LOGIN", font=("Verdana", 28, "bold"), bg="white", fg=PRIMARY_COLOR).pack(pady=50)
        self.user_entry = tk.Entry(self, font=("Arial", 16), width=25, bd=2, relief="groove")
        self.user_entry.insert(0, "admin")
        self.user_entry.pack(pady=10)
        self.pass_entry = tk.Entry(self, show="*", font=("Arial", 16), width=25, bd=2, relief="groove")
        self.pass_entry.insert(0, "password123")
        self.pass_entry.pack(pady=10)
        tk.Button(self, text="LOGIN", font=("Arial", 12, "bold"), bg=SUCCESS_COLOR, fg="white", width=20, pady=10, command=self.login).pack(pady=30)
        tk.Button(self, text="Register New Account", command=lambda: controller.show_frame("RegisterPage"), bg="white", bd=0).pack()

    def login(self):
        u, p = self.user_entry.get(), self.pass_entry.get()
        if u in self.controller.users and self.controller.users[u] == p:
            self.controller.current_user = u
            self.controller.show_frame("DashboardPage")
        else:
            messagebox.showerror("Error", "Invalid Login")

class RegisterPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller
        tk.Label(self, text="REGISTER", font=("Verdana", 24, "bold"), bg="white").pack(pady=40)
        self.u_reg = tk.Entry(self, font=("Arial", 14)); self.u_reg.pack(pady=10)
        self.p_reg = tk.Entry(self, show="*", font=("Arial", 14)); self.p_reg.pack(pady=10)
        tk.Button(self, text="SIGN UP", bg=ACCENT_COLOR, fg="white", command=self.register_user).pack(pady=20)
        tk.Button(self, text="Back", command=lambda: controller.show_frame("LoginPage")).pack()

    def register_user(self):
        u, p = self.u_reg.get(), self.p_reg.get()
        if u and p:
            self.controller.users[u] = p
            messagebox.showinfo("Success", "Account created!")
            self.controller.show_frame("LoginPage")

class DashboardPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_COLOR)
        self.controller = controller
        nav = tk.Frame(self, bg=PRIMARY_COLOR, height=60); nav.pack(fill="x")
        tk.Label(nav, text="HEALTH DASHBOARD", fg="white", bg=PRIMARY_COLOR, font=("Arial", 14, "bold")).pack(side="left", padx=20)
        tk.Button(nav, text="History", bg=ACCENT_COLOR, fg="white", command=lambda: controller.show_frame("HistoryPage")).pack(side="right", padx=10)

        card = tk.Frame(self, bg="white", bd=1, relief="solid"); card.pack(pady=30, padx=50, fill="both")
        tk.Label(card, text="Weight (kg):", bg="white").pack(pady=5)
        self.w_ent = tk.Entry(card, font=("Arial", 14)); self.w_ent.pack(pady=5)
        tk.Label(card, text="Height (m):", bg="white").pack(pady=5)
        self.h_ent = tk.Entry(card, font=("Arial", 14)); self.h_ent.pack(pady=5)

        tk.Button(card, text="CALCULATE", bg=SUCCESS_COLOR, fg="white", font=("Arial", 12, "bold"), command=self.process_health).pack(pady=20)
        self.res_label = tk.Label(card, text="---", font=("Arial", 28, "bold"), bg="white"); self.res_label.pack()
        self.status_label = tk.Label(card, text="", font=("Arial", 16), bg="white"); self.status_label.pack()

        self.btn_save = tk.Button(card, text="💾 Save to Database", state="disabled", command=self.save_data)
        self.btn_save.pack(pady=5)
        self.btn_pdf = tk.Button(card, text="📄 Download PDF Report", state="disabled", bg="#e67e22", fg="white", command=self.export_pdf)
        self.btn_pdf.pack(pady=5)

    def process_health(self):
        try:
            self.w, self.h = float(self.w_ent.get()), float(self.h_ent.get())
            self.bmi = round(self.w / (self.h**2), 2)
            if self.bmi < 18.5: self.status, self.col = "Underweight", "#3498db"
            elif 18.5 <= self.bmi < 24.9: self.status, self.col = "Normal", "#2ecc71"
            else: self.status, self.col = "Overweight", "#e74c3c"
            
            self.res_label.config(text=f"BMI: {self.bmi}", fg=self.col)
            self.status_label.config(text=self.status, fg=self.col)
            self.btn_save.config(state="normal"); self.btn_pdf.config(state="normal")
        except:
            messagebox.showerror("Error", "Enter valid numbers")

    def save_data(self):
        with open("health_history.csv", "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([datetime.datetime.now().strftime("%Y-%m-%d"), self.controller.current_user, self.bmi, self.status])
        messagebox.showinfo("Saved", "Record Added")

    def export_pdf(self):
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 20)
            pdf.cell(200, 20, txt="ProHealth Medical Report", ln=True, align='C')
            pdf.set_font("Arial", size=12)
            pdf.ln(10)
            pdf.cell(200, 10, txt=f"Patient: {self.controller.current_user}", ln=True)
            pdf.cell(200, 10, txt=f"BMI Result: {self.bmi}", ln=True)
            pdf.cell(200, 10, txt=f"Status: {self.status}", ln=True)
            
            filename = f"Report_{self.controller.current_user}.pdf"
            pdf.output(filename)
            messagebox.showinfo("PDF Export", f"Saved as {filename}")
        except Exception as e:
            messagebox.showerror("PDF Error", str(e))

class HistoryPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller
        tk.Label(self, text="HEALTH HISTORY", font=("Arial", 18, "bold"), bg="white").pack(pady=20)
        self.tree = ttk.Treeview(self, columns=("Date", "BMI", "Status"), show='headings')
        self.tree.heading("Date", text="Date"); self.tree.heading("BMI", text="BMI"); self.tree.heading("Status", text="Status")
        self.tree.pack(fill="both", expand=True, padx=20)
        tk.Button(self, text="Back to Dashboard", command=lambda: controller.show_frame("DashboardPage")).pack(pady=20)

    def load_history(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        if os.path.exists("health_history.csv"):
            with open("health_history.csv", "r") as f:
                reader = csv.reader(f)
                for row in reader:
                    if row and row[1] == self.controller.current_user:
                        self.tree.insert("", "end", values=(row[0], row[2], row[3]))

if __name__ == "__main__":
    app = HealthApp()
    app.mainloop()