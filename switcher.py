import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import json
import shutil
from PIL import Image, ImageTk
import subprocess
import os
import sys
import ctypes

# === BASE DIR (для exe и py) ===
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# === APPDATA DIR ===
APPDATA_DIR = os.path.join(os.getenv("APPDATA"), "LolilandAccountSwitcher")
PROFILES_DIR = os.path.join(APPDATA_DIR, "profiles")
ACCOUNTS_FILE = os.path.join(APPDATA_DIR, "accounts.json")

# создаём папки при первом запуске
os.makedirs(PROFILES_DIR, exist_ok=True)

# создаём accounts.json если его нет
if not os.path.exists(ACCOUNTS_FILE):
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        f.write("{}")

CONFIG_FILE = os.path.join(APPDATA_DIR, "config.json")

# Загружаем или создаём config.json
if not os.path.exists(CONFIG_FILE):
    config = {}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
else:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        try:
            config = json.load(f)
        except json.JSONDecodeError:
            config = {}


# === ЗАГРУЗКА АККАУНТОВ ===
def load_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        return {}
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_accounts(data):
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# === GUI ===
def refresh_list():
    listbox.delete(0, tk.END)
    for name in accounts:
        listbox.insert(tk.END, name)

def get_launcher_path():
    """
    Проверяет путь к лаунчеру в config.json.
    Если путь существует — возвращает его.
    Если нет — возвращает None.
    """
    path = config.get("launcher_path")
    if path and os.path.exists(path):
        return path
    return None

def choose_launcher_path():
    """
    Запрашивает путь к лаунчеру через диалог,
    сохраняет его в config.json и возвращает путь.
    """
    path = filedialog.askopenfilename(
        title="Выберите exe-файл лаунчера",
        filetypes=[("Executable files", "*.exe")]
    )
    if path:
        config["launcher_path"] = path
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        return path
    return None

def get_target_storage():
    """
    Проверяет путь к storage.txt в config.json.
    Если путь существует — возвращает его.
    Если нет — возвращает None.
    """
    path = config.get("storage_path")
    if path and os.path.exists(path):
        return path
    return None

def choose_target_storage():
    """
    Запрашивает путь к storage.txt через диалог,
    сохраняет его в config.json и возвращает путь.
    """
    path = filedialog.askopenfilename(
        title="Выберите файл storage.txt лаунчера",
        filetypes=[("Text files", "*.txt")]
    )
    if path:
        config["storage_path"] = path
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        return path
    return None



def add_account():
    file_path = filedialog.askopenfilename(
        title="Выберите storage.txt",
        filetypes=[("Text files", "*.txt")]
    )
    if not file_path:
        return

    name = simpledialog.askstring("Имя аккаунта", "Введите имя аккаунта:")
    if not name:
        return

    dest = os.path.join(PROFILES_DIR, f"{name}.txt")

    try:
        shutil.copy(file_path, dest)
        accounts[name] = dest
        save_accounts(accounts)
        refresh_list()
    except Exception as e:
        messagebox.showerror("Ошибка", str(e))

def switch_account(close_after=True):
    selection = listbox.curselection()
    if not selection:
        messagebox.showwarning("Ошибка", "Выберите аккаунт")
        return

    name = listbox.get(selection)
    profile_file = accounts[name]

    try:
        # Получаем пути
        target_storage = get_target_storage()
        launcher_path = get_launcher_path()

        if not target_storage:
            messagebox.showerror(
                "Ошибка",
                "Файл storage.txt не выбран. Нажмите 'Сменить путь к storage.txt'."
            )
            return

        if not launcher_path:
            messagebox.showerror(
                "Ошибка",
                "Путь к лаунчеру не указан. Нажмите 'Сменить путь к лаунчеру'."
            )
            return

        # Копируем профиль
        if os.path.abspath(profile_file) != os.path.abspath(target_storage):
            shutil.copy(profile_file, target_storage)

        # Запускаем лаунчер
        subprocess.Popen(launcher_path)

        # Закрываем свитчер
        if close_after:
            root.destroy()
        else:
            messagebox.showinfo("Готово", f"Аккаунт '{name}' активирован")

    except Exception as e:
        messagebox.showerror("Ошибка", str(e))

def set_app_icon(root, icon_path):
    if os.path.exists(icon_path):
        # Для Tkinter окна
        root.iconbitmap(icon_path)

        try:
            # Для панели задач Windows
            hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
            hicon = ctypes.windll.user32.LoadImageW(0, icon_path, 1, 0, 0, 0x00000010)
            ctypes.windll.user32.SendMessageW(hwnd, 0x80, 0, hicon)
        except Exception as e:
            print("Не удалось установить иконку для панели задач:", e)



def delete_account():
    selection = listbox.curselection()
    if not selection:
        messagebox.showwarning("Ошибка", "Выберите аккаунт")
        return

    name = listbox.get(selection)

    confirm = messagebox.askyesno(
        "Подтверждение",
        f"Удалить аккаунт '{name}'?\nФайл профиля тоже будет удалён."
    )

    if not confirm:
        return

    try:
        profile_path = accounts[name]

        # удаляем файл профиля
        if os.path.exists(profile_path):
            os.remove(profile_path)

        # удаляем из словаря
        del accounts[name]
        save_accounts(accounts)
        refresh_list()

    except Exception as e:
        messagebox.showerror("Ошибка", str(e))

def show_context_menu(event):
    index = listbox.nearest(event.y)
    if index >= 0:
        listbox.selection_clear(0, tk.END)
        listbox.selection_set(index)
        context_menu.tk_popup(event.x_root, event.y_root)


# === ОКНО ===
root = tk.Tk()
root.title("Loliland Account Switcher")
root.geometry("350x450")
BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
icon_path = os.path.join(BASE_DIR, "icon.ico")

if os.path.exists(icon_path):
    root.iconbitmap(icon_path)

try:
    from ctypes import windll
    hwnd = windll.user32.GetParent(root.winfo_id())
    hicon = windll.user32.LoadImageW(0, icon_path, 1, 0, 0, 0x00000010)  # IMAGE_ICON
    windll.user32.SendMessageW(hwnd, 0x80, 0, hicon)  # WM_SETICON
except Exception:
    pass

# Размер окна
window_width = 400
window_height = 500

# Получаем размер экрана
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Вычисляем координаты центра
x = int((screen_width - window_width) / 2)
y = int((screen_height - window_height) / 2)

# Задаём геометрию окна
root.geometry(f"{window_width}x{window_height}+{x}+{y}")
root.resizable(False, False)


accounts = load_accounts()

listbox = tk.Listbox(root, font=("Segoe UI", 10))
listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
listbox.bind("<Double-Button-1>", lambda event: switch_account(close_after=True))
listbox.bind("<Button-3>", show_context_menu)  # ПКМ


context_menu = tk.Menu(root, tearoff=0)
context_menu.add_command(label="🗑 Удалить аккаунт", command=delete_account)



tk.Button(root, text="➕ Добавить аккаунт", command=add_account).pack(
    fill=tk.X, padx=10, pady=5
)

tk.Button(
    root,
    text="🗑 Удалить аккаунт",
    command=delete_account
).pack(fill=tk.X, padx=10, pady=5)

tk.Button(
    root,
    text="⚙ Указать путь к лаунчеру",
    command=choose_launcher_path
).pack(fill=tk.X, padx=10, pady=5)

tk.Button(
    root,
    text="⚙ Указать путь к storage.txt",
    command=choose_target_storage
).pack(fill=tk.X, padx=10, pady=5)


refresh_list()
root.mainloop()
