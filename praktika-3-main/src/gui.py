"""
GUI системы учета заявок на ремонт бытовой техники.
Поддерживает роли пользователей и авторизацию.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
from typing import Optional
import logging

from src.database import get_database
from src.models import STATUS_CHOICES, DEVICE_TYPES
from src.utils import validate_phone_number, format_phone_number

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServiceCenterApp(tk.Tk):
    """
    Главное окно приложения.
    """

    def __init__(self):
        super().__init__()

        self.title("Система учета заявок на ремонт")
        self.geometry("1200x700")
        self.minsize(1000, 600)

        self.db = get_database()
        self.current_user = None

        self._setup_styles()
        self._create_widgets()
        self._center_window()

    # =========================
    # ПОЛЬЗОВАТЕЛЬ И РОЛИ
    # =========================

    def set_current_user(self, user: dict):
        """
        Установка текущего пользователя и применение ролевых ограничений.
        """
        self.current_user = user

        self.title(
            f"Система учета заявок | {user['full_name']} ({user['role']})"
        )

        role = user["role"]

        # Ограничения по ролям
        if role not in ("admin", "operator"):
            self.add_button.state(["disabled"])

        if role not in ("admin", "master"):
            self.comment_button.state(["disabled"])
            self.status_button.state(["disabled"])

        if role not in ("admin", "manager"):
            self.extend_button.state(["disabled"])

    # =========================
    # НАСТРОЙКА ИНТЕРФЕЙСА
    # =========================

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Title.TLabel", font=("Arial", 16, "bold"))
        style.configure("Error.TButton", foreground="red")
        style.configure("Success.TButton", foreground="green")

    def _center_window(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    # =========================
    # СОЗДАНИЕ ВИДЖЕТОВ
    # =========================

    def _create_widgets(self):
        container = ttk.Frame(self, padding=10)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            container,
            text="Система учета заявок на ремонт бытовой техники",
            style="Title.TLabel"
        ).pack(pady=10)

        self._create_toolbar(container)
        self._create_table(container)
        self._create_details(container)
        self._create_status_bar(container)

        self._load_requests()

    def _create_toolbar(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)

        self.add_button = ttk.Button(
            frame, text="Новая заявка", command=self._add_request
        )
        self.add_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            frame, text="Обновить", command=self._load_requests
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            frame, text="Статистика", command=self._show_statistics
        ).pack(side=tk.LEFT, padx=5)

        self.extend_button = ttk.Button(
            frame, text="Продлить срок (менеджер)", command=self._extend_deadline
        )
        self.extend_button.pack(side=tk.LEFT, padx=20)

        ttk.Label(frame, text="Поиск:").pack(side=tk.RIGHT, padx=5)
        self.search_var = tk.StringVar()
        entry = ttk.Entry(frame, textvariable=self.search_var, width=25)
        entry.pack(side=tk.RIGHT)
        entry.bind("<Return>", lambda _: self._search())

    def _create_table(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)

        columns = (
            "ID", "Дата", "Устройство", "Модель",
            "Клиент", "Статус", "Мастер", "Срок"
        )

        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor=tk.CENTER)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", self._show_details)

        scrollbar = ttk.Scrollbar(
            frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

    def _create_details(self, parent):
        frame = ttk.LabelFrame(parent, text="Детали заявки", padding=10)
        frame.pack(fill=tk.BOTH, expand=False, pady=5)

        self.details = scrolledtext.ScrolledText(
            frame, height=10, wrap=tk.WORD
        )
        self.details.pack(fill=tk.BOTH, expand=True)

        btns = ttk.Frame(frame)
        btns.pack(fill=tk.X, pady=5)

        self.status_button = ttk.Button(
            btns, text="Изменить статус", command=self._change_status
        )
        self.status_button.pack(side=tk.LEFT, padx=5)

        self.comment_button = ttk.Button(
            btns, text="Комментарий", command=self._add_comment
        )
        self.comment_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btns, text="Удалить", style="Error.TButton",
            command=self._delete_request
        ).pack(side=tk.LEFT, padx=5)

    def _create_status_bar(self, parent):
        self.status_bar = ttk.Label(parent, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X)

    # =========================
    # ЛОГИКА
    # =========================

    def _load_requests(self):
        self.tree.delete(*self.tree.get_children())
        requests = self.db.get_all_requests()

        for r in requests:
            self.tree.insert(
                "", tk.END, iid=r["id"],
                values=(
                    r["id"],
                    r["created_date"][:19],
                    r["device_type"],
                    r["device_model"],
                    r["client_name"],
                    r["status"],
                    r["master_name"] or "-",
                    r["deadline"] or "-"
                )
            )

        self.status_bar.config(text=f"Загружено заявок: {len(requests)}")

    def _get_selected_id(self) -> Optional[int]:
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def _show_details(self, _=None):
        rid = self._get_selected_id()
        if not rid:
            return

        req = next(r for r in self.db.get_all_requests() if r["id"] == rid)

        text = (
            f"Заявка №{req['id']}\n"
            f"Дата: {req['created_date']}\n"
            f"Статус: {req['status']}\n"
            f"Мастер: {req['master_name'] or 'Не назначен'}\n"
            f"Срок: {req['deadline'] or 'Не задан'}\n\n"
            f"Клиент: {req['client_name']}\n"
            f"Телефон: {req['client_phone']}\n\n"
            f"Устройство: {req['device_type']}\n"
            f"Модель: {req['device_model']}\n\n"
            f"Проблема:\n{req['problem_description']}"
        )

        self.details.delete(1.0, tk.END)
        self.details.insert(tk.END, text)

    # =========================
    # ДЕЙСТВИЯ
    # =========================

    def _add_request(self):
        dialog = AddRequestDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            self._load_requests()

    def _change_status(self):
        rid = self._get_selected_id()
        if not rid:
            messagebox.showwarning("Внимание", "Выберите заявку")
            return

        dialog = ChangeStatusDialog(self, rid)
        self.wait_window(dialog)
        if dialog.result:
            self._load_requests()
            self._show_details()

    def _add_comment(self):
        rid = self._get_selected_id()
        if not rid:
            messagebox.showwarning("Внимание", "Выберите заявку")
            return

        AddCommentDialog(self, rid)

    def _extend_deadline(self):
        rid = self._get_selected_id()
        if not rid:
            messagebox.showwarning("Внимание", "Выберите заявку")
            return

        new_date = simpledialog.askstring(
            "Продление срока", "Новая дата (YYYY-MM-DD):"
        )
        if not new_date:
            return

        if self.db.extend_deadline(rid, new_date):
            self._load_requests()
            self._show_details()
            messagebox.showinfo("Успешно", "Срок продлён")

    def _delete_request(self):
        rid = self._get_selected_id()
        if not rid:
            return

        if not messagebox.askyesno(
            "Подтверждение", f"Удалить заявку №{rid}?"
        ):
            return

        self.db.cursor.execute(
            "DELETE FROM requests WHERE id = ?", (rid,)
        )
        self.db.connection.commit()

        self._load_requests()
        self.details.delete(1.0, tk.END)

    def _search(self):
        term = self.search_var.get().strip()
        if not term:
            self._load_requests()
            return

        self.tree.delete(*self.tree.get_children())
        results = self.db.search_requests(term)

        for r in results:
            self.tree.insert(
                "", tk.END, iid=r["id"],
                values=(
                    r["id"],
                    r["created_date"][:19],
                    r["device_type"],
                    r["device_model"],
                    r["client_name"],
                    r["status"],
                    r["master_name"] or "-",
                    r["deadline"] or "-"
                )
            )

        self.status_bar.config(text=f"Найдено: {len(results)}")

    def _show_statistics(self):
        stats = self.db.get_request_statistics()

        text = f"Всего заявок: {stats['total_requests']}\n\n"
        text += "По статусам:\n"
        for s, c in stats["status_counts"].items():
            text += f"  {s}: {c}\n"
        text += f"\nСреднее время выполнения: {stats['average_completion_hours']} ч"

        win = tk.Toplevel(self)
        win.title("Статистика")

        st = scrolledtext.ScrolledText(win, width=50, height=20)
        st.pack(fill=tk.BOTH, expand=True)
        st.insert(tk.END, text)
        st.config(state=tk.DISABLED)


# =========================
# ДИАЛОГИ
# =========================

class AddRequestDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.result = False

        self.title("Новая заявка")
        self.geometry("400x450")
        self.resizable(False, False)

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Тип устройства").pack(anchor=tk.W)
        self.device = ttk.Combobox(frame, values=DEVICE_TYPES, state="readonly")
        self.device.pack(fill=tk.X)

        ttk.Label(frame, text="Модель").pack(anchor=tk.W, pady=(10, 0))
        self.model = ttk.Entry(frame)
        self.model.pack(fill=tk.X)

        ttk.Label(frame, text="Описание проблемы").pack(anchor=tk.W, pady=(10, 0))
        self.problem = scrolledtext.ScrolledText(frame, height=5)
        self.problem.pack(fill=tk.X)

        ttk.Label(frame, text="ФИО клиента").pack(anchor=tk.W, pady=(10, 0))
        self.client = ttk.Entry(frame)
        self.client.pack(fill=tk.X)

        ttk.Label(frame, text="Телефон").pack(anchor=tk.W, pady=(10, 0))
        self.phone = ttk.Entry(frame)
        self.phone.pack(fill=tk.X)

        ttk.Button(
            frame, text="Добавить", style="Success.TButton",
            command=self._save
        ).pack(pady=15)

    def _save(self):
        phone = self.phone.get().strip()
        if not validate_phone_number(phone):
            messagebox.showerror("Ошибка", "Неверный номер телефона")
            return

        self.parent.db.add_request(
            self.device.get(),
            self.model.get(),
            self.problem.get(1.0, tk.END).strip(),
            self.client.get(),
            format_phone_number(phone)
        )

        self.result = True
        self.destroy()


class ChangeStatusDialog(tk.Toplevel):
    def __init__(self, parent, request_id):
        super().__init__(parent)
        self.parent = parent
        self.request_id = request_id
        self.result = False

        self.title("Изменение статуса")
        self.geometry("300x300")

        self.status = tk.StringVar()
        self.master = tk.StringVar()

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        for text, value in STATUS_CHOICES:
            ttk.Radiobutton(
                frame, text=text,
                variable=self.status, value=value
            ).pack(anchor=tk.W)

        ttk.Label(frame, text="Мастер").pack(anchor=tk.W, pady=(10, 0))
        ttk.Entry(frame, textvariable=self.master).pack(fill=tk.X)

        ttk.Button(
            frame, text="Сохранить", style="Success.TButton",
            command=self._save
        ).pack(pady=15)

    def _save(self):
        if not self.status.get():
            return

        self.parent.db.update_request_status(
            self.request_id,
            self.status.get(),
            self.master.get() or None
        )

        self.result = True
        self.destroy()


class AddCommentDialog(tk.Toplevel):
    def __init__(self, parent, request_id):
        super().__init__(parent)
        self.parent = parent
        self.request_id = request_id

        self.title("Комментарий")
        self.geometry("400x350")

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Комментарий").pack(anchor=tk.W)
        self.comment = scrolledtext.ScrolledText(frame, height=6)
        self.comment.pack(fill=tk.X)

        ttk.Label(frame, text="Запчасти").pack(anchor=tk.W, pady=(10, 0))
        self.parts = ttk.Entry(frame)
        self.parts.pack(fill=tk.X)

        ttk.Label(frame, text="Автор").pack(anchor=tk.W, pady=(10, 0))
        self.author = ttk.Entry(frame)
        self.author.pack(fill=tk.X)

        ttk.Button(
            frame, text="Добавить", style="Success.TButton",
            command=self._save
        ).pack(pady=15)

    def _save(self):
        self.parent.db.add_comment(
            self.request_id,
            self.comment.get(1.0, tk.END).strip(),
            self.parts.get(),
            self.author.get()
        )
        self.destroy()

