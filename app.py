"""ProcessLens: a native CustomTkinter process resource monitor."""

from __future__ import annotations

import time
import tkinter as tk
from datetime import datetime

import customtkinter as ctk
import psutil


ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

BG = ("#F3F4F6", "#111318")
SURFACE = ("#FFFFFF", "#1B1D23")
INK = ("#202124", "#E7E9ED")
MUTED = ("#6B7280", "#A0A5AE")
LINE = ("#E5E7EB", "#30333A")
BLUE = ("#2563EB", "#7AA2F7")
GREEN = ("#138A62", "#5DCAA1")
SELECTED = ("#E8F0FE", "#252B38")
HOVER = ("#EEF1F5", "#292D35")
SUBTLE = ("#F3F4F6", "#25272E")
SUBTLE_HOVER = ("#E8EAED", "#30333A")


class ProcessLens(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ProcessLens")
        self.geometry("1260x850")
        self.minsize(1000, 700)
        self.configure(fg_color=BG)

        self.processes: list[dict] = []
        self.samples: list[dict] = []
        self.spikes: list[str] = []
        self.selected_pid: int | None = None
        self.selected_name = ""
        self.process: psutil.Process | None = None
        self.monitoring = False
        self.started_at = 0.0
        self.after_id = None
        self.search_job = None
        self.dark_mode = False
        self.report_ready = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_header()
        self._build_body()
        self.refresh_processes()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0, height=68,
                              border_width=1, border_color=LINE)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="ProcessLens", text_color=INK,
                     font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, padx=24, pady=17, sticky="w")
        self.theme_switch = ctk.CTkSwitch(header, text="Dark mode", width=76,
                                          command=self.toggle_theme,
                                          font=ctk.CTkFont(size=12))
        self.theme_switch.grid(row=0, column=1, padx=14, sticky="e")
        self.status_label = ctk.CTkLabel(header, text="Ready", text_color=MUTED,
                                         font=ctk.CTkFont(size=12))
        self.status_label.grid(row=0, column=2, padx=24, sticky="e")

    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, padx=22, pady=20, sticky="nsew")
        body.grid_columnconfigure(0, weight=0, minsize=292)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self._build_process_panel(body)
        self._build_dashboard(body)

    def _build_process_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=10,
                             border_width=1, border_color=LINE)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(panel, text="Processes", text_color=INK,
                     font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, padx=16, pady=(17, 10), sticky="w")
        self.search = ctk.CTkEntry(panel, placeholder_text="Search name or PID…",
                                   height=36, corner_radius=7, border_color=LINE,
                                   fg_color=SURFACE, text_color=INK)
        self.search.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")
        self.search.bind("<KeyRelease>", self.on_search)

        self.proc_count = ctk.CTkLabel(panel, text="", text_color=MUTED,
                                       font=ctk.CTkFont(size=11))
        self.proc_count.grid(row=2, column=0, padx=16, pady=(0, 6), sticky="w")
        self.proc_list = ctk.CTkScrollableFrame(panel, fg_color="transparent",
                                               corner_radius=0)
        self.proc_list.grid(row=3, column=0, padx=6, pady=(0, 8), sticky="nsew")

        ctk.CTkButton(panel, text="Refresh process list", height=34,
                      fg_color=SUBTLE, hover_color=SUBTLE_HOVER, text_color=INK,
                      corner_radius=7, command=self.refresh_processes).grid(
            row=4, column=0, padx=12, pady=(4, 12), sticky="ew")

    def _build_dashboard(self, parent):
        area = ctk.CTkFrame(parent, fg_color="transparent")
        area.grid(row=0, column=1, sticky="nsew")
        area.grid_columnconfigure(0, weight=1)
        area.grid_rowconfigure(0, weight=1)
        self.dashboard_area = area
        overview = ctk.CTkFrame(area, fg_color="transparent")
        overview.grid(row=0, column=0, sticky="nsew")
        self.overview = overview
        overview.grid_columnconfigure(0, weight=1)
        overview.grid_rowconfigure(3, weight=1)

        top = ctk.CTkFrame(overview, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        top.grid_columnconfigure(0, weight=1)
        self.title_label = ctk.CTkLabel(top, text="Select a process", text_color=INK,
                                        font=ctk.CTkFont(size=23, weight="bold"))
        self.title_label.grid(row=0, column=0, sticky="w")
        self.report_button = ctk.CTkButton(top, text="Detailed report", width=125, height=34,
                                           corner_radius=7, command=self.open_report)
        self.report_button.grid(row=0, column=1, padx=(8, 0))
        self.report_button.grid_remove()
        self.pid_input = ctk.CTkEntry(top, width=112, height=34,
                                      placeholder_text="PID", corner_radius=7,
                                      border_color=LINE, fg_color=SURFACE, text_color=INK)
        self.pid_input.grid(row=0, column=2, padx=(8, 6))
        self.pid_input.bind("<Return>", lambda _event: self.select_pid())
        ctk.CTkButton(top, text="Open PID", width=84, height=34,
                      corner_radius=7, command=self.select_pid).grid(row=0, column=3)

        self.identity = ctk.CTkLabel(overview, text="Choose a process from the list or enter its PID.",
                                     text_color=MUTED, font=ctk.CTkFont(size=12), anchor="w")
        self.identity.grid(row=1, column=0, sticky="ew", pady=(0, 14))

        cards = ctk.CTkFrame(overview, fg_color="transparent")
        cards.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        cards.grid_columnconfigure(0, weight=1)
        cards.grid_columnconfigure(1, weight=2)
        cards.grid_columnconfigure(2, weight=1)
        self.cpu_card = self._metric_card(cards, 0, "CPU", "—", "%")
        self.mem_card = self._metric_card(cards, 1, "Resident memory", "—", "MB")
        self.thread_card = self._metric_card(cards, 2, "Threads", "—", "")

        lower = ctk.CTkFrame(overview, fg_color="transparent")
        lower.grid(row=3, column=0, sticky="nsew")
        lower.grid_columnconfigure(0, weight=1)
        lower.grid_rowconfigure(0, weight=1)
        lower.grid_rowconfigure(1, weight=1)

        chart_panel = ctk.CTkFrame(lower, fg_color=SURFACE, corner_radius=10,
                                   border_width=1, border_color=LINE)
        chart_panel.grid(row=0, column=0, sticky="nsew", pady=(0, 14))
        chart_panel.grid_columnconfigure(0, weight=1)
        chart_panel.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(chart_panel, text="Usage over time", text_color=INK,
                     font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, padx=16, pady=(13, 4), sticky="w")
        self.chart = tk.Canvas(chart_panel, height=270, bg=self._color(SURFACE), highlightthickness=0)
        self.chart.grid(row=1, column=0, padx=10, pady=(0, 8), sticky="nsew")
        self.chart.bind("<Configure>", lambda _e: self.draw_chart())

        info_panel = ctk.CTkFrame(lower, fg_color=SURFACE, corner_radius=10,
                                  border_width=1, border_color=LINE)
        info_panel.grid(row=1, column=0, sticky="nsew")
        info_panel.grid_columnconfigure(0, weight=1)
        info_panel.grid_rowconfigure(1, weight=1)
        info_head = ctk.CTkFrame(info_panel, fg_color="transparent")
        info_head.grid(row=0, column=0, padx=16, pady=(11, 2), sticky="ew")
        info_head.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(info_head, text="Process details", text_color=INK,
                     font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky="w")
        self.track_button = ctk.CTkButton(info_head, text="Start monitoring", width=135,
                                          height=31, corner_radius=7, state="disabled",
                                          command=self.toggle_monitoring)
        self.track_button.grid(row=0, column=1, sticky="e")
        self.details = ctk.CTkTextbox(info_panel, height=230, fg_color="transparent",
                                      text_color=INK, border_width=0, wrap="word",
                                      font=ctk.CTkFont(size=12))
        self.details.grid(row=1, column=0, padx=14, pady=(2, 10), sticky="nsew")
        self._set_details("Process information will appear here.")
        self.finish_button = ctk.CTkButton(info_head, text="Finish session", width=112,
                                           height=31, corner_radius=7, state="disabled",
                                           fg_color=SUBTLE, hover_color=SUBTLE_HOVER,
                                           text_color=INK, command=self.finish_session)
        self.finish_button.grid(row=0, column=2, padx=(8, 0), sticky="e")

    def _metric_card(self, parent, col, title, value, unit):
        card = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=9,
                            border_width=1, border_color=LINE)
        card.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 7, 7 if col < 2 else 0))
        ctk.CTkLabel(card, text=title, text_color=MUTED,
                     font=ctk.CTkFont(size=11)).grid(row=0, column=0, padx=14, pady=(12, 0), sticky="w")
        value_label = ctk.CTkLabel(card, text=f"{value} {unit}".strip(), text_color=INK,
                                   font=ctk.CTkFont(size=25 if col == 1 else 23, weight="bold"))
        value_label.grid(row=1, column=0, padx=14, pady=(2, 12), sticky="w")
        return value_label

    def refresh_processes(self):
        self.processes = []
        for proc in psutil.process_iter(["pid", "name", "username"]):
            try:
                info = proc.info
                self.processes.append({"pid": info["pid"], "name": info.get("name") or "Unknown",
                                       "username": info.get("username") or ""})
            except (psutil.Error, OSError):
                continue
        self.processes.sort(key=lambda item: item["name"].casefold())
        self.render_processes()
        self.status_label.configure(text=f"{len(self.processes)} processes")

    def on_search(self, _event=None):
        if self.search_job:
            self.after_cancel(self.search_job)
        self.search_job = self.after(140, self.render_processes)

    def render_processes(self):
        query = self.search.get().strip().casefold()
        matches = [p for p in self.processes if query in p["name"].casefold() or query in str(p["pid"])]
        self.proc_count.configure(text=f"{len(matches)} processes" + (" · showing first 300" if len(matches) > 300 else ""))
        for child in self.proc_list.winfo_children():
            child.destroy()
        for item in matches[:300]:
            active = item["pid"] == self.selected_pid
            label = f"{item['name']}\nPID {item['pid']}"
            button = ctk.CTkButton(
                self.proc_list, text=label, anchor="w", height=48, corner_radius=7,
                fg_color=SELECTED if active else "transparent",
                hover_color=HOVER, text_color=BLUE if active else INK,
                font=ctk.CTkFont(size=12, weight="bold" if active else "normal"),
                command=lambda p=item["pid"], n=item["name"]: self.select_process(p, n),
            )
            button.pack(fill="x", padx=2, pady=2)

    def select_pid(self):
        raw = self.pid_input.get().strip()
        if not raw.isdigit() or int(raw) < 1:
            self.status_label.configure(text="Enter a valid PID")
            return
        try:
            proc = psutil.Process(int(raw))
            self.select_process(proc.pid, proc.name())
        except psutil.NoSuchProcess:
            self.status_label.configure(text=f"PID {raw} is not running")
        except psutil.AccessDenied:
            self.status_label.configure(text="Access denied for this process")

    def select_process(self, pid: int, name: str):
        self.stop_monitoring()
        if self.report_ready:
            if hasattr(self, "report_page"):
                self.report_page.destroy()
            self.overview.grid()
            self.report_button.grid_remove()
            self.report_ready = False
        try:
            self.process = psutil.Process(pid)
            self.process.cpu_percent(None)
            self.process.memory_info()
        except (psutil.Error, OSError) as exc:
            self.status_label.configure(text=f"Cannot inspect process: {exc}")
            return
        self.selected_pid, self.selected_name = pid, name
        self.samples.clear()
        self.spikes.clear()
        self.title_label.configure(text=name)
        self.identity.configure(text=f"PID {pid}   ·   {self._safe(self.process.username) or 'Unknown user'}")
        self.pid_input.delete(0, "end")
        self.pid_input.insert(0, str(pid))
        self.track_button.configure(state="normal", text="Start monitoring")
        self.finish_button.configure(state="disabled")
        self.status_label.configure(text="Selected process")
        self._set_details("Press Start monitoring to capture live usage and process details.")
        self.render_processes()
        self.draw_chart()

    def toggle_monitoring(self):
        if self.monitoring:
            self.stop_monitoring()
            self.track_button.configure(text="Resume monitoring")
            self.finish_button.configure(state="normal")
            self.status_label.configure(text="Monitoring paused")
            return
        if self.process is None:
            return
        self.monitoring = True
        self.started_at = time.monotonic() - (self.samples[-1]["elapsed"] if self.samples else 0)
        self.track_button.configure(text="Pause monitoring")
        self.finish_button.configure(state="normal")
        self.sample_process()

    def finish_session(self):
        if not self.samples:
            self.status_label.configure(text="No samples to report yet")
            return
        self.stop_monitoring()
        self.track_button.configure(text="Start monitoring")
        self.track_button.configure(state="normal")
        self.finish_button.configure(state="disabled")
        self.status_label.configure(text=f"Session finished · {len(self.samples)} samples")
        self._show_report()

    def _show_report(self):
        if not self.report_ready:
            self.report_page = ctk.CTkFrame(self.dashboard_area, fg_color="transparent")
            self.report_page.grid(row=0, column=0, sticky="nsew")
            self.report_page.grid_columnconfigure(0, weight=1)
            self.report_page.grid_rowconfigure(1, weight=1)
            report_head = ctk.CTkFrame(self.report_page, fg_color="transparent")
            report_head.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 12))
            report_head.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(report_head, text="Session report", text_color=INK,
                         font=ctk.CTkFont(size=20, weight="bold")).grid(
                row=0, column=0, sticky="w")
            ctk.CTkButton(report_head, text="Back to process", width=132, height=34,
                          corner_radius=7, command=self.show_overview).grid(row=0, column=1, sticky="e")
            self.report_text = ctk.CTkTextbox(self.report_page, fg_color=SURFACE, text_color=INK,
                                              border_width=1, border_color=LINE, corner_radius=9,
                                              wrap="word", font=ctk.CTkFont(size=13))
            self.report_text.grid(row=1, column=0, padx=8, pady=(0, 10), sticky="nsew")
            self.report_ready = True
        if not self.samples:
            report = "No samples were captured."
        else:
            cpus = [s["cpu"] for s in self.samples]
            memories = [s["rss"] for s in self.samples]
            peak_cpu = max(self.samples, key=lambda sample: sample["cpu"])
            peak_mem = max(self.samples, key=lambda sample: sample["rss"])
            duration = self.samples[-1]["elapsed"]
            report = (
                f"Process: {self.selected_name} (PID {self.selected_pid})\n"
                f"Session started: {self.samples[0]['time']:%Y-%m-%d %H:%M:%S}\n"
                f"Duration: {duration:.0f} seconds · Samples: {len(self.samples)}\n\n"
                f"CPU usage\n"
                f"  Average: {sum(cpus) / len(cpus):.1f}%\n"
                f"  Peak: {peak_cpu['cpu']:.1f}% at {peak_cpu['time']:%H:%M:%S} ({peak_cpu['elapsed']:.0f}s)\n\n"
                f"Resident memory\n"
                f"  Average: {sum(memories) / len(memories):.1f} MB\n"
                f"  Peak: {peak_mem['rss']:.1f} MB at {peak_mem['time']:%H:%M:%S} ({peak_mem['elapsed']:.0f}s)\n\n"
                f"Spikes ({len(self.spikes)})\n"
                + ("\n".join(f"  {spike}" for spike in self.spikes) if self.spikes else "  No spikes detected.")
            )
        self.report_text.configure(state="normal")
        self.report_text.delete("1.0", "end")
        self.report_text.insert("1.0", report)
        self.report_text.configure(state="disabled")
        self.overview.grid_remove()
        self.report_page.grid()
        self.report_button.grid()

    def open_report(self):
        if self.report_ready:
            self.overview.grid_remove()
            self.report_page.grid()

    def show_overview(self):
        if self.report_ready:
            self.report_page.grid_remove()
            self.overview.grid()

    def sample_process(self):
        if not self.monitoring or self.process is None:
            return
        try:
            proc = self.process
            with proc.oneshot():
                memory = proc.memory_info()
                cpu = proc.cpu_percent(None)
                data = {
                    "pid": proc.pid, "name": proc.name(), "username": self._safe(proc.username),
                    "status": proc.status(), "cpu": cpu, "rss": memory.rss / 1048576,
                    "vms": memory.vms / 1048576, "memory_percent": proc.memory_percent(),
                    "threads": proc.num_threads(), "created": proc.create_time(),
                    "cpu_times": proc.cpu_times(), "exe": self._safe(proc.exe),
                    "cwd": self._safe(proc.cwd), "cmdline": self._safe(lambda: " ".join(proc.cmdline())),
                    "parent": proc.ppid(), "files": self._safe(lambda: len(proc.open_files())),
                    "connections": self._safe(lambda: len(proc.net_connections())),
                    "ctx": self._safe(lambda: sum(proc.num_ctx_switches())),
                }
            sample = {"elapsed": time.monotonic() - self.started_at, "time": datetime.now(),
                      "cpu": cpu, "rss": data["rss"]}
            if self.samples:
                old = self.samples[-1]
                if cpu >= 80:
                    self.spikes.insert(0, f"{sample['time']:%H:%M:%S}  CPU spike  {cpu:.1f}%")
                if old["rss"] > 0 and data["rss"] >= old["rss"] * 1.2:
                    self.spikes.insert(0, f"{sample['time']:%H:%M:%S}  Memory jump  {data['rss']:.1f} MB")
            self.samples.append(sample)
            self.samples = self.samples[-300:]
            self.spikes = self.spikes[:20]
            self.cpu_card.configure(text=f"{cpu:.1f} %")
            self.mem_card.configure(text=f"{data['rss']:.1f} MB")
            self.thread_card.configure(text=str(data["threads"]))
            self.status_label.configure(text=f"Monitoring · {sample['elapsed']:.0f}s · {len(self.samples)} samples")
            self.show_details(data)
            self.draw_chart()
        except (psutil.Error, OSError) as exc:
            self.stop_monitoring()
            self.track_button.configure(text="Start monitoring")
            self.status_label.configure(text=f"Process exited or inaccessible: {exc}")
            return
        self.after_id = self.after(1000, self.sample_process)

    def stop_monitoring(self):
        self.monitoring = False
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
        if hasattr(self, "finish_button") and self.samples:
            self.finish_button.configure(state="normal")

    def show_details(self, data):
        started = datetime.fromtimestamp(data["created"]).strftime("%Y-%m-%d %H:%M:%S")
        cpu_times = data["cpu_times"]
        rows = [
            f"Status: {data['status']}     User: {data['username'] or 'Unavailable'}",
            f"Memory: {data['rss']:.1f} MB resident · {data['vms']:.1f} MB virtual · {data['memory_percent']:.2f}% of system",
            f"CPU time: {cpu_times.user:.1f}s user · {cpu_times.system:.1f}s system     Threads: {data['threads']}",
            f"Started: {started}     Parent PID: {data['parent']}",
            f"Open files: {self._display(data['files'])}     Network connections: {self._display(data['connections'])}     Context switches: {self._display(data['ctx'])}",
            f"Executable: {data['exe'] or 'Unavailable'}",
            f"Working directory: {data['cwd'] or 'Unavailable'}",
            f"Command: {data['cmdline'] or 'Unavailable'}",
        ]
        if self.spikes:
            rows.extend(["", "Recent spikes:", *self.spikes[:4]])
        self._set_details("\n".join(rows))

    def _set_details(self, text):
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("1.0", text)
        self.details.configure(state="disabled")

    def draw_chart(self):
        if not hasattr(self, "chart"):
            return
        canvas = self.chart
        canvas.delete("all")
        width = max(canvas.winfo_width(), 400)
        height = max(canvas.winfo_height(), 230)
        left, right, top, bottom = 53, 16, 23, 20
        gap = 24
        plot_unit = (height - top - bottom - gap) / 3
        plot_heights = (plot_unit, plot_unit * 2)
        plot_w = width - left - right
        offset = 0
        for index, (key, label, color, minimum) in enumerate((
            ("cpu", "CPU  (%)", BLUE, 100.0), ("rss", "Memory  (MB)", GREEN, 0.0)
        )):
            plot_h = plot_heights[index]
            y0 = top + offset
            offset += plot_h + gap
            values = [float(s[key]) for s in self.samples]
            maximum = max(minimum, max(values, default=0) * 1.12, 1.0)
            canvas.create_text(left, y0 - 7, text=label, fill=self._color(MUTED), anchor="w",
                               font=("Segoe UI", 9, "bold"))
            for tick in range(3):
                y = y0 + plot_h * tick / 2
                canvas.create_line(left, y, width - right, y, fill=self._color(LINE))
                canvas.create_text(left - 7, y, text=f"{maximum * (1 - tick / 2):.0f}",
                                   fill=self._color(MUTED), anchor="e", font=("Segoe UI", 8))
            if values:
                count = len(values)
                points = []
                for i, value in enumerate(values):
                    x = left + (plot_w * i / max(count - 1, 1))
                    y = y0 + plot_h - min(value, maximum) / maximum * plot_h
                    points.extend((x, y))
                if len(points) >= 4:
                    canvas.create_line(*points, fill=self._color(color), width=2, smooth=True)
                else:
                    canvas.create_oval(points[0] - 2, points[1] - 2, points[0] + 2,
                                       points[1] + 2, fill=self._color(color), outline=self._color(color))
                canvas.create_text(left, y0 + plot_h + 8,
                                   text=f"0s  ·  {self.samples[-1]['elapsed']:.0f}s",
                                   fill=self._color(MUTED), anchor="w", font=("Segoe UI", 8))
            else:
                canvas.create_text(left + plot_w / 2, y0 + plot_h / 2,
                                   text="Start monitoring to collect samples", fill=self._color(MUTED),
                                   font=("Segoe UI", 9))

    @staticmethod
    def _safe(call):
        try:
            return call()
        except (psutil.Error, OSError):
            return None

    @staticmethod
    def _display(value):
        return "Unavailable" if value is None else str(value)

    def _color(self, value):
        return value[1 if self.dark_mode else 0] if isinstance(value, tuple) else value

    def toggle_theme(self):
        self.dark_mode = bool(self.theme_switch.get())
        ctk.set_appearance_mode("Dark" if self.dark_mode else "Light")
        self.configure(fg_color=BG)
        self.chart.configure(bg=self._color(SURFACE))
        self.draw_chart()

    def on_close(self):
        self.stop_monitoring()
        self.destroy()


if __name__ == "__main__":
    ProcessLens().mainloop()
