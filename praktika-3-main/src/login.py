import tkinter as tk
from tkinter import ttk, messagebox
from src.database import get_database
from src.utils import hash_password

class LoginWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.result = None

        self.title("Авторизация")
        self.geometry("300x200")
        self.resizable(False, False)

        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Логин").pack(anchor=tk.W)
        self.login = ttk.Entry(frame)
        self.login.pack(fill=tk.X)

        ttk.Label(frame, text="Пароль").pack(anchor=tk.W, pady=(10, 0))
        self.password = ttk.Entry(frame, show="*")
        self.password.pack(fill=tk.X)

        ttk.Button(frame, text="Войти", command=self._auth).pack(pady=15)

    def _auth(self):
        db = get_database()
        login = self.login.get().strip()
        password = hash_password(self.password.get().strip())

        db.cursor.execute("""
            SELECT username, role, full_name
            FROM users
            WHERE username = ? AND password_hash = ?
        """, (login, password))

        user = db.cursor.fetchone()
        if not user:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")
            return

        self.result = {
            "username": user["username"],
            "role": user["role"],
            "full_name": user["full_name"]
        }
        self.destroy()
