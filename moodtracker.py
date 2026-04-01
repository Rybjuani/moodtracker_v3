#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MoodTracker v4 — escritorio + Android."""

import datetime
import json
import os
import platform
import sys

IS_WIN = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"
IS_ANDROID = "ANDROID_ARGUMENT" in os.environ or platform.system() == "Android"
SCRIPT = os.path.abspath(__file__)

FN = "Segoe UI" if IS_WIN else "DejaVu Sans"

BG = "#0f0f18"
CARD = "#16161f"
CARD2 = "#1c1c28"
BORDER = "#28283a"
ACCENT = "#6c63ff"
ACCT2 = "#9088ff"
TEXT = "#eeeefc"
MUTED = "#55556a"
MUTED2 = "#35354a"

DESCS = [
    "Malestar extremo", "Malestar severo", "Muy mal", "Bastante mal",
    "Mal", "Algo mal", "Bajo", "Un poco bajo", "Levemente bajo",
    "Casi neutral", "Neutral", "Levemente bien", "Algo bien",
    "Un poco bien", "Bien", "Bastante bien", "Muy bien",
    "Genial", "Excelente", "Extraordinario", "Bienestar total",
]


def lerp(a, b, t):
    return int(a + (b - a) * t)


def mood_color(val):
    t = (val + 10) / 20.0
    stops = [
        (0.00, (190, 20, 20)),
        (0.30, (210, 90, 20)),
        (0.48, (140, 110, 50)),
        (0.50, (70, 70, 85)),
        (0.52, (50, 120, 55)),
        (0.70, (30, 185, 75)),
        (1.00, (15, 150, 55)),
    ]
    for i in range(len(stops) - 1):
        t0, c0 = stops[i]
        t1, c1 = stops[i + 1]
        if t0 <= t <= t1:
            f = (t - t0) / (t1 - t0)
            return "#{:02x}{:02x}{:02x}".format(
                lerp(c0[0], c1[0], f),
                lerp(c0[1], c1[1], f),
                lerp(c0[2], c1[2], f),
            )
    return "#505060"


def mood_color_rgba(val, alpha=1.0):
    col = mood_color(val).lstrip("#")
    return tuple(int(col[i:i + 2], 16) / 255.0 for i in (0, 2, 4)) + (alpha,)


def hex_rgba(value, alpha=1.0):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255.0 for i in (0, 2, 4)) + (alpha,)


def mood_emoji(val):
    if val <= -9:
        return "😭"
    if val <= -7:
        return "😢"
    if val <= -5:
        return "😔"
    if val <= -3:
        return "😕"
    if val <= -1:
        return "😶"
    if val == 0:
        return "😐"
    if val <= 2:
        return "🙂"
    if val <= 4:
        return "😌"
    if val <= 6:
        return "😊"
    if val <= 8:
        return "😁"
    return "🌟"


def get_data_dir():
    if IS_ANDROID:
        try:
            from kivy.app import App
            app = App.get_running_app()
            if app and app.user_data_dir:
                return app.user_data_dir
        except Exception:
            pass
        return os.path.join(os.path.expanduser("~"), ".moodtracker_android")
    if IS_WIN:
        return os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "MoodTracker")
    return os.path.expanduser("~/.moodtracker")


def data_file():
    return os.path.join(get_data_dir(), "data.json")


def load_data():
    os.makedirs(get_data_dir(), exist_ok=True)
    path = data_file()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        for key in ("entries", "daily", "weekly", "monthly"):
            data.setdefault(key, [] if key == "entries" else {})
        return data
    return {"entries": [], "daily": {}, "weekly": {}, "monthly": {}}


def save_data(data):
    os.makedirs(get_data_dir(), exist_ok=True)
    with open(data_file(), "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def recalculate(data):
    today = datetime.date.today().isoformat()
    by_date = {}
    for entry in data["entries"]:
        by_date.setdefault(entry["date"], []).append(entry["value"])

    data["daily"] = {}
    for date_key, values in by_date.items():
        if date_key != today:
            data["daily"][date_key] = round(sum(values) / len(values), 2)

    by_week = {}
    for date_key, avg in data["daily"].items():
        dt = datetime.date.fromisoformat(date_key)
        week_key = f"{dt.isocalendar()[0]}-W{dt.isocalendar()[1]:02d}"
        by_week.setdefault(week_key, []).append(avg)

    data["weekly"] = {}
    for week_key, values in by_week.items():
        data["weekly"][week_key] = round(sum(values) / len(values), 2)

    by_month = {}
    for date_key, avg in data["daily"].items():
        month_key = date_key[:7]
        by_month.setdefault(month_key, []).append(avg)

    data["monthly"] = {}
    for month_key, values in by_month.items():
        data["monthly"][month_key] = round(sum(values) / len(values), 2)

    save_data(data)


def today_stats(data):
    today = datetime.date.today().isoformat()
    values = [entry["value"] for entry in data["entries"] if entry["date"] == today]
    if not values:
        return None, 0
    return round(sum(values) / len(values), 2), len(values)


def history_items(data, tab):
    today = datetime.date.today().isoformat()
    if tab == "entries":
        return [
            (
                datetime.datetime.fromisoformat(entry["timestamp"]).strftime("%d/%m %H:%M"),
                entry["value"],
            )
            for entry in data["entries"]
        ]
    if tab == "daily":
        daily = dict(data["daily"])
        avg, _ = today_stats(data)
        if avg is not None:
            daily[today] = avg
        return sorted(daily.items())
    if tab == "weekly":
        return sorted(data["weekly"].items())
    return sorted(data["monthly"].items())


def add_entry(data, value):
    now = datetime.datetime.now().isoformat(timespec="seconds")
    today = datetime.date.today().isoformat()
    data["entries"].append({"timestamp": now, "date": today, "value": int(value)})
    save_data(data)


if not IS_ANDROID:
    import tkinter as tk
    from tkinter import messagebox

    class Slider(tk.Canvas):
        TH = 6
        KR = 9

        def __init__(self, parent, command=None, **kw):
            self._cw = int(kw.pop("width", 240))
            super().__init__(
                parent,
                width=self._cw,
                height=28,
                bg=CARD,
                highlightthickness=0,
                **kw,
            )
            self._val = 0
            self._cmd = command
            self.bind("<ButtonPress-1>", self._press)
            self.bind("<B1-Motion>", self._motion)
            self.bind("<ButtonRelease-1>", lambda e: None)
            self._redraw()

        def get(self):
            return self._val

        def _px(self, v):
            pad = self.KR + 2
            return pad + (v + 10) / 20 * (self._cw - 2 * pad)

        def _val_from(self, x):
            pad = self.KR + 2
            span = self._cw - 2 * pad
            raw = (x - pad) / span * 20 - 10
            return max(-10, min(10, int(round(raw))))

        def _redraw(self):
            self.delete("all")
            pad = self.KR + 2
            ty = 14
            span = self._cw - 2 * pad
            for i in range(int(span)):
                value = -10 + 20 * i / span
                self.create_line(
                    pad + i,
                    ty - self.TH // 2,
                    pad + i,
                    ty + self.TH // 2,
                    fill=mood_color(value),
                )
            self.create_rectangle(
                pad,
                ty - self.TH // 2,
                pad + span,
                ty + self.TH // 2,
                outline=MUTED2,
                fill="",
                width=1,
            )
            knob_x = self._px(self._val)
            col = mood_color(self._val)
            self.create_oval(
                knob_x - self.KR,
                ty - self.KR,
                knob_x + self.KR,
                ty + self.KR,
                fill=CARD,
                outline=col,
                width=2,
            )
            self.create_oval(knob_x - 3, ty - 3, knob_x + 3, ty + 3, fill=col, outline="")

        def _press(self, event):
            self._update(event.x)

        def _motion(self, event):
            self._update(event.x)

        def _update(self, x):
            value = self._val_from(x)
            if value != self._val:
                self._val = value
                self._redraw()
                if self._cmd:
                    self._cmd(value)


    class TimelineWindow(tk.Toplevel):
        TABS = [("Registros", "entries"), ("Diario", "daily"), ("Semanal", "weekly"), ("Mensual", "monthly")]

        def __init__(self, parent, data):
            super().__init__(parent)
            self.title("MoodTracker — Historial")
            self.configure(bg=BG)
            self.geometry("900x580")
            self.minsize(600, 400)
            self.data = data
            self._btns = {}
            self._build()

        def _build(self):
            bar = tk.Frame(self, bg=CARD2)
            bar.pack(fill="x")
            for label, value in self.TABS:
                btn = tk.Button(
                    bar,
                    text=label,
                    command=lambda v=value: self._switch(v),
                    bg=CARD2,
                    fg=MUTED,
                    font=(FN, 9),
                    relief="flat",
                    padx=18,
                    pady=8,
                    cursor="hand2",
                    bd=0,
                    activebackground=CARD,
                    activeforeground=TEXT,
                )
                btn.pack(side="left")
                self._btns[value] = btn
            tk.Frame(self, bg=BORDER, height=1).pack(fill="x")
            self._fr = tk.Frame(self, bg=BG)
            self._fr.pack(fill="both", expand=True)
            self._switch("entries")

        def _switch(self, tab):
            for value, btn in self._btns.items():
                btn.config(bg=CARD if value == tab else CARD2, fg=TEXT if value == tab else MUTED)
            for widget in self._fr.winfo_children():
                widget.destroy()
            self._draw(tab)

        def _draw(self, tab):
            items = history_items(self.data, tab)
            title_map = {
                "entries": "Todos los registros",
                "daily": "Promedio Diario",
                "weekly": "Promedio Semanal",
                "monthly": "Promedio Mensual",
            }
            if not items:
                tk.Label(self._fr, text="Sin datos aún.", bg=BG, fg=MUTED, font=(FN, 11)).pack(expand=True)
                return

            canvas = tk.Canvas(self._fr, bg=BG, highlightthickness=0)
            canvas.pack(fill="both", expand=True)
            self._fr.update_idletasks()
            width = self._fr.winfo_width() or 860
            height = self._fr.winfo_height() or 540
            pl, pr, pt, pb = 52, 16, 44, 64
            plot_width = width - pl - pr
            plot_height = height - pt - pb
            center_y = pt + plot_height // 2
            canvas.create_text(width // 2, 20, text=title_map[tab], fill=TEXT, font=(FN, 10, "bold"))
            canvas.create_line(pl, pt, pl, height - pb, fill=BORDER)
            canvas.create_line(pl, center_y, width - pr, center_y, fill=BORDER, dash=(4, 4))
            for value in range(-10, 11, 5):
                y = center_y - value * (plot_height // 2) // 10
                canvas.create_text(pl - 5, y, text=str(value), fill=MUTED, anchor="e", font=(FN, 7))

            count = len(items)
            bar_width = max(5, min(32, (plot_width - 8) // max(1, count) - 2))
            for i, (label, value) in enumerate(items):
                x = pl + 8 + i * (plot_width - 8) // max(1, count) + bar_width // 2
                y_value = center_y - int(value * (plot_height // 2) / 10)
                col = mood_color(value)
                canvas.create_rectangle(
                    x - bar_width // 2,
                    min(y_value, center_y),
                    x + bar_width // 2,
                    max(y_value, center_y),
                    fill=col,
                    outline="",
                )
                canvas.create_text(
                    x,
                    y_value + (-10 if value >= 0 else 10),
                    text=f"{value:.1f}" if isinstance(value, float) else str(value),
                    fill=TEXT,
                    font=(FN, 7),
                )
                if i % max(1, count // 12) == 0:
                    canvas.create_text(x, height - pb + 12, text=str(label)[:7], fill=MUTED, font=(FN, 7))


    def setup_autostart():
        if IS_WIN:
            import winreg
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                    0,
                    winreg.KEY_SET_VALUE,
                )
                pythonw = sys.executable.replace("python.exe", "pythonw.exe")
                if not os.path.exists(pythonw):
                    pythonw = sys.executable
                winreg.SetValueEx(key, "MoodTracker", 0, winreg.REG_SZ, f'"{pythonw}" "{SCRIPT}"')
                winreg.CloseKey(key)
                messagebox.showinfo(
                    "Inicio Automático",
                    "MoodTracker se iniciará automáticamente cada vez que abras Windows.",
                )
            except Exception as exc:
                messagebox.showerror("Error", f"No se pudo configurar:\n{exc}")
            return

        path = os.path.expanduser("~/.config/autostart/moodtracker.desktop")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(
                "[Desktop Entry]\n"
                "Type=Application\n"
                "Name=MoodTracker\n"
                f"Exec=python3 {SCRIPT}\n"
                "X-GNOME-Autostart-enabled=true\n"
            )
        messagebox.showinfo("Inicio Automático", "MoodTracker se iniciará automáticamente.")


    class MoodWidget:
        def __init__(self):
            self.root = tk.Tk()
            self.root.title("MoodTracker")
            self.root.resizable(False, False)
            self.root.configure(bg=BORDER)
            self.root.attributes("-topmost", True)
            if IS_WIN:
                self.root.attributes("-toolwindow", True)
            self.root.update_idletasks()
            sw = self.root.winfo_screenwidth()
            self.root.geometry(f"+{sw - 296}+14")
            self.data = load_data()
            recalculate(self.data)
            self._after = None
            self._build()
            self._refresh()
            self.root.protocol("WM_DELETE_WINDOW", self._close)

        def _build(self):
            outer = tk.Frame(self.root, bg=BORDER, padx=1, pady=1)
            outer.pack(fill="both", expand=True)
            self._main = tk.Frame(outer, bg=CARD)
            self._main.pack(fill="both", expand=True)
            main = self._main

            header = tk.Frame(main, bg=CARD2, padx=12, pady=5)
            header.pack(fill="x")
            tk.Label(header, text="MOOD", bg=CARD2, fg=ACCENT, font=(FN, 8, "bold")).pack(side="left")
            tk.Label(header, text="TRACKER", bg=CARD2, fg=MUTED, font=(FN, 8)).pack(side="left", padx=(3, 0))
            self._date_lbl = tk.Label(header, bg=CARD2, fg=MUTED, font=(FN, 8))
            self._date_lbl.pack(side="right")
            tk.Frame(main, bg=BORDER, height=1).pack(fill="x")

            middle = tk.Frame(main, bg=CARD, pady=10)
            middle.pack(fill="x")
            row = tk.Frame(middle, bg=CARD)
            row.pack()
            self._emoji_lbl = tk.Label(row, text="😐", bg=CARD, font=("Arial", 20))
            self._emoji_lbl.pack(side="left", padx=(0, 6))
            self._num_lbl = tk.Label(row, text=" 0", bg=CARD, fg=TEXT, font=(FN, 34, "bold"), width=3, anchor="e")
            self._num_lbl.pack(side="left")
            self._desc_lbl = tk.Label(middle, text="Neutral", bg=CARD, fg=MUTED, font=(FN, 8))
            self._desc_lbl.pack(pady=(2, 0))

            slider_frame = tk.Frame(main, bg=CARD, padx=12, pady=4)
            slider_frame.pack(fill="x")
            limits = tk.Frame(slider_frame, bg=CARD)
            limits.pack(fill="x")
            tk.Label(limits, text="−10", bg=CARD, fg="#be1414", font=(FN, 7)).pack(side="left")
            tk.Label(limits, text="+10", bg=CARD, fg="#0f9637", font=(FN, 7)).pack(side="right")
            self._sl = Slider(slider_frame, command=self._slide, width=256)
            self._sl.pack(pady=(2, 0))

            button_frame = tk.Frame(main, bg=CARD, padx=12, pady=8)
            button_frame.pack(fill="x")
            self._rbtn = tk.Button(
                button_frame,
                text="▶  REGISTRAR",
                command=self._reg,
                bg=ACCENT,
                fg="white",
                font=(FN, 9, "bold"),
                relief="flat",
                pady=7,
                cursor="hand2",
                activebackground=ACCT2,
                activeforeground="white",
            )
            self._rbtn.pack(fill="x")

            tk.Frame(main, bg=BORDER, height=1).pack(fill="x")
            stats = tk.Frame(main, bg=CARD, padx=12, pady=8)
            stats.pack(fill="x")
            self._avg_lbl = tk.Label(stats, text="Promedio hoy:  —", bg=CARD, fg=TEXT, font=(FN, 9, "bold"), anchor="w")
            self._avg_lbl.pack(fill="x")
            self._cnt_lbl = tk.Label(stats, text="Sin registros aún", bg=CARD, fg=MUTED, font=(FN, 8), anchor="w")
            self._cnt_lbl.pack(fill="x", pady=(1, 6))
            self._hist_fr = tk.Frame(stats, bg=CARD)
            self._hist_fr.pack(fill="x")

            tk.Frame(main, bg=BORDER, height=1).pack(fill="x")
            bottom = tk.Frame(main, bg=CARD2, padx=8, pady=6)
            bottom.pack(fill="x")
            for text, command in [("📊 Historial", self._timeline), ("⚙ Inicio auto", setup_autostart)]:
                tk.Button(
                    bottom,
                    text=text,
                    command=command,
                    bg=CARD2,
                    fg=MUTED,
                    font=(FN, 8),
                    relief="flat",
                    padx=10,
                    pady=4,
                    cursor="hand2",
                    activebackground=CARD,
                    activeforeground=TEXT,
                ).pack(side="left", padx=2)

        def _slide(self, value=None):
            if value is None:
                value = self._sl.get()
            col = mood_color(value)
            self._num_lbl.config(text=f"{value:+d}" if value != 0 else " 0", fg=col)
            self._emoji_lbl.config(text=mood_emoji(value))
            self._desc_lbl.config(text=DESCS[value + 10], fg=col)

        def _reg(self):
            value = self._sl.get()
            add_entry(self.data, value)
            self._refresh()
            col = mood_color(value)
            self._rbtn.config(bg=col, text="  ✓  GUARDADO  ")
            if self._after:
                self.root.after_cancel(self._after)
            self._after = self.root.after(1100, lambda: self._rbtn.config(bg=ACCENT, text="▶  REGISTRAR"))

        def _refresh(self):
            today = datetime.date.today().isoformat()
            self._date_lbl.config(text=today)
            avg, count = today_stats(self.data)
            if avg is None:
                self._avg_lbl.config(text="Promedio hoy:  —", fg=TEXT)
                self._cnt_lbl.config(text="Sin registros aún")
            else:
                self._avg_lbl.config(text=f"Promedio hoy:  {avg:+.1f}", fg=mood_color(avg))
                self._cnt_lbl.config(text=f"{count} registro{'s' if count > 1 else ''} hoy")

            for widget in self._hist_fr.winfo_children():
                widget.destroy()
            entries = [entry for entry in self.data["entries"] if entry["date"] == today][-5:]
            if not entries:
                return
            tk.Label(self._hist_fr, text="Últimos:", bg=CARD, fg=MUTED2, font=(FN, 7)).pack(anchor="w")
            row = tk.Frame(self._hist_fr, bg=CARD)
            row.pack(anchor="w", pady=(2, 0))
            for entry in entries:
                pill = tk.Frame(row, bg=CARD2, padx=5, pady=2)
                pill.pack(side="left", padx=(0, 4))
                tk.Label(pill, text=f"{entry['value']:+d}", bg=CARD2, fg=mood_color(entry["value"]), font=(FN, 8, "bold")).pack()
                tk.Label(
                    pill,
                    text=datetime.datetime.fromisoformat(entry["timestamp"]).strftime("%H:%M"),
                    bg=CARD2,
                    fg=MUTED,
                    font=(FN, 7),
                ).pack()

        def _timeline(self):
            recalculate(self.data)
            TimelineWindow(self.root, self.data)

        def _close(self):
            recalculate(self.data)
            self.root.destroy()

        def run(self):
            self._slide(0)
            self.root.mainloop()


def run_desktop():
    if IS_ANDROID:
        raise RuntimeError("run_desktop() no está disponible en Android.")
    if IS_LINUX and "--detached" not in sys.argv:
        try:
            if sys.stdin and os.isatty(sys.stdin.fileno()):
                import subprocess
                subprocess.Popen(
                    [sys.executable, SCRIPT, "--detached"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    start_new_session=True,
                )
                print("MoodTracker iniciado ✓")
                return
        except Exception:
            pass
    MoodWidget().run()


if IS_ANDROID:
    from kivy.app import App
    from kivy.core.window import Window
    from kivy.graphics import Color, Line, RoundedRectangle
    from kivy.metrics import dp, sp
    from kivy.properties import NumericProperty, StringProperty
    from kivy.uix.behaviors import ButtonBehavior
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.button import Button
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.label import Label
    from kivy.uix.modalview import ModalView
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.slider import Slider as KivySlider
    from kivy.uix.widget import Widget

    Window.clearcolor = hex_rgba(BORDER)

    class Card(BoxLayout):
        def __init__(self, bg_color=CARD, radius=20, **kwargs):
            super().__init__(**kwargs)
            self.orientation = kwargs.get("orientation", "vertical")
            self.padding = kwargs.get("padding", dp(14))
            self.spacing = kwargs.get("spacing", dp(10))
            self._radius = dp(radius)
            with self.canvas.before:
                self._color = Color(*hex_rgba(bg_color))
                self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[self._radius] * 4)
            self.bind(pos=self._sync_rect, size=self._sync_rect)

        def _sync_rect(self, *_):
            self._rect.pos = self.pos
            self._rect.size = self.size

        def set_background(self, value):
            self._color.rgba = hex_rgba(value)


    class Pill(Card):
        def __init__(self, **kwargs):
            super().__init__(bg_color=CARD2, radius=14, size_hint_y=None, height=dp(64), **kwargs)


    class ThinDivider(Widget):
        def __init__(self, **kwargs):
            super().__init__(size_hint_y=None, height=dp(1), **kwargs)
            with self.canvas:
                Color(*hex_rgba(BORDER))
                self._line = Line(points=[0, 0, 0, 0], width=1.0)
            self.bind(pos=self._sync, size=self._sync)

        def _sync(self, *_):
            y = self.y + self.height / 2
            self._line.points = [self.x, y, self.right, y]


    class TouchButton(ButtonBehavior, Card):
        def __init__(self, text="", bg_color=ACCENT, fg=(1, 1, 1, 1), **kwargs):
            super().__init__(bg_color=bg_color, radius=18, size_hint_y=None, height=dp(54), **kwargs)
            self.label = Label(text=text, color=fg, font_size=sp(16), bold=True)
            self.add_widget(self.label)

        def set_background(self, value):
            super().set_background(value)


    class HistoryBar(Card):
        def __init__(self, label_text, value, **kwargs):
            super().__init__(bg_color=CARD2, radius=18, size_hint_y=None, height=dp(92), padding=dp(12), **kwargs)
            self.orientation = "vertical"
            self.spacing = dp(8)
            top = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(22))
            top.add_widget(Label(text=label_text, color=hex_rgba(MUTED), halign="left", valign="middle", font_size=sp(12)))
            top.add_widget(Label(text=f"{value:+.1f}" if isinstance(value, float) else f"{value:+d}", color=mood_color_rgba(value), bold=True, halign="right", valign="middle", font_size=sp(15)))
            self.add_widget(top)

            canvas_holder = Widget(size_hint_y=None, height=dp(30))
            self.add_widget(canvas_holder)

            baseline = dp(12)
            full = dp(116)
            center = full / 2
            px = max(-10.0, min(10.0, float(value))) / 10.0
            width = abs(px) * center
            start_x = center if px >= 0 else center - width
            with canvas_holder.canvas:
                Color(*hex_rgba(BORDER))
                Line(points=[0, baseline + dp(8), full, baseline + dp(8)], width=1.0)
                Color(*mood_color_rgba(value))
                RoundedRectangle(pos=(start_x, baseline), size=(max(width, dp(3)), dp(16)), radius=[dp(8)] * 4)


    class TimelineModal(ModalView):
        TABS = [
            ("Registros", "entries"),
            ("Diario", "daily"),
            ("Semanal", "weekly"),
            ("Mensual", "monthly"),
        ]

        def __init__(self, data, **kwargs):
            super().__init__(**kwargs)
            self.size_hint = (0.96, 0.96)
            self.background_color = (0, 0, 0, 0.45)
            self.data = data
            self.current_tab = "entries"
            root = Card(bg_color=BG, radius=24, padding=dp(0), spacing=dp(0))
            root.orientation = "vertical"
            self.add_widget(root)

            header = Card(bg_color=CARD2, radius=24, size_hint_y=None, height=dp(66), padding=(dp(14), dp(10)), spacing=dp(10))
            header.orientation = "horizontal"
            title = Label(text="Historial", color=hex_rgba(TEXT), bold=True, font_size=sp(18))
            close_btn = Button(text="Cerrar", size_hint=(None, None), size=(dp(92), dp(38)), background_normal="", background_color=hex_rgba(CARD), color=hex_rgba(TEXT))
            close_btn.bind(on_release=lambda *_: self.dismiss())
            header.add_widget(title)
            header.add_widget(close_btn)
            root.add_widget(header)
            root.add_widget(ThinDivider())

            self.tabs = GridLayout(cols=2, size_hint_y=None, spacing=dp(8), padding=dp(12))
            self.tabs.bind(minimum_height=self.tabs.setter("height"))
            root.add_widget(self.tabs)
            self._tab_buttons = {}
            for label, value in self.TABS:
                btn = Button(
                    text=label,
                    size_hint_y=None,
                    height=dp(42),
                    background_normal="",
                    background_color=hex_rgba(CARD2),
                    color=hex_rgba(MUTED),
                )
                btn.bind(on_release=lambda *_evt, tab=value: self.switch(tab))
                self._tab_buttons[value] = btn
                self.tabs.add_widget(btn)

            root.add_widget(ThinDivider())
            scroll = ScrollView(bar_width=dp(6), scroll_type=["bars", "content"])
            self.body = GridLayout(cols=1, spacing=dp(10), padding=dp(14), size_hint_y=None)
            self.body.bind(minimum_height=self.body.setter("height"))
            scroll.add_widget(self.body)
            root.add_widget(scroll)
            self.switch(self.current_tab)

        def switch(self, tab):
            self.current_tab = tab
            for value, btn in self._tab_buttons.items():
                active = value == tab
                btn.background_color = hex_rgba(CARD if active else CARD2)
                btn.color = hex_rgba(TEXT if active else MUTED)
            self.body.clear_widgets()
            items = history_items(self.data, tab)
            if not items:
                empty = Label(
                    text="Sin datos aún.",
                    color=hex_rgba(MUTED),
                    size_hint_y=None,
                    height=dp(120),
                    font_size=sp(16),
                )
                self.body.add_widget(empty)
                return
            for label, value in items[::-1]:
                self.body.add_widget(HistoryBar(str(label), value))


    class MoodTrackerAndroidApp(App):
        mood_value = NumericProperty(0)
        mood_text = StringProperty("Neutral")
        mood_emoji_value = StringProperty("😐")

        def build(self):
            self.title = "MoodTracker"
            self.data = load_data()
            recalculate(self.data)

            root = Card(bg_color=BG, radius=0, padding=(dp(14), dp(18)), spacing=dp(12))
            scroll = ScrollView(bar_width=dp(6), scroll_type=["bars", "content"])
            content = GridLayout(cols=1, spacing=dp(12), size_hint_y=None)
            content.bind(minimum_height=content.setter("height"))
            scroll.add_widget(content)
            root.add_widget(scroll)

            header = Card(bg_color=CARD2, radius=22, size_hint_y=None, height=dp(62), orientation="horizontal", padding=(dp(14), dp(12)))
            brand = BoxLayout(orientation="horizontal")
            brand.add_widget(Label(text="[b]MOOD[/b]", markup=True, color=hex_rgba(ACCENT), font_size=sp(14)))
            brand.add_widget(Label(text="TRACKER", color=hex_rgba(MUTED), font_size=sp(14)))
            self.date_label = Label(text=datetime.date.today().isoformat(), color=hex_rgba(MUTED), font_size=sp(13))
            header.add_widget(brand)
            header.add_widget(self.date_label)
            content.add_widget(header)

            hero = Card(bg_color=CARD, radius=24, size_hint_y=None, height=dp(190), padding=(dp(16), dp(18)))
            row = BoxLayout(orientation="horizontal")
            self.emoji_label = Label(text=self.mood_emoji_value, font_size=sp(32))
            self.value_label = Label(text="0", color=hex_rgba(TEXT), font_size=sp(52), bold=True)
            row.add_widget(self.emoji_label)
            row.add_widget(self.value_label)
            hero.add_widget(row)
            self.desc_label = Label(text=self.mood_text, color=hex_rgba(MUTED), font_size=sp(16), size_hint_y=None, height=dp(28))
            hero.add_widget(self.desc_label)
            limits = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(18))
            limits.add_widget(Label(text="-10", color=hex_rgba("#be1414"), font_size=sp(12)))
            limits.add_widget(Label(text="+10", color=hex_rgba("#0f9637"), font_size=sp(12), halign="right"))
            hero.add_widget(limits)
            self.slider = KivySlider(min=-10, max=10, value=0, step=1, size_hint_y=None, height=dp(40), cursor_size=(dp(22), dp(22)))
            self.slider.bind(value=self.on_slider)
            hero.add_widget(self.slider)
            content.add_widget(hero)

            self.register_button = TouchButton(text="REGISTRAR", bg_color=ACCENT)
            self.register_button.bind(on_release=self.register_value)
            content.add_widget(self.register_button)

            stats = Card(bg_color=CARD, radius=24, size_hint_y=None, height=dp(340), padding=(dp(16), dp(16)))
            self.avg_label = Label(text="Promedio hoy:  —", color=hex_rgba(TEXT), bold=True, font_size=sp(16), size_hint_y=None, height=dp(26))
            self.count_label = Label(text="Sin registros aún", color=hex_rgba(MUTED), font_size=sp(14), size_hint_y=None, height=dp(24))
            self.last_entries = GridLayout(cols=1, spacing=dp(8), size_hint_y=None)
            self.last_entries.bind(minimum_height=self.last_entries.setter("height"))
            stats.add_widget(self.avg_label)
            stats.add_widget(self.count_label)
            stats.add_widget(ThinDivider())
            stats.add_widget(self.last_entries)
            content.add_widget(stats)

            actions = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(54))
            history_btn = Button(text="Historial", background_normal="", background_color=hex_rgba(CARD2), color=hex_rgba(TEXT))
            auto_btn = Button(text="Inicio auto", background_normal="", background_color=hex_rgba(CARD2), color=hex_rgba(TEXT))
            history_btn.bind(on_release=lambda *_: self.open_history())
            auto_btn.bind(on_release=lambda *_: self.show_autostart_info())
            actions.add_widget(history_btn)
            actions.add_widget(auto_btn)
            content.add_widget(actions)

            self.on_slider(self.slider, 0)
            self.refresh()
            return root

        def on_slider(self, _slider, value):
            current = int(value)
            self.mood_value = current
            col = mood_color_rgba(current)
            self.value_label.text = f"{current:+d}" if current else "0"
            self.value_label.color = col
            self.emoji_label.text = mood_emoji(current)
            self.desc_label.text = DESCS[current + 10]
            self.desc_label.color = col

        def register_value(self, *_):
            add_entry(self.data, self.mood_value)
            self.refresh()
            self.register_button.label.text = "GUARDADO"
            self.register_button.set_background(mood_color(self.mood_value))
            self.register_button.label.color = (1, 1, 1, 1)
            self.cancel_btn_reset()
            self._reset_event = self.clock_schedule()

        def clock_schedule(self):
            from kivy.clock import Clock
            return Clock.schedule_once(self.reset_button, 1.1)

        def cancel_btn_reset(self):
            if hasattr(self, "_reset_event") and self._reset_event is not None:
                self._reset_event.cancel()

        def reset_button(self, *_):
            self.register_button.label.text = "REGISTRAR"
            self.register_button.set_background(ACCENT)
            self._reset_event = None

        def refresh(self):
            self.date_label.text = datetime.date.today().isoformat()
            avg, count = today_stats(self.data)
            if avg is None:
                self.avg_label.text = "Promedio hoy:  —"
                self.avg_label.color = hex_rgba(TEXT)
                self.count_label.text = "Sin registros aún"
            else:
                self.avg_label.text = f"Promedio hoy:  {avg:+.1f}"
                self.avg_label.color = mood_color_rgba(avg)
                self.count_label.text = f"{count} registro{'s' if count > 1 else ''} hoy"

            self.last_entries.clear_widgets()
            entries = [entry for entry in self.data["entries"] if entry["date"] == datetime.date.today().isoformat()][-5:]
            if not entries:
                self.last_entries.add_widget(Label(text="", size_hint_y=None, height=dp(0)))
                return
            self.last_entries.add_widget(Label(text="Últimos:", color=hex_rgba(MUTED2), font_size=sp(13), size_hint_y=None, height=dp(24), halign="left"))
            pills = GridLayout(cols=1, spacing=dp(8), size_hint_y=None)
            pills.bind(minimum_height=pills.setter("height"))
            for entry in reversed(entries):
                pill = Pill(orientation="horizontal", height=dp(58))
                pill.add_widget(Label(text=f"{entry['value']:+d}", color=mood_color_rgba(entry["value"]), bold=True, font_size=sp(18)))
                pill.add_widget(Label(
                    text=datetime.datetime.fromisoformat(entry["timestamp"]).strftime("%H:%M"),
                    color=hex_rgba(MUTED),
                    font_size=sp(14),
                ))
                pills.add_widget(pill)
            self.last_entries.add_widget(pills)

        def open_history(self):
            recalculate(self.data)
            TimelineModal(self.data).open()

        def show_autostart_info(self):
            modal = ModalView(size_hint=(0.88, None), height=dp(180), background_color=(0, 0, 0, 0.45))
            card = Card(bg_color=CARD, radius=22)
            card.add_widget(Label(
                text="Android no permite un 'inicio automático' equivalente al de escritorio desde esta app empaquetada.",
                color=hex_rgba(TEXT),
                font_size=sp(15),
            ))
            close_btn = Button(text="Entendido", size_hint_y=None, height=dp(44), background_normal="", background_color=hex_rgba(ACCENT), color=(1, 1, 1, 1))
            close_btn.bind(on_release=lambda *_: modal.dismiss())
            card.add_widget(close_btn)
            modal.add_widget(card)
            modal.open()

        def on_stop(self):
            recalculate(self.data)


def run_android():
    if not IS_ANDROID:
        raise RuntimeError("run_android() solo está disponible en Android.")
    MoodTrackerAndroidApp().run()


def main():
    if IS_ANDROID:
        run_android()
    else:
        run_desktop()


if __name__ == "__main__":
    main()
