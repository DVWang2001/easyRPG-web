"""easyRPG-web 的 Tkinter GUI（薄前端，呼叫 easyrpg_web_build 核心）。"""
from __future__ import annotations

import queue
import threading
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

import easyrpg_web_build as core


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("EasyRPG → 網頁版/PWA 打包工具")
        self.log_q: queue.Queue = queue.Queue()

        self.game = tk.StringVar()
        self.label = tk.StringVar()
        self.soundfont = tk.StringVar(value=str(core.DEFAULT_SOUNDFONT))
        self.icon = tk.StringVar(value=str(core.DEFAULT_ICON))
        self.rtp = tk.StringVar()
        self.out = tk.StringVar(value="dist")
        self.deploy = tk.BooleanVar(value=False)
        self.refresh = tk.BooleanVar(value=False)

        self._build_form()
        self.root.after(100, self._drain_log)

    def _row(self, parent, r, text, var, picker):
        ttk.Label(parent, text=text).grid(row=r, column=0, sticky="w", padx=4, pady=3)
        ttk.Entry(parent, textvariable=var, width=48).grid(row=r, column=1, padx=4)
        if picker:
            ttk.Button(parent, text="…", width=3, command=picker).grid(row=r, column=2)

    def _build_form(self):
        f = ttk.Frame(self.root, padding=10)
        f.grid(sticky="nsew")
        self._row(f, 0, "遊戲資料夾", self.game,
                  lambda: self._pick_dir(self.game, on_game=True))
        self._row(f, 1, "App 名稱", self.label, None)
        self._row(f, 2, "音色 SF2", self.soundfont, lambda: self._pick_file(self.soundfont))
        self._row(f, 3, "App 圖示", self.icon, lambda: self._pick_file(self.icon))
        self._row(f, 4, "RTP（選填）", self.rtp, lambda: self._pick_dir(self.rtp))
        self._row(f, 5, "輸出夾", self.out, lambda: self._pick_dir(self.out))
        ttk.Checkbutton(f, text="完成後部署到 GitHub Pages",
                        variable=self.deploy).grid(row=6, column=1, sticky="w")
        ttk.Checkbutton(f, text="強制更新 web player",
                        variable=self.refresh).grid(row=7, column=1, sticky="w")
        self.run_btn = ttk.Button(f, text="開始打包", command=self._run)
        self.run_btn.grid(row=8, column=1, sticky="w", pady=6)
        self.log = ScrolledText(f, width=70, height=16, state="disabled")
        self.log.grid(row=9, column=0, columnspan=3, pady=6)

    def _pick_dir(self, var, on_game=False):
        d = filedialog.askdirectory()
        if d:
            var.set(d)
            if on_game and not self.label.get():
                self.label.set(Path(d).name)

    def _pick_file(self, var):
        p = filedialog.askopenfilename()
        if p:
            var.set(p)

    def _emit(self, msg):
        self.log_q.put(msg)

    def _drain_log(self):
        while not self.log_q.empty():
            msg = self.log_q.get()
            self.log.configure(state="normal")
            self.log.insert("end", msg + "\n")
            self.log.see("end")
            self.log.configure(state="disabled")
        self.root.after(100, self._drain_log)

    def _run(self):
        if not self.game.get():
            messagebox.showerror("缺少設定", "請先選遊戲資料夾")
            return
        self.run_btn.configure(state="disabled")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        try:
            out = core.build(
                game=self.game.get(),
                app_label=self.label.get() or None,
                soundfont=self.soundfont.get() or None,
                app_icon=self.icon.get() or None,
                rtp=self.rtp.get() or None,
                out=self.out.get() or "dist",
                refresh_player=self.refresh.get(),
                deploy=self.deploy.get(),
                log=self._emit,
            )
            self._emit(f"✓ 完成，輸出在：{out}")
        except Exception as e:  # noqa: BLE001 — GUI 需把任何錯誤回報給使用者
            self._emit(f"✗ 失敗：{e}")
        finally:
            self.root.after(0, lambda: self.run_btn.configure(state="normal"))


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
