# easyrpg_web_gui.py
"""easyRPG-web 遊戲庫 GUI（持久化清單編輯器：增刪查改 ＋ 一鍵重建並部署）。"""
from __future__ import annotations

import queue
import threading
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

import easyrpg_web_build as core
import project

LIBRARY_JSON = Path(__file__).resolve().parent / "library.json"


class GameDialog(tk.Toplevel):
    """加入/編輯單一遊戲：原始資料夾 + 名稱 + 封面（選填）+ RTP（勾選＋資料夾）。回傳 dict 或 None。"""

    def __init__(self, parent, folder="", label="", cover="", rtp="", tags=(),
                 available_tags=()):
        super().__init__(parent)
        self.title("遊戲設定")
        self.result = None
        self.transient(parent)
        self.grab_set()

        self.v_folder = tk.StringVar(value=folder)
        self.v_label = tk.StringVar(value=label)
        self.v_cover = tk.StringVar(value=cover)
        self.v_rtp_on = tk.BooleanVar(value=bool(rtp))
        self.v_rtp = tk.StringVar(value=rtp)
        self.selected_tags = list(tags)

        ttk.Label(self, text="原始資料夾").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(self, textvariable=self.v_folder, width=36).grid(row=0, column=1, padx=4)
        ttk.Button(self, text="…", width=3, command=self._pick_folder).grid(row=0, column=2)
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
        ttk.Label(self, text="標籤").grid(row=5, column=0, sticky="nw", padx=8, pady=(6, 0))
        self.cb_tag = ttk.Combobox(self, values=list(available_tags), width=22)
        self.cb_tag.grid(row=5, column=1, sticky="w", padx=4, pady=(6, 0))
        ttk.Button(self, text="加入標籤", width=8,
                   command=self._add_tag).grid(row=5, column=2, pady=(6, 0))
        self.tag_lb = tk.Listbox(self, height=4, width=34)
        self.tag_lb.grid(row=6, column=1, sticky="w", padx=4)
        ttk.Button(self, text="移除", width=8,
                   command=self._remove_tag).grid(row=6, column=2, sticky="n")
        self._refresh_tag_lb()
        bar = ttk.Frame(self)
        bar.grid(row=7, column=0, columnspan=3, pady=8)
        ttk.Button(bar, text="確定", command=self._ok).pack(side="left", padx=4)
        ttk.Button(bar, text="取消", command=self.destroy).pack(side="left", padx=4)

    def _pick_folder(self):
        d = filedialog.askdirectory(title="選擇遊戲資料夾")
        if d:
            self.v_folder.set(d)
            if not self.v_label.get().strip():
                self.v_label.set(Path(d).name)

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

    def _refresh_tag_lb(self):
        self.tag_lb.delete(0, "end")
        for t in self.selected_tags:
            self.tag_lb.insert("end", t)

    def _add_tag(self):
        # 從下拉選現有標籤，或直接打字新增；加入這個遊戲的已選清單。
        t = self.cb_tag.get().strip()
        if t and t not in self.selected_tags:
            self.selected_tags.append(t)
            self._refresh_tag_lb()
        self.cb_tag.set("")

    def _remove_tag(self):
        # 只把標籤從「這個遊戲」移除，不影響全域標籤清單。
        sel = self.tag_lb.curselection()
        if sel:
            del self.selected_tags[sel[0]]
            self._refresh_tag_lb()

    def _ok(self):
        if not self.v_folder.get().strip():
            messagebox.showerror("缺少資料夾", "請選擇遊戲的原始資料夾", parent=self)
            return
        if not self.v_label.get().strip():
            messagebox.showerror("缺少名稱", "請輸入顯示名稱", parent=self)
            return
        rtp = self.v_rtp.get().strip() if self.v_rtp_on.get() else ""
        self.result = {
            "folder": self.v_folder.get().strip(),
            "label": self.v_label.get().strip(),
            "cover": self.v_cover.get().strip() or None,
            "rtp": rtp or None,
            "tags": list(self.selected_tags),
        }
        self.destroy()


class App:
    def __init__(self, root: tk.Tk, project_path=None):
        self.root = root
        root.title("EasyRPG → 遊戲庫（網頁版/PWA）打包工具")
        self.log_q: queue.Queue = queue.Queue()
        self.project_path = Path(project_path) if project_path else LIBRARY_JSON

        proj, warning = project.load_project(self.project_path)
        self.games: list = [dict(g) for g in proj["games"]]
        self.all_tags: list = list(proj["all_tags"])
        self.new_tag = tk.StringVar()
        self.lib_name = tk.StringVar(value=proj["lib_name"])
        self.icon = tk.StringVar(value=proj["icon"])
        self.soundfont = tk.StringVar(value=proj["soundfont"])
        self.out = tk.StringVar(value=proj["out"])
        self.refresh = tk.BooleanVar(value=False)

        self._build_ui()
        self._refresh_tree()
        self._refresh_tags_list()

        # 初值設定完才掛 trace，避免初始化時誤觸發寫檔
        for var in (self.lib_name, self.icon, self.soundfont, self.out):
            var.trace_add("write", lambda *_: self._save())

        if warning:
            messagebox.showwarning("讀取專案檔", warning)
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

        self.tree = ttk.Treeview(f, columns=("label", "folder", "cover", "rtp", "tags"),
                                 show="headings", height=8)
        for col, txt, w in [("label", "名稱", 130), ("folder", "資料夾", 240),
                            ("cover", "封面", 90), ("rtp", "RTP", 80),
                            ("tags", "標籤", 160)]:
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

        tagmgr = ttk.LabelFrame(f, text="標籤清單（新增可選用的標籤名稱）", padding=6)
        tagmgr.grid(row=3, column=0, sticky="ew", pady=4)
        tagmgr.columnconfigure(0, weight=1)
        self.tags_list = tk.Listbox(tagmgr, height=3)
        self.tags_list.grid(row=0, column=0, rowspan=2, sticky="ew", padx=(0, 6))
        ttk.Entry(tagmgr, textvariable=self.new_tag, width=18).grid(
            row=0, column=1, padx=2, pady=(0, 2))
        ttk.Button(tagmgr, text="新增標籤", command=self._add_tag).grid(row=0, column=2, padx=2)

        opt = ttk.Frame(f)
        opt.grid(row=4, column=0, sticky="w", pady=4)
        ttk.Label(opt, text="音色 SF2").grid(row=0, column=0, padx=4)
        ttk.Entry(opt, textvariable=self.soundfont, width=34).grid(row=0, column=1, padx=4)
        ttk.Button(opt, text="…", width=3,
                   command=lambda: self._pick_file(self.soundfont)).grid(row=0, column=2)
        ttk.Label(opt, text="輸出夾").grid(row=0, column=3, padx=4)
        ttk.Entry(opt, textvariable=self.out, width=14).grid(row=0, column=4, padx=4)

        chk = ttk.Frame(f)
        chk.grid(row=5, column=0, sticky="w")
        ttk.Checkbutton(chk, text="強制更新 web player",
                        variable=self.refresh).pack(side="left", padx=4)

        self.run_btn = ttk.Button(f, text="重建並部署到網頁", command=self._run)
        self.run_btn.grid(row=6, column=0, sticky="w", pady=6)
        self.log = ScrolledText(f, width=78, height=14, state="disabled")
        self.log.grid(row=7, column=0, pady=6)

    def _refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for g in self.games:
            folder = str(g.get("folder") or "")
            folder_disp = folder if folder else "⚠ 待指定"
            cover = Path(g["cover"]).name if g.get("cover") else "（預設）"
            rtp = Path(g["rtp"]).name if g.get("rtp") else "（無）"
            tags = "、".join(g.get("tags") or [])
            self.tree.insert("", "end",
                             values=(g.get("label") or "", folder_disp, cover, rtp, tags))

    def _refresh_tags_list(self):
        self.tags_list.delete(0, "end")
        for t in self.all_tags:
            self.tags_list.insert("end", t)

    def _add_tag(self):
        # 主視窗新增「全域標籤名稱」（不套用到任何遊戲，只是讓它出現在下拉選單可選）。
        t = self.new_tag.get().strip()
        if t and t not in self.all_tags:
            self.all_tags.append(t)
            self._refresh_tags_list()
            self._save()
        self.new_tag.set("")

    def _merge_tags(self, tags):
        # 在遊戲設定裡新打的標籤，自動補進全域清單。
        changed = False
        for t in tags or []:
            if t and t not in self.all_tags:
                self.all_tags.append(t)
                changed = True
        if changed:
            self._refresh_tags_list()

    def _save(self):
        project.save_project(self.project_path, {
            "version": project.VERSION,
            "lib_name": self.lib_name.get(),
            "icon": self.icon.get(),
            "soundfont": self.soundfont.get(),
            "out": self.out.get(),
            "all_tags": list(self.all_tags),
            "games": [
                {"folder": str(g.get("folder") or ""), "label": g.get("label") or "",
                 "cover": g.get("cover") or None, "rtp": g.get("rtp") or None,
                 "tags": list(g.get("tags") or [])}
                for g in self.games
            ],
        })

    def _selected_index(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return self.tree.index(sel[0])

    def _add(self):
        dlg = GameDialog(self.root, available_tags=list(self.all_tags))
        self.root.wait_window(dlg)
        if dlg.result:
            self.games.append(dlg.result)
            self._merge_tags(dlg.result.get("tags"))
            self._refresh_tree()
            self._save()

    def _edit(self):
        i = self._selected_index()
        if i is None:
            return
        g = self.games[i]
        dlg = GameDialog(self.root, str(g.get("folder") or ""), g.get("label") or "",
                         g.get("cover") or "", g.get("rtp") or "",
                         tags=list(g.get("tags") or []),
                         available_tags=list(self.all_tags))
        self.root.wait_window(dlg)
        if dlg.result:
            self.games[i] = dlg.result
            self._merge_tags(dlg.result.get("tags"))
            self._refresh_tree()
            self._save()

    def _remove(self):
        i = self._selected_index()
        if i is None:
            return
        name = self.games[i].get("label") or "這個遊戲"
        if not messagebox.askyesno(
                "移除遊戲",
                f"確定要從清單移除「{name}」嗎？\n（只移除清單，不會刪除遊戲原始資料夾）"):
            return
        del self.games[i]
        self._refresh_tree()
        self._save()

    def _move(self, delta):
        i = self._selected_index()
        if i is None:
            return
        j = i + delta
        if 0 <= j < len(self.games):
            self.games[i], self.games[j] = self.games[j], self.games[i]
            self._refresh_tree()
            self.tree.selection_set(self.tree.get_children()[j])
            self._save()

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
        missing = project.missing_sources(self.games)
        if missing:
            messagebox.showerror(
                "尚未指定原始資料夾",
                "以下遊戲還沒指定有效的原始資料夾（含 RPG_RT.ldb/.lmt），"
                "請先用「編輯」補上再部署：\n\n" + "\n".join("• " + m for m in missing))
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
                deploy=True,
                log=self._emit,
            )
            self._emit(f"✓ 完成並已部署，輸出在：{out}")
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
