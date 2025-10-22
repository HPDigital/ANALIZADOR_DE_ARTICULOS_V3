import json
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

from analyzer import load_openai_client, process_pdf, find_pdfs


CONFIG_FILE = "config.json"


class AnalyzerGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Analizador de Artículos V3")
        self.geometry("980x640")
        self.minsize(900, 560)
        self.config_data = self._load_config()
        self._build_ui()

    def _build_ui(self) -> None:
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        container = ttk.Frame(self, padding=16)
        container.pack(fill=tk.BOTH, expand=True)

        input_frame = ttk.LabelFrame(container, text="Entrada", padding=12)
        input_frame.pack(fill=tk.X)

        self.path_var = tk.StringVar(value=self.config_data.get("last_path", ""))
        ttk.Label(input_frame, text="Archivo o carpeta PDF:").grid(row=0, column=0, sticky=tk.W, padx=(0, 8), pady=4)
        path_entry = ttk.Entry(input_frame, textvariable=self.path_var)
        path_entry.grid(row=0, column=1, sticky=tk.EW, pady=4)
        input_frame.columnconfigure(1, weight=1)
        ttk.Button(input_frame, text="Seleccionar archivo", command=self._select_file).grid(row=0, column=2, padx=4)
        ttk.Button(input_frame, text="Seleccionar carpeta", command=self._select_dir).grid(row=0, column=3)

        self.out_dir_var = tk.StringVar(value=self.config_data.get("last_out_dir", ""))
        ttk.Label(input_frame, text="Carpeta de salida (opcional):").grid(row=1, column=0, sticky=tk.W, padx=(0, 8), pady=4)
        out_entry = ttk.Entry(input_frame, textvariable=self.out_dir_var)
        out_entry.grid(row=1, column=1, sticky=tk.EW, pady=4)
        ttk.Button(input_frame, text="Explorar", command=self._select_out_dir).grid(row=1, column=2, padx=4)

        self.key_var = tk.StringVar(value=os.getenv("OPENAI_API_KEY", ""))
        ttk.Label(input_frame, text="OPENAI_API_KEY (opcional):").grid(row=2, column=0, sticky=tk.W, padx=(0, 8), pady=4)
        key_entry = ttk.Entry(input_frame, textvariable=self.key_var, show="*")
        key_entry.grid(row=2, column=1, sticky=tk.EW, pady=4)
        ttk.Button(input_frame, text="Usar ENV", command=self._use_env_key).grid(row=2, column=2, padx=4)

        # Opciones del modelo
        opts_frame = ttk.LabelFrame(container, text="Opciones de análisis", padding=12)
        opts_frame.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(opts_frame, text="Modelo:").grid(row=0, column=0, sticky=tk.W)
        self.model_var = tk.StringVar(value=self.config_data.get("model", "gpt-4o-2024-08-06"))
        model_cb = ttk.Combobox(
            opts_frame,
            textvariable=self.model_var,
            values=["gpt-4o-2024-08-06", "gpt-4o-mini-2024-07-18"],
            state="readonly",
            width=24,
        )
        model_cb.grid(row=0, column=1, sticky=tk.W, padx=(8, 16))
        ttk.Label(opts_frame, text="Temperatura:").grid(row=0, column=2, sticky=tk.W)
        self.temp_var = tk.DoubleVar(value=float(self.config_data.get("temperature", 0.2)))
        ttk.Spinbox(opts_frame, from_=0.0, to=1.0, increment=0.1, textvariable=self.temp_var, width=6).grid(
            row=0, column=3, sticky=tk.W, padx=(8, 16)
        )
        ttk.Label(opts_frame, text="Máx. tokens salida:").grid(row=0, column=4, sticky=tk.W)
        self.max_tokens_var = tk.IntVar(value=int(self.config_data.get("max_output_tokens", 1200)))
        ttk.Spinbox(opts_frame, from_=300, to=4000, increment=100, textvariable=self.max_tokens_var, width=8).grid(
            row=0, column=5, sticky=tk.W, padx=(8, 0)
        )

        actions = ttk.Frame(container)
        actions.pack(fill=tk.X, pady=(12, 0))
        self.run_btn = ttk.Button(actions, text="Analizar", command=self._run)
        self.run_btn.pack(side=tk.LEFT)
        self.stop_requested = False
        ttk.Button(actions, text="Cancelar", command=self._cancel).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(actions, text="Abrir carpeta salida", command=self._open_out_dir).pack(side=tk.LEFT, padx=(8, 0))

        self.progress = ttk.Progressbar(actions, mode="determinate", length=260)
        self.progress.pack(side=tk.RIGHT)

        log_frame = ttk.LabelFrame(container, text="Progreso", padding=12)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        self.log = tk.Text(log_frame, height=20, wrap=tk.WORD)
        # Colores de log
        self.log.tag_config("info", foreground="#1f6feb")
        self.log.tag_config("success", foreground="#1a7f37")
        self.log.tag_config("error", foreground="#d1242f")
        self.log.pack(fill=tk.BOTH, expand=True)

        status_frame = ttk.Frame(container)
        status_frame.pack(fill=tk.X, pady=(8, 0))
        self.status_var = tk.StringVar(value="Listo")
        ttk.Label(status_frame, textvariable=self.status_var, anchor=tk.W).pack(fill=tk.X)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _select_file(self) -> None:
        path = filedialog.askopenfilename(title="Selecciona un PDF", filetypes=[("PDF", "*.pdf")])
        if path:
            self.path_var.set(path)

    def _select_dir(self) -> None:
        path = filedialog.askdirectory(title="Selecciona una carpeta con PDFs")
        if path:
            self.path_var.set(path)

    def _select_out_dir(self) -> None:
        path = filedialog.askdirectory(title="Selecciona carpeta de salida")
        if path:
            self.out_dir_var.set(path)

    def _use_env_key(self) -> None:
        self.key_var.set(os.getenv("OPENAI_API_KEY", ""))

    def _append_log(self, text: str, level: str = "info") -> None:
        tag = level if level in ("info", "success", "error") else "info"
        self.log.insert(tk.END, text + "\n", tag)
        self.log.see(tk.END)

    def _cancel(self) -> None:
        self.stop_requested = True
        self.status_var.set("Cancelando...")

    def _open_out_dir(self) -> None:
        path = self.out_dir_var.get().strip() or os.path.dirname(self.path_var.get().strip() or ".")
        if path and os.path.isdir(path):
            try:
                os.startfile(path)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir la carpeta: {e}")
        else:
            messagebox.showinfo("Carpeta", "Define una carpeta de salida o selecciona archivos primero.")

    def _run(self) -> None:
        target = self.path_var.get().strip()
        if not target:
            messagebox.showwarning("Falta ruta", "Selecciona un archivo PDF o una carpeta.")
            return
        self.stop_requested = False
        self.run_btn.configure(state=tk.DISABLED)
        self.log.delete("1.0", tk.END)
        self.status_var.set("Estimando coste y preparando...")
        # guardar preferencias
        self._save_config()
        # reset progreso
        self.progress.configure(value=0, maximum=1)
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self) -> None:
        target = self.path_var.get().strip()
        out_dir = self.out_dir_var.get().strip() or None
        key = self.key_var.get().strip() or None
        model = self.model_var.get().strip() or "gpt-4o-2024-08-06"
        temperature = float(self.temp_var.get())
        max_output_tokens = int(self.max_tokens_var.get())
        try:
            client = load_openai_client(key)
        except Exception as e:
            self._finish_with_error(f"Error con OpenAI: {e}")
            return

        paths: list[str] = []
        if os.path.isdir(target):
            paths = find_pdfs(target, recursive=True)
        elif os.path.isfile(target) and target.lower().endswith(".pdf"):
            paths = [target]
        else:
            self._finish_with_error("Ruta no válida. Selecciona PDF o carpeta con PDFs.")
            return

        if not paths:
            self._finish_with_error("No se encontraron archivos PDF.")
            return

        # Estimación simple de tokens
        try:
            total_bytes = sum(max(1, os.path.getsize(p)) for p in paths)
            approx_in_tokens = total_bytes // 4
            approx_out_tokens = len(paths) * max_output_tokens
            self._append_log(
                f"≈ Tokens entrada: {approx_in_tokens:,} | salida: {approx_out_tokens:,}",
                level="info",
            )
        except Exception:
            pass

        success, fails = 0, 0
        self.progress.configure(maximum=len(paths), value=0)
        for pdf in paths:
            if self.stop_requested:
                break
            self._append_log(f"Procesando: {pdf}")
            try:
                out_path = process_pdf(
                    pdf,
                    client,
                    out_dir,
                    model=model,
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                    progress_cb=lambda msg, p=pdf: self._append_log(f"  - {msg}", level="info"),
                    cancel_cb=lambda: self.stop_requested,
                )
                success += 1
                self._append_log(f"✓ Guardado: {out_path}", level="success")
            except Exception as e:
                fails += 1
                self._append_log(f"✗ Error: {e}", level="error")
            finally:
                try:
                    self.progress.step(1)
                except Exception:
                    pass

        if self.stop_requested:
            self._finish_with_message(f"Cancelado. Exitosos: {success}, Fallidos: {fails}")
        else:
            self._finish_with_message(f"Completado. Exitosos: {success}, Fallidos: {fails}")

    def _finish_with_error(self, msg: str) -> None:
        self._append_log(msg, level="error")
        self.status_var.set(msg)
        self.run_btn.configure(state=tk.NORMAL)

    def _finish_with_message(self, msg: str) -> None:
        self.status_var.set(msg)
        self.run_btn.configure(state=tk.NORMAL)

    def _load_config(self) -> dict:
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save_config(self) -> None:
        data = {
            "last_path": self.path_var.get().strip(),
            "last_out_dir": self.out_dir_var.get().strip(),
            "model": self.model_var.get().strip() if hasattr(self, "model_var") else "",
            "temperature": self.temp_var.get() if hasattr(self, "temp_var") else 0.2,
            "max_output_tokens": self.max_tokens_var.get() if hasattr(self, "max_tokens_var") else 1200,
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _on_close(self) -> None:
        try:
            self._save_config()
        finally:
            self.destroy()


def main() -> None:
    app = AnalyzerGUI()
    app.mainloop()


if __name__ == "__main__":
    main()

