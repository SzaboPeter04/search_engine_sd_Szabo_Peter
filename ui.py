import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from db import search_documents, get_document_content
from indexer import Indexer


class SearchEngineUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Search Engine")
        self.geometry("950x650")
        self.search_after_id = None
        self.result_paths = {}
        self.root_dir_var = tk.StringVar(value=os.getcwd())
        self.search_var = tk.StringVar()
        self._build_widgets()
        self.refresh_results()

    def _build_widgets(self):
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text="Root folder:").pack(side="left")
        tk.Entry(top, textvariable=self.root_dir_var, width=60, bd=0, highlightthickness=0).pack(side="left", padx=5)
        tk.Button(top, text="Browse", command=self.browse_folder, bd=0, relief="flat").pack(side="left")
        tk.Button(top, text="Index Files", command=self.start_indexing, bd=0, relief="flat").pack(side="left", padx=5)
        search_frame = ttk.Frame(self, padding=(10, 0, 10, 10))
        search_frame.pack(fill="x")
        ttk.Label(search_frame, text="Search:").pack(side="left")
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=60, bd=0, highlightthickness=0)
        search_entry.pack(side="left", fill="x", expand=True, padx=5)
        search_entry.bind("<KeyRelease>", self.on_search_change)
        main = ttk.PanedWindow(self, orient="vertical")
        main.pack(fill="both", expand=True, padx=10, pady=10)
        results_frame = ttk.Frame(main)
        preview_frame = ttk.Frame(main)
        main.add(results_frame, weight=3)
        main.add(preview_frame, weight=2)
        self.tree = ttk.Treeview(
            results_frame,
            columns=("filename", "extension", "path"),
            show="headings",
            height=15
        )
        self.tree.heading("filename", text="Filename")
        self.tree.heading("extension", text="Type")
        self.tree.heading("path", text="Path")
        self.tree.column("filename", width=220)
        self.tree.column("extension", width=80)
        self.tree.column("path", width=600)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_result_selected)
        self.preview_text = tk.Text(preview_frame, wrap="word", bd=0, highlightthickness=0)
        self.preview_text.pack(fill="both", expand=True)
        self.status_var = tk.StringVar(value="Ready.")
        status = tk.Label(self, textvariable=self.status_var, relief="flat", bd=0, anchor="w")
        status.pack(fill="x", side="bottom")

    def browse_folder(self):
        selected = filedialog.askdirectory()
        if selected:
            self.root_dir_var.set(selected)

    def set_status(self, message: str):
        def _update():
            try:
                if isinstance(message, int):
                    self.status_var.set(f"New files added: {message}")
                    return
                if isinstance(message, str) and message.isdigit():
                    self.status_var.set(f"New files added: {int(message)}")
                    return
            except Exception:
                pass
            self.status_var.set(str(message))

        self.after(0, _update)

    def start_indexing(self):
        root_dir = self.root_dir_var.get().strip()
        if not root_dir:
            messagebox.showerror("Error", "Choose a folder first.")
            return

        thread = threading.Thread(
            target=self.run_indexing,
            args=(root_dir,),
            daemon=True
        )
        thread.start()

    def run_indexing(self, root_dir: str):
        try:
            indexer = Indexer(status_callback=self.set_status)
            summary = indexer.index_directory(root_dir)
            self.after(0, lambda: self.show_summary(summary))
            self.after(0, self.refresh_results)
        except Exception as exc:
            self.set_status(f"Indexing failed: {exc}")

    def show_summary(self, summary):
        new = summary.get("new_added", 0)
        indexed = summary.get("indexed", 0)
        failed = summary.get("failed", 0)
        msg = f"New files added: {new}\nIndexed: {indexed}\nFailed: {failed}"
        try:
            messagebox.showinfo("Indexing summary", msg)
        except Exception:
            pass
        self.set_status(new)

    def on_search_change(self, _event=None):
        if self.search_after_id:
            self.after_cancel(self.search_after_id)
        self.search_after_id = self.after(200, self.refresh_results)

    def refresh_results(self):
        query = self.search_var.get().strip()
        rows = search_documents(query)

        for item in self.tree.get_children():
            self.tree.delete(item)

        self.result_paths.clear()

        for i, row in enumerate(rows):
            iid = str(i)
            self.result_paths[iid] = row["path"]
            self.tree.insert(
                "",
                "end",
                iid=iid,
                values=(row["filename"], row["extension"], row["path"])
            )

        self.preview_text.delete("1.0", tk.END)
        self.status_var.set(f"{len(rows)} result(s).")

    def on_result_selected(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return

        iid = selected[0]
        path = self.result_paths.get(iid)
        if not path:
            return

        content = get_document_content(path)

        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert(
            tk.END,
            f"Path:\n{path}\n\n"
            f"Preview:\n"
            f"{content[:3000]}"
        )