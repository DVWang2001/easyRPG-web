# easyrpg_web_gui.py
"""easyRPG-web 遊戲庫 GUI（Tkinter 清單編輯器，呼叫 build_library 核心）。"""
from __future__ import annotations

import queue
import threading
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

import easyrpg_web_build as core


class GameDialog(tk.Toplevel):
    """加入/編輯單一遊戲：名稱 + 封面（選填）+ RTP（勾選＋資料夾）。回傳 dict 或 None。"""

    def __init__(self, parent, folder, label="", cover="", rtp=""):
        super().__init__(parent)
        self.title("遊戲設定")
        self.result = None
        self.transient(parent)
        self.grab_set()

        self.v_label = tk.StringVar(value=label or Path(folder).name)
        self.v_cover = tk.StringVar(value=cover)
        self.v_rtp_on = tk.BooleanVar(value=bool(rtp))
        self.v_rtp = tk.StringVar(value=rtp)

        ttk.Label(self, text=f"資料夾：{folder}").grid(row=0, column=0, columnspan=3,
                                                     sticky="w", padx=8, pady=6)
        ttk.Label(self, text="顯示名稱").grid(row=1, column=0, sticky="w", padx=8)
        ttk.Entry(self, textvariable=self.v_label, width=36).grid(row=1, column=1, padx=4)
        ttk.Label(self, text="封面圖（選填）").grid(row=2, column=0, sticky="w", padx=8)
        ttk.Entry(self, textvariable=self.v_cover, width=36).grid(row=2, column=1, padx=4)
        ttk.Button(self, text="…", width=3, command=self._pick_cover).grid(row=2, column=2)
        ttk.Checkbutton(self, text="加入 RTP", variable=self.v_rtp_on).grid(
            row=3, column=0, columnspan=2, sticky="w", padx=8, pady=(6, 0))
        ttk.Label(self, text="RTP 資料夾").grid(row=4, column=0, sticky="w", padx=8)
        ttk.Entry(self, textvariable=self.v_rtp, width=36).grid(row=4, column=1, padx=4)
        ttk.Button(self, text="…", width=3, command=self._pick_rtp).grid(row=4, column=2)
        bar = ttk.Frame(self)
        bar.grid(row=5, column=0, columnspan=3, pady=8)
        ttk.Button(bar, text="確定", command=self._ok).pack(side="left", padx=4)
        ttk.Button(bar, text="取消", command=self.destroy).pack(side="left", padx=4)

        self._folder = folder

    def _pick_cover(self):
        p = filedialog.askopenfilename(
            filetypes=[("圖片", "*.png *.jpg *.jpeg *.gif"), ("全部", "*.*")])
        if p:
            self.v_cover.set(p)

    def _pick_rtp(self):
        d = filedialog.askdirectory(title="選擇 RTP 資料夾")
        if d:
            self.v_rtp.set(d)
            self.v_rtp_on.set(True)

    def _ok(self):
        if not self.v_label.get().strip():
            messagebox.showerror("缺少名稱", "請輸入顯示名稱", parent=self)
            return
        rtp = self.v_rtp.get().strip() if self.v_rtp_on.get() else ""
        self.result = {
            "folder": self._folder,
            "label": self.v_label.get().strip(),
            "cover": self.v_cover.get().strip() or None,
            "rtp": rtp or None,
        }
        self.destroy()


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("EasyRPG → 遊戲庫（網頁版/PWA）打包工具")
        self.log_q: queue.Queue = queue.Queue()
        self.games: list = []

        self.lib_name = tk.StringVar(value="我的遊戲庫")
        self.icon = tk.StringVar(value=str(core.DEFAULT_ICON))
        self.soundfont = tk.StringVar(value=str(core.DEFAULT_SOUNDFONT))
        self.out = tk.StringVar(value="dist")
        self.deploy = tk.BooleanVar(value=False)
        self.refresh = tk.BooleanVar(value=False)

        self._build_ui()
        self.root.after(100, self._drain_log)

    def _build_ui(self):
        f = ttk.Frame(self.root, padding=10)
        f.grid(sticky="nsew")

        top = ttk.Frame(f)
        top.grid(row=0, column=0, sticky="w", pady=(0, 6))
        ttk.Label(top, text="遊戲庫名稱").grid(row=0, column=0, padx=4)
        ttk.Entry(top, textvariable=self.lib_name, width=24).grid(row=0, column=1, padx=4)
        ttk.Label(top, text="App 圖示").grid(row=0, column=2, padx=4)
        ttk.Entry(top, textvariable=self.icon, width=28).grid(row=0, column=3, padx=4)
        ttk.Button(top, text="…", width=3,
                   command=lambda: self._pick_file(self.icon)).grid(row=0, column=4)

        self.tree = ttk.Treeview(f, columns=("label", "folder", "cover", "rtp"),
                                 show="headings", height=8)
        for col, txt, w in [("label", "名稱", 130), ("folder", "資料夾", 280),
                            ("cover", "封面", 100), ("rtp", "RTP", 100)]:
            self.tree.heading(col, text=txt)
            self.tree.column(col, width=w)
        self.tree.grid(row=1, column=0, sticky="nsew")

        btns = ttk.Frame(f)
        btns.grid(row=2, column=0, sticky="w", pady=4)
        ttk.Button(btns, text="＋ 加入遊戲", command=self._add).pack(side="left", padx=2)
        ttk.Button(btns, text="編輯", command=self._edit).pack(side="left", padx=2)
        ttk.Button(btns, text="移除", command=self._remove).pack(side="left", padx=2)
        ttk.Button(btns, text="↑", width=3, command=lambda: self._move(-1)).pack(side="left", padx=2)
        ttk.Button(btns, text="↓", width=3, command=lambda: self._move(1)).pack(side="left", padx=2)

        opt = ttk.Frame(f)
        opt.grid(row=3, column=0, sticky="w", pady=4)
        ttk.Label(opt, text="音色 SF2").grid(row=0, column=0, padx=4)
        ttk.Entry(opt, textvariable=self.soundfont, width=34).grid(row=0, column=1, padx=4)
        ttk.Button(opt, text="…", width=3,
                   command=lambda: self._pick_file(self.soundfont)).grid(row=0, column=2)
        ttk.Label(opt, text="輸出夾").grid(row=0, column=3, padx=4)
        ttk.Entry(opt, textvariable=self.out, width=14).grid(row=0, column=4, padx=4)

        chk = ttk.Frame(f)
        chk.grid(row=4, column=0, sticky="w")
        ttk.Checkbutton(chk, text="完成後部署到 GitHub Pages",
                        variable=self.deploy).pack(side="left", padx=4)
        ttk.Checkbutton(chk, text="強制更新 web player",
                        variable=self.refresh).pack(side="left", padx=4)

        self.run_btn = ttk.Button(f, text="開始打包遊戲庫", command=self._run)
        self.run_btn.grid(row=5, column=0, sticky="w", pady=6)
        self.log = ScrolledText(f, width=78, height=14, state="disabled")
        self.log.grid(row=6, column=0, pady=6)

    def _refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for g in self.games:
            cover = Path(g["cover"]).name if g.get("cover") else "（預設）"
            rtp = Path(g["rtp"]).name if g.get("rtp") else "（無）"
            self.tree.insert("", "end", values=(g["label"], str(g["folder"]), cover, rtp))

    def _selected_index(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return self.tree.index(sel[0])

    def _add(self):
        folder = filedialog.askdirectory(title="選擇遊戲資料夾")
        if not folder:
            return
        dlg = GameDialog(self.root, folder)
        self.root.wait_window(dlg)
        if dlg.result:
            self.games.append(dlg.result)
            self._refresh_tree()

    def _edit(self):
        i = self._selected_index()
        if i is None:
            return
        g = self.games[i]
        dlg = GameDialog(self.root, g["folder"], g["label"],
                         g.get("cover") or "", g.get("rtp") or "")
        self.root.wait_window(dlg)
        if dlg.result:
            self.games[i] = dlg.result
            self._refresh_tree()

    def _remove(self):
        i = self._selected_index()
        if i is None:
            return
        del self.games[i]
        self._refresh_tree()

    def _move(self, delta):
        i = self._selected_index()
        if i is None:
            return
        j = i + delta
        if 0 <= j < len(self.games):
            self.games[i], self.games[j] = self.games[j], self.games[i]
            self._refresh_tree()
            self.tree.selection_set(self.tree.get_children()[j])

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
        if not self.games:
            messagebox.showerror("沒有遊戲", "請先用「＋ 加入遊戲」加至少一個遊戲")
            return
        self.run_btn.configure(state="disabled")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        try:
            out = core.build_library(
                games=list(self.games),
                app_label=self.lib_name.get() or "我的遊戲庫",
                app_icon=self.icon.get() or None,
                soundfont=self.soundfont.get() or None,
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
