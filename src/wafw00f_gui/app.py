from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
import logging
from pathlib import Path
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from urllib.parse import urlparse

from wafw00f_gui import __version__
from wafw00f_gui.logging_utils import setup_logging
from wafw00f_gui.runner import ScanConfig, ScanResult, UiEventBridge, Wafw00fRunner


class Wafw00fGuiApp:
    TERMS_VERSION = "2026-03-07"
    MAINTAINER = "Letmehackyou011"

    def __init__(self) -> None:
        log_file = setup_logging()
        self.logger = logging.getLogger(__name__)
        self.logger.info("Starting wafw00f GUI v%s", __version__)

        self.root = tk.Tk()
        self.root.title("wafw00f GUI")
        self.root.geometry("980x680")
        self.root.minsize(900, 620)
        self._logo_image: tk.PhotoImage | None = None
        self._apply_logo()
        self._configure_style()

        self.app_dir = Path.home() / ".wafw00f-gui"
        self.consent_file = self.app_dir / "consent.json"

        self.runner = Wafw00fRunner()
        self.bridge = UiEventBridge()
        self.history: list[ScanResult] = []

        self.url_var = tk.StringVar()
        self.find_all_var = tk.BooleanVar(value=False)
        self.verbose_var = tk.BooleanVar(value=False)
        self.no_redirect_var = tk.BooleanVar(value=False)
        self.extra_args_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        self.summary_var = tk.StringVar(value="No scan yet")

        self._build_ui()

        if not self._ensure_terms_accepted():
            self.logger.warning("Terms were not accepted; closing application")
            self.root.after(10, self.root.destroy)
            return

        self.root.after(120, self._poll_events)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.status_var.set(f"Ready | log: {log_file}")

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        themes = set(style.theme_names())
        if "vista" in themes:
            style.theme_use("vista")
        elif "clam" in themes:
            style.theme_use("clam")

        style.configure("Header.TLabel", font=("Segoe UI", 17, "bold"))
        style.configure("SubHeader.TLabel", font=("Segoe UI", 10))

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)

        top_frame = ttk.Frame(self.root, padding=12)
        top_frame.grid(row=0, column=0, sticky="ew")
        top_frame.columnconfigure(1, weight=1)

        ttk.Label(top_frame, text="wafw00f GUI", style="Header.TLabel").grid(
            row=0, column=0, columnspan=4, sticky="w"
        )
        ttk.Label(
            top_frame,
            text="Web Application Firewall fingerprinting desktop client",
            style="SubHeader.TLabel",
        ).grid(row=1, column=0, columnspan=4, sticky="w", pady=(2, 10))

        if self._logo_image is not None:
            logo_label = ttk.Label(top_frame, image=self._logo_image)
            logo_label.grid(row=0, column=4, rowspan=3, sticky="ne", padx=(12, 0))

        ttk.Label(top_frame, text="Target URL:").grid(row=2, column=0, sticky="w", padx=(0, 8))
        self.url_entry = ttk.Entry(top_frame, textvariable=self.url_var)
        self.url_entry.grid(row=2, column=1, sticky="ew")
        self.url_entry.insert(0, "https://example.org")

        self.run_btn = ttk.Button(top_frame, text="Run Scan", command=self.start_scan)
        self.run_btn.grid(row=2, column=2, padx=(10, 0))

        self.stop_btn = ttk.Button(top_frame, text="Stop", command=self.stop_scan, state="disabled")
        self.stop_btn.grid(row=2, column=3, padx=(8, 0))

        options_frame = ttk.LabelFrame(self.root, text="Options", padding=12)
        options_frame.grid(row=1, column=0, sticky="ew", padx=12)
        options_frame.columnconfigure(4, weight=1)

        ttk.Checkbutton(options_frame, text="Find all WAFs (-a)", variable=self.find_all_var).grid(
            row=0, column=0, sticky="w", padx=(0, 16)
        )
        ttk.Checkbutton(options_frame, text="Verbose (-v)", variable=self.verbose_var).grid(
            row=0, column=1, sticky="w", padx=(0, 16)
        )
        ttk.Checkbutton(options_frame, text="No redirect (-r)", variable=self.no_redirect_var).grid(
            row=0, column=2, sticky="w", padx=(0, 16)
        )
        ttk.Label(options_frame, text="Extra args:").grid(row=0, column=3, sticky="e", padx=(0, 8))
        ttk.Entry(options_frame, textvariable=self.extra_args_var).grid(row=0, column=4, sticky="ew")

        main_pane = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        main_pane.grid(row=2, column=0, sticky="nsew", padx=12, pady=(10, 10))

        left = ttk.Frame(main_pane)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)
        main_pane.add(left, weight=4)

        ttk.Label(left, text="Live Output").grid(row=0, column=0, sticky="w", pady=(0, 6))

        text_frame = ttk.Frame(left)
        text_frame.grid(row=1, column=0, sticky="nsew")
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        self.output_text = tk.Text(text_frame, wrap="word", state="disabled", height=20)
        self.output_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.output_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.output_text.configure(yscrollcommand=scrollbar.set)

        actions = ttk.Frame(left)
        actions.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        actions.columnconfigure(4, weight=1)

        ttk.Button(actions, text="Clear Output", command=self.clear_output).grid(row=0, column=0)
        ttk.Button(actions, text="Export TXT", command=self.export_txt).grid(row=0, column=1, padx=(8, 0))
        ttk.Button(actions, text="Export JSON", command=self.export_json).grid(row=0, column=2, padx=(8, 0))
        ttk.Label(actions, textvariable=self.summary_var).grid(row=0, column=4, sticky="e")

        right = ttk.Frame(main_pane, padding=(8, 0, 0, 0))
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)
        main_pane.add(right, weight=2)

        ttk.Label(right, text="History").grid(row=0, column=0, sticky="w", pady=(0, 6))

        self.history_list = tk.Listbox(right, height=10)
        self.history_list.grid(row=1, column=0, sticky="nsew")
        self.history_list.bind("<<ListboxSelect>>", self._on_history_select)

        footer = ttk.Frame(self.root, padding=(12, 0, 12, 12))
        footer.grid(row=3, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        ttk.Label(footer, textvariable=self.status_var).grid(row=0, column=0, sticky="w")
        ttk.Button(footer, text="Terms", command=self.show_terms).grid(row=0, column=1, sticky="e", padx=(0, 8))
        ttk.Button(footer, text="About", command=self.show_about).grid(row=0, column=2, sticky="e")

        self.root.bind("<Return>", lambda _event: self.start_scan())
        self.root.bind("<Control-l>", self._focus_url)

    def run(self) -> None:
        self.root.mainloop()

    def start_scan(self) -> None:
        if self.runner.is_running:
            return

        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Missing target", "Please enter a target URL, e.g. https://example.org")
            return

        valid, validation_message = self._validate_target_url(url)
        if not valid:
            messagebox.showerror("Invalid target URL", validation_message)
            return

        config = ScanConfig(
            target_url=url,
            find_all=self.find_all_var.get(),
            verbose=self.verbose_var.get(),
            no_redirect=self.no_redirect_var.get(),
            extra_args=self.extra_args_var.get(),
        )

        self.clear_output()
        self._append_output(f"[info] Started at {datetime.now().isoformat(timespec='seconds')}")
        self._append_output(f"[info] Target: {url}")

        try:
            self.runner.run_async(config, self.bridge.push_line, self.bridge.push_done)
        except Exception as exc:
            self.logger.exception("Cannot start scan")
            messagebox.showerror("Cannot start", str(exc))
            return

        self.run_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_var.set("Scan running...")
        self.summary_var.set("Running")

    def stop_scan(self) -> None:
        self.runner.stop()
        self.status_var.set("Stopping scan...")

    def clear_output(self) -> None:
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.configure(state="disabled")

    def export_txt(self) -> None:
        content = self._get_output_text().strip()
        if not content:
            messagebox.showinfo("Nothing to export", "No output to export yet.")
            return

        path = filedialog.asksaveasfilename(
            title="Export output as TXT",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile="wafw00f_scan.txt",
        )
        if not path:
            return

        try:
            Path(path).write_text(content, encoding="utf-8")
        except Exception as exc:
            self.logger.exception("TXT export failed")
            messagebox.showerror("Export failed", f"Could not export TXT file.\n\n{exc}")
            return

        self.status_var.set(f"Exported TXT: {path}")

    def export_json(self) -> None:
        if not self.history:
            messagebox.showinfo("Nothing to export", "Run at least one scan before exporting JSON.")
            return

        path = filedialog.asksaveasfilename(
            title="Export scan history as JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="wafw00f_scans.json",
        )
        if not path:
            return

        payload = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "total_scans": len(self.history),
            "scans": [asdict(item) for item in self.history],
        }

        try:
            Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception as exc:
            self.logger.exception("JSON export failed")
            messagebox.showerror("Export failed", f"Could not export JSON file.\n\n{exc}")
            return

        self.status_var.set(f"Exported JSON: {path}")

    def _on_history_select(self, _event: object) -> None:
        selection = self.history_list.curselection()
        if not selection:
            return

        idx = selection[0]
        if idx < 0 or idx >= len(self.history):
            return

        result = self.history[idx]
        self.clear_output()
        self._append_output(result.output)
        self.summary_var.set(self._build_summary(result))
        self.status_var.set(f"Loaded history item {idx + 1}")

    def _poll_events(self) -> None:
        while not self.bridge.queue.empty():
            event_type, payload = self.bridge.queue.get_nowait()

            if event_type == "line":
                self._append_output(str(payload))
            elif event_type == "done":
                result = payload
                assert isinstance(result, ScanResult)
                self._finish_scan(result)

        self.root.after(120, self._poll_events)

    def _finish_scan(self, result: ScanResult) -> None:
        self.run_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

        self.history.insert(0, result)
        self._refresh_history()

        summary = self._build_summary(result)
        self.summary_var.set(summary)

        if result.exit_code is None:
            self.status_var.set("Scan failed to execute")
            if result.error_message:
                self.logger.error("Scan failed: %s", result.error_message)
        elif result.stopped:
            self.status_var.set("Scan stopped by user")
        elif result.exit_code != 0:
            self.status_var.set(f"Scan finished with errors (exit {result.exit_code})")
            if "No module named wafw00f" in result.output:
                messagebox.showerror(
                    "wafw00f not installed",
                    "wafw00f is not installed in this Python environment.\n\n"
                    "Install it with: python -m pip install wafw00f",
                )
            else:
                snippet = result.output.strip()
                if len(snippet) > 900:
                    snippet = snippet[:900] + "\n..."
                if snippet:
                    messagebox.showerror(
                        "Scan failed",
                        "The scan command failed. Check the output panel for full details.\n\n"
                        f"Last output:\n{snippet}",
                    )
        else:
            self.status_var.set("Scan completed")

    def _refresh_history(self) -> None:
        self.history_list.delete(0, tk.END)
        for result in self.history:
            waf = ", ".join(result.detected_wafs) if result.detected_wafs else "No WAF detected"
            label = f"{result.finished_at[:19]} | {result.target_url} | {waf}"
            self.history_list.insert(tk.END, label)

    def _build_summary(self, result: ScanResult) -> str:
        waf = ", ".join(result.detected_wafs) if result.detected_wafs else "No WAF detected"
        requests = f"requests={result.request_count}" if result.request_count is not None else "requests=?"
        code = result.exit_code if result.exit_code is not None else "error"
        return f"{waf} | {requests} | exit={code}"

    def _append_output(self, text: str) -> None:
        self.output_text.configure(state="normal")
        self.output_text.insert(tk.END, text + "\n")
        self.output_text.see(tk.END)
        self.output_text.configure(state="disabled")

    def _get_output_text(self) -> str:
        return self.output_text.get("1.0", tk.END)

    def show_about(self) -> None:
        about_text = (
            f"wafw00f GUI v{__version__}\n\n"
            "Maintainer:\n"
            f"- {self.MAINTAINER} (GitHub)\n\n"
            "Original wafw00f developers:\n"
            "- Sandro Gauci\n"
            "- Pinaki Mondal\n"
            "- Upstream: https://github.com/EnableSecurity/wafw00f\n\n"
            "License:\n"
            "- BSD-3-Clause"
        )
        messagebox.showinfo("About wafw00f GUI", about_text)

    @staticmethod
    def _resource_path(*parts: str) -> Path:
        base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
        return base_dir.joinpath(*parts)

    def _apply_logo(self) -> None:
        logo_path = self._resource_path("assets", "logo.png")
        if not logo_path.exists():
            self.logger.info("Logo file not found at %s", logo_path)
            return

        try:
            image = tk.PhotoImage(file=str(logo_path))
            subsample_factor = 8 if image.width() > 256 else 4
            self._logo_image = image.subsample(subsample_factor, subsample_factor)
            self.root.iconphoto(True, self._logo_image)
        except Exception:
            self.logger.exception("Failed loading logo from %s", logo_path)

    def show_terms(self) -> None:
        messagebox.showinfo("Terms & Legal Disclaimer", self._terms_text())

    def _focus_url(self, _event: object) -> None:
        self.url_entry.focus_set()
        self.url_entry.select_range(0, tk.END)

    def _ensure_terms_accepted(self) -> bool:
        consent = self._load_consent()
        if consent.get("accepted") and consent.get("version") == self.TERMS_VERSION:
            return True

        accepted = self._show_terms_acceptance_dialog()
        if accepted:
            self._save_consent(
                {
                    "accepted": True,
                    "version": self.TERMS_VERSION,
                    "accepted_at": datetime.utcnow().isoformat() + "Z",
                    "maintainer": self.MAINTAINER,
                }
            )
            return True

        return False

    def _show_terms_acceptance_dialog(self) -> bool:
        dialog = tk.Toplevel(self.root)
        dialog.title("Terms & Conditions")
        dialog.geometry("760x520")
        dialog.minsize(720, 480)
        dialog.transient(self.root)
        dialog.grab_set()

        accepted = {"value": False}

        wrapper = ttk.Frame(dialog, padding=12)
        wrapper.pack(fill="both", expand=True)
        wrapper.columnconfigure(0, weight=1)
        wrapper.rowconfigure(1, weight=1)

        ttk.Label(wrapper, text="Terms & Conditions", style="Header.TLabel").grid(row=0, column=0, sticky="w")

        text_frame = ttk.Frame(wrapper)
        text_frame.grid(row=1, column=0, sticky="nsew", pady=(8, 8))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        terms_text = tk.Text(text_frame, wrap="word", height=18)
        terms_text.grid(row=0, column=0, sticky="nsew")
        terms_text.insert("1.0", self._terms_text())
        terms_text.configure(state="disabled")

        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=terms_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        terms_text.configure(yscrollcommand=scrollbar.set)

        agree_var = tk.BooleanVar(value=False)

        actions = ttk.Frame(wrapper)
        actions.grid(row=3, column=0, sticky="e", pady=(10, 0))
        accept_btn = ttk.Button(actions, text="Accept and Continue", state="disabled")

        def toggle_accept() -> None:
            accept_btn.configure(state=("normal" if agree_var.get() else "disabled"))

        ttk.Checkbutton(
            wrapper,
            text="I have read and agree to the Terms & Conditions and Legal Disclaimer",
            variable=agree_var,
            command=toggle_accept,
        ).grid(row=2, column=0, sticky="w")

        def on_accept() -> None:
            accepted["value"] = True
            dialog.destroy()

        def on_decline() -> None:
            if messagebox.askyesno(
                "Decline Terms",
                "You must accept the Terms & Conditions to use this application. Exit now?",
                parent=dialog,
            ):
                accepted["value"] = False
                dialog.destroy()

        accept_btn.configure(command=on_accept)
        accept_btn.grid(row=0, column=0, padx=(0, 8))
        ttk.Button(actions, text="Decline", command=on_decline).grid(row=0, column=1)

        dialog.protocol("WM_DELETE_WINDOW", on_decline)
        self.root.wait_window(dialog)
        return accepted["value"]

    def _terms_text(self) -> str:
        return (
            "IMPORTANT LEGAL DISCLAIMER\n\n"
            "This application performs web application firewall fingerprinting and may send security-related "
            "HTTP requests to target systems.\n\n"
            "By clicking 'Accept and Continue', you agree that:\n"
            "1) You will use this software only on systems you own or are explicitly authorized to test.\n"
            "2) You are solely responsible for complying with applicable laws, regulations, and contracts.\n"
            "3) Unauthorized scanning or testing may be illegal in your jurisdiction.\n"
            "4) The software is provided 'AS IS' without warranties, under the BSD-3-Clause license.\n"
            "5) The maintainer and upstream contributors are not liable for misuse, damages, or legal claims.\n\n"
            f"Maintainer: {self.MAINTAINER} (GitHub)\n"
            "Original wafw00f developers: Sandro Gauci, Pinaki Mondal\n"
            "Upstream project: https://github.com/EnableSecurity/wafw00f\n"
        )

    def _load_consent(self) -> dict[str, object]:
        try:
            if not self.consent_file.exists():
                return {}
            return json.loads(self.consent_file.read_text(encoding="utf-8"))
        except Exception:
            self.logger.exception("Could not read consent file")
            return {}

    def _save_consent(self, payload: dict[str, object]) -> None:
        try:
            self.app_dir.mkdir(parents=True, exist_ok=True)
            self.consent_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:
            self.logger.exception("Could not write consent file")

    @staticmethod
    def _validate_target_url(url: str) -> tuple[bool, str]:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False, "URL must start with http:// or https://"
        if not parsed.netloc:
            return False, "URL is missing host name"
        return True, ""

    def _on_close(self) -> None:
        if self.runner.is_running:
            if not messagebox.askyesno("Quit", "A scan is still running. Stop it and exit?"):
                return
            self.runner.stop()
        self.root.destroy()
