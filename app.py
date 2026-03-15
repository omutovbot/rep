import json
import random
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

# Локальный файл для хранения списка дел.
TASKS_FILE = Path("tasks.json")
MAX_TASK_LENGTH = 200


class TaskPickerApp:
    """Простое desktop-приложение для выбора случайного дела из списка."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Случайное дело")
        self.root.geometry("760x560")
        self.root.minsize(700, 520)
        self.root.configure(bg="#f5f7fb")

        # Данные приложения.
        self.tasks: list[str] = []
        self.is_notepad_open = True

        # Служебные поля для анимации.
        self.animation_id: str | None = None
        self.animation_sequence: list[str] = []
        self.animation_step = 0
        self.final_task = ""

        self._build_ui()
        self._load_tasks()
        self._render_tasks_in_editor()

    def _build_ui(self) -> None:
        """Создаёт и настраивает все виджеты интерфейса."""
        # Основной контейнер.
        main = tk.Frame(self.root, bg="#f5f7fb", padx=20, pady=20)
        main.pack(fill="both", expand=True)

        title = tk.Label(
            main,
            text="Выбор случайного дела",
            font=("Segoe UI", 24, "bold"),
            fg="#1f2a44",
            bg="#f5f7fb",
        )
        title.pack(anchor="w", pady=(0, 12))

        subtitle = tk.Label(
            main,
            text="Введите дела в блокнот и выберите, чем заняться прямо сейчас.",
            font=("Segoe UI", 11),
            fg="#4b5a78",
            bg="#f5f7fb",
        )
        subtitle.pack(anchor="w", pady=(0, 16))

        # Блок кнопок действий.
        actions = tk.Frame(main, bg="#f5f7fb")
        actions.pack(fill="x", pady=(0, 12))

        self.toggle_notepad_button = tk.Button(
            actions,
            text="Свернуть блокнот",
            font=("Segoe UI", 10, "bold"),
            bg="#2667ff",
            fg="white",
            activebackground="#1451dd",
            activeforeground="white",
            bd=0,
            padx=14,
            pady=10,
            command=self.toggle_notepad,
            cursor="hand2",
        )
        self.toggle_notepad_button.pack(side="left", padx=(0, 10))

        self.choose_button = tk.Button(
            actions,
            text="Выбрать дело",
            font=("Segoe UI", 10, "bold"),
            bg="#00a878",
            fg="white",
            activebackground="#018b64",
            activeforeground="white",
            bd=0,
            padx=14,
            pady=10,
            command=self.choose_task,
            cursor="hand2",
        )
        self.choose_button.pack(side="left", padx=(0, 10))

        self.choose_again_button = tk.Button(
            actions,
            text="Выбрать ещё раз",
            font=("Segoe UI", 10, "bold"),
            bg="#4e5d78",
            fg="white",
            activebackground="#3b4760",
            activeforeground="white",
            bd=0,
            padx=14,
            pady=10,
            command=self.choose_task,
            cursor="hand2",
        )
        self.choose_again_button.pack(side="left", padx=(0, 10))

        self.clear_button = tk.Button(
            actions,
            text="Очистить список",
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg="#b42318",
            activebackground="#fef3f2",
            activeforeground="#b42318",
            highlightthickness=1,
            highlightbackground="#fecdca",
            padx=14,
            pady=10,
            command=self.clear_tasks,
            cursor="hand2",
        )
        self.clear_button.pack(side="right")

        # Карточка блокнота.
        self.notepad_card = tk.Frame(main, bg="white", bd=0, highlightthickness=1, highlightbackground="#dbe1f0")
        self.notepad_card.pack(fill="both", expand=True)

        card_header = tk.Frame(self.notepad_card, bg="white")
        card_header.pack(fill="x", padx=14, pady=(14, 8))

        tk.Label(
            card_header,
            text="Блокнот дел (каждое дело с новой строки)",
            font=("Segoe UI", 11, "bold"),
            fg="#1f2a44",
            bg="white",
        ).pack(side="left")

        self.save_button = tk.Button(
            card_header,
            text="Сохранить и свернуть",
            font=("Segoe UI", 9, "bold"),
            bg="#2667ff",
            fg="white",
            activebackground="#1451dd",
            activeforeground="white",
            bd=0,
            padx=12,
            pady=7,
            command=self.save_and_collapse,
            cursor="hand2",
        )
        self.save_button.pack(side="right")

        text_wrap = tk.Frame(self.notepad_card, bg="white")
        text_wrap.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        self.text_editor = tk.Text(
            text_wrap,
            height=12,
            wrap="word",
            font=("Consolas", 11),
            bd=0,
            highlightthickness=1,
            highlightbackground="#cfd8ea",
            padx=10,
            pady=10,
        )
        self.text_editor.pack(side="left", fill="both", expand=True)

        text_scroll = tk.Scrollbar(text_wrap, command=self.text_editor.yview)
        text_scroll.pack(side="right", fill="y")
        self.text_editor.configure(yscrollcommand=text_scroll.set)

        # Блок показа выбранного дела.
        result_card = tk.Frame(main, bg="#eef3ff", highlightthickness=1, highlightbackground="#ced7f1")
        result_card.pack(fill="x", pady=(12, 0))

        tk.Label(
            result_card,
            text="Выбранное дело",
            font=("Segoe UI", 11, "bold"),
            fg="#2b3d66",
            bg="#eef3ff",
        ).pack(anchor="w", padx=14, pady=(12, 4))

        self.result_label = tk.Label(
            result_card,
            text="Пока ничего не выбрано",
            font=("Segoe UI", 24, "bold"),
            fg="#0a1f52",
            bg="#eef3ff",
            justify="left",
            wraplength=680,
        )
        self.result_label.pack(anchor="w", padx=14, pady=(4, 16))

    def _load_tasks(self) -> None:
        """Загружает список дел из tasks.json, если файл уже существует."""
        if not TASKS_FILE.exists():
            self.tasks = []
            return

        try:
            raw = json.loads(TASKS_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                loaded_tasks = []
                for item in raw:
                    if isinstance(item, str):
                        task = item.strip()
                        if task and task not in loaded_tasks:
                            loaded_tasks.append(task)
                self.tasks = loaded_tasks
            else:
                self.tasks = []
        except (json.JSONDecodeError, OSError):
            self.tasks = []

    def _save_tasks_to_file(self) -> None:
        """Сохраняет текущий список дел в tasks.json."""
        TASKS_FILE.write_text(
            json.dumps(self.tasks, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _render_tasks_in_editor(self) -> None:
        """Отображает текущий список дел в текстовом поле."""
        self.text_editor.delete("1.0", tk.END)
        if self.tasks:
            self.text_editor.insert("1.0", "\n".join(self.tasks))

    def _parse_editor_tasks(self) -> list[str]:
        """Считывает задачи из текстового поля с валидацией и удалением дублей."""
        content = self.text_editor.get("1.0", tk.END)
        lines = content.splitlines()

        cleaned_tasks = []
        seen = set()
        for index, line in enumerate(lines, start=1):
            task = line.strip()

            # Пустые строки пропускаем.
            if not task:
                continue

            if len(task) > MAX_TASK_LENGTH:
                raise ValueError(
                    f"Строка {index} слишком длинная ({len(task)} символов). "
                    f"Максимум: {MAX_TASK_LENGTH}."
                )

            # Не сохраняем дубликаты.
            if task not in seen:
                cleaned_tasks.append(task)
                seen.add(task)

        return cleaned_tasks

    def toggle_notepad(self) -> None:
        """Показывает или скрывает блокнот."""
        if self.is_notepad_open:
            self.notepad_card.pack_forget()
            self.toggle_notepad_button.configure(text="Открыть блокнот")
            self.is_notepad_open = False
        else:
            self.notepad_card.pack(fill="both", expand=True, before=self.result_label.master, pady=(0, 0))
            self.toggle_notepad_button.configure(text="Свернуть блокнот")
            self.is_notepad_open = True

    def save_and_collapse(self) -> None:
        """Сохраняет список задач, затем сворачивает блокнот."""
        try:
            parsed = self._parse_editor_tasks()
        except ValueError as error:
            messagebox.showerror("Ошибка ввода", str(error))
            return

        self.tasks = parsed
        try:
            self._save_tasks_to_file()
        except OSError as error:
            messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить tasks.json:\n{error}")
            return

        messagebox.showinfo("Сохранено", f"Сохранено дел: {len(self.tasks)}")
        if self.is_notepad_open:
            self.toggle_notepad()

    def clear_tasks(self) -> None:
        """Очищает задачи в интерфейсе и в файле."""
        if not messagebox.askyesno("Подтверждение", "Очистить весь список дел?"):
            return

        self.tasks = []
        self.text_editor.delete("1.0", tk.END)
        self.result_label.configure(text="Список очищен")

        try:
            self._save_tasks_to_file()
        except OSError as error:
            messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить tasks.json:\n{error}")

    def choose_task(self) -> None:
        """Запускает анимацию случайного выбора дела."""
        # Если блокнот открыт, пробуем сначала взять актуальные данные из него.
        if self.is_notepad_open:
            try:
                self.tasks = self._parse_editor_tasks()
            except ValueError as error:
                messagebox.showerror("Ошибка ввода", str(error))
                return

        if len(self.tasks) < 2:
            messagebox.showwarning(
                "Недостаточно данных",
                "Для выбора нужно минимум 2 разных дела. Добавьте ещё пункты в блокнот.",
            )
            return

        # Останавливаем прошлую анимацию, если пользователь нажал кнопку снова.
        if self.animation_id is not None:
            self.root.after_cancel(self.animation_id)
            self.animation_id = None

        self._build_animation_sequence()
        self.animation_step = 0
        self._animate_roll()

    def _build_animation_sequence(self) -> None:
        """Готовит последовательность задач для эффекта прокрутки с замедлением."""
        self.final_task = random.choice(self.tasks)

        seq = [random.choice(self.tasks) for _ in range(22)]
        seq.extend([random.choice(self.tasks) for _ in range(8)])
        seq.append(self.final_task)

        # Последний элемент всегда финальный выбранный вариант.
        self.animation_sequence = seq

    def _animate_roll(self) -> None:
        """Покадровая анимация выбора через безопасный after() без потоков."""
        if self.animation_step >= len(self.animation_sequence):
            self.result_label.configure(text=self.final_task)
            self.animation_id = None
            return

        current_task = self.animation_sequence[self.animation_step]
        self.result_label.configure(text=current_task)

        # В начале быстро, в конце медленнее.
        step = self.animation_step
        if step < 10:
            delay_ms = 45
        elif step < 18:
            delay_ms = 90
        elif step < 25:
            delay_ms = 150
        else:
            delay_ms = 240

        self.animation_step += 1
        self.animation_id = self.root.after(delay_ms, self._animate_roll)


if __name__ == "__main__":
    root_window = tk.Tk()
    app = TaskPickerApp(root_window)
    root_window.mainloop()
