# -*- coding: utf-8 -*-
import shutil
import os
import sys
import time
import configparser
from datetime import datetime
import ctypes
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from collections import deque


def refresh_explorer_file(filepath):
    if sys.platform != "win32":
        return
    SHCNE_UPDATEITEM = 0x00002000
    SHCNF_PATH = 0x0005
    ctypes.windll.shell32.SHChangeNotify(SHCNE_UPDATEITEM, SHCNF_PATH, ctypes.c_wchar_p(filepath), None)


def get_app_root():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))


def get_icon_path():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, "app.ico")


class ImageToolApp:
    def __init__(self, root):
        self.root = root
        self.app_dir = get_app_root()
        self.backup_dir = os.path.join(self.app_dir, "wheel_backup")
        self.config_path = os.path.join(self.app_dir, "config.ini")
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

        self.config = configparser.ConfigParser()
        self.lang = "zh"
        if os.path.exists(self.config_path):
            try:
                self.config.read(self.config_path, encoding="utf-8")
                saved_lang = self.config.get("UI", "language", fallback="zh")
                if saved_lang in ["zh", "en"]:
                    self.lang = saved_lang
            except Exception:
                pass

        self.text_data = {
            "zh": {
                "win_title": "SimuCUBE方向盘更换工具",
                "main_title": "SimuCUBE方向盘更换工具",
                "btn_select": "选择图片",
                "btn_confirm": "确定执行替换",
                "scale_text": "缩放比例：",
                "pos_text": "图片位置调整：",
                "btn_center": "居中",
                "btn_reset_scale": "重置缩放(恢复1.0倍+居中)",
                "magic_group": "魔术橡皮擦（仅擦连通白色区域）",
                "magic_check": "启用魔术橡皮擦（点击白色区域，只擦除相连白色，变成透明）",
                "tolerance_text": "白色容差：",
                "btn_undo": "撤销本次擦除",
                "left_preview": "待替换图片(400×400预览)",
                "right_preview": "wheelimage.png(当前)",
                "status_default": "点击【选择图片】按钮进行选择",
                "magic_on": "魔术橡皮擦已启用：点击白色连通区域，擦为透明",
                "magic_off": "魔术橡皮擦已关闭",
                "tip_no_img": "请先选择图片",
                "tip_click_out": "点击位置不在图片区域内",
                "tip_not_white": "点击点不是接近白色，跳过擦除",
                "tip_already_trans": "当前区域已经透明",
                "tip_erase_ok": "已擦除连通白色区域",
                "tip_undo_ok": "已撤销本次擦除",
                "tip_no_undo": "没有可撤销的擦除",
                "tip_no_file": "未选择图片",
                "tip_read_fail": "图片读取失败：{}",
                "tip_selected": "已选中图片，可缩放、移动、启用魔术橡皮擦",
                "tip_backup_ok": "旧文件已备份至 wheel_backup\\{}",
                "tip_replace_ok": "替换完成，已生成400×400 wheelimage.png，可继续调整图片再次替换",
                "msg_title_tip": "提示",
                "msg_title_info": "完成",
                "msg_title_err": "错误",
                "msg_select_first": "请先选择一张图片！",
                "msg_replace_info": "替换完成！\n新wheelimage.png位于程序根目录\n历史备份保存在 wheel_backup 文件夹\n当前图片保留，可继续编辑后再次替换",
                "msg_fail": "操作失败：{}",
                "lang_text": "语言:"
            },
            "en": {
                "win_title": "SimuCUBE Wheel Image Tool",
                "main_title": "SimuCUBE Wheel Image Tool",
                "btn_select": "Select Image",
                "btn_confirm": "Execute Replace",
                "scale_text": "Scale:",
                "pos_text": "Image Position Adjust:",
                "btn_center": "Center",
                "btn_reset_scale": "Reset Scale (1.0x + Center)",
                "magic_group": "Magic Eraser (Only connected white area)",
                "magic_check": "Enable Magic Eraser (Click white area, erase connected white to transparent)",
                "tolerance_text": "Tolerance:",
                "btn_undo": "Undo Erase",
                "left_preview": "Source Image (400×400 Preview)",
                "right_preview": "Current wheelimage.png",
                "status_default": "Click [Select Image] to choose picture",
                "magic_on": "Magic Eraser ON: Click connected white region to make transparent",
                "magic_off": "Magic Eraser OFF",
                "tip_no_img": "Please select an image",
                "tip_click_out": "Click outside image",
                "tip_not_white": "Clicked pixel is not near white, skip erase",
                "tip_already_trans": "This area is already transparent",
                "tip_erase_ok": "Connected white area erased",
                "tip_undo_ok": "Undo erase completed",
                "tip_no_undo": "Nothing to undo",
                "tip_no_file": "No file selected",
                "tip_read_fail": "Image load error: {}",
                "tip_selected": "Image loaded, you can scale, move or use magic eraser",
                "tip_backup_ok": "Old file backed up to wheel_backup\\{}",
                "tip_replace_ok": "Replace done, 400×400 wheelimage.png created. Edit and replace again.",
                "msg_title_tip": "Tip",
                "msg_title_info": "Complete",
                "msg_title_err": "Error",
                "msg_select_first": "Please select an image first!",
                "msg_replace_info": "Replace completed!\nNew wheelimage.png at app root\nBackups stored in wheel_backup folder\nImage remains, you can edit and replace again.",
                "msg_fail": "Failed: {}",
                "lang_text": "Lang:"
            }
        }

        self.root.geometry("1100x940")
        self.root.resizable(True, True)

        icon_fp = get_icon_path()
        if os.path.exists(icon_fp):
            try:
                self.root.iconbitmap(icon_fp)
            except Exception:
                pass

        self.tk_selected = None
        self.tk_wheel = None
        self.selected_src_path = None
        self.original_pil_img = None
        self.erased_pil_img = None

        self.status_var = tk.StringVar(value=self.text_data[self.lang]["status_default"])
        self.scale_var = tk.DoubleVar(value=1.0)
        self.offset_x = tk.IntVar(value=0)
        self.offset_y = tk.IntVar(value=0)
        self.move_step = 1

        self.magic_mode = tk.BooleanVar(value=False)
        self.tolerance_var = tk.IntVar(value=15)

        main_frame = tk.Frame(root, padx=16, pady=16)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ============ 修改布局：语言选择放在右上角，标题放在按钮正上方 ============
        # 语言选择行（右上角）
        lang_top_frame = tk.Frame(main_frame)
        lang_top_frame.pack(fill=tk.X)

        lang_frame = tk.Frame(lang_top_frame)
        lang_frame.pack(side=tk.RIGHT, pady=2)
        self.label_lang_text = tk.Label(lang_frame, text=self.text_data[self.lang]["lang_text"])
        self.label_lang_text.pack(side=tk.LEFT)
        self.cb_lang = ttk.Combobox(lang_frame, values=["中文", "English"], width=10, state="readonly")
        if self.lang == "zh":
            self.cb_lang.set("中文")
        else:
            self.cb_lang.set("English")
        self.cb_lang.pack(side=tk.LEFT, padx=4)
        self.cb_lang.bind("<<ComboboxSelected>>", self.switch_language)

        # 标题框架，放在按钮正上方居中
        title_frame = tk.Frame(main_frame)
        title_frame.pack(pady=(4, 0))
        self.label_main_title = tk.Label(
            title_frame,
            text=self.text_data[self.lang]["main_title"],
            font=("微软雅黑", 18)
        )
        self.label_main_title.pack()

        # 两个按钮所在行
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(pady=10)

        self.btn_select = tk.Button(
            btn_frame,
            text=self.text_data[self.lang]["btn_select"],
            command=self.on_select_file,
            font=("微软雅黑", 12)
        )
        self.btn_select.pack(side=tk.LEFT, padx=8)

        self.btn_confirm = tk.Button(
            btn_frame,
            text=self.text_data[self.lang]["btn_confirm"],
            command=self.on_confirm,
            font=("微软雅黑", 12),
            state=tk.DISABLED,
            bg="#cccccc"
        )
        self.btn_confirm.pack(side=tk.LEFT, padx=8)
        # ======================================================================

        scale_frame = tk.Frame(main_frame)
        scale_frame.pack(pady=8, fill=tk.X)

        self.label_scale_text = tk.Label(
            scale_frame,
            text=self.text_data[self.lang]["scale_text"],
            font=("微软雅黑", 11)
        )
        self.label_scale_text.pack(side=tk.LEFT)

        self.scale_slider = tk.Scale(
            scale_frame,
            from_=0.2,
            to=2.0,
            resolution=0.01,
            orient=tk.HORIZONTAL,
            variable=self.scale_var,
            command=self.on_scale_changed,
            length=600
        )
        self.scale_slider.pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True)

        self.scale_label = tk.Label(
            scale_frame,
            text="1.00x",
            font=("微软雅黑", 11)
        )
        self.scale_label.pack(side=tk.LEFT)

        move_frame = tk.Frame(main_frame)
        move_frame.pack(pady=6)
        self.label_pos_text = tk.Label(move_frame, text=self.text_data[self.lang]["pos_text"], font=("微软雅黑", 11))
        self.label_pos_text.pack(side=tk.LEFT, padx=5)

        row_up = tk.Frame(move_frame)
        row_up.pack()
        tk.Button(row_up, text="↑", width=3, command=self.move_up, font=("微软雅黑", 11)).pack(padx=2)

        row_mid = tk.Frame(move_frame)
        row_mid.pack()
        tk.Button(row_mid, text="←", width=3, command=self.move_left, font=("微软雅黑", 11)).pack(side=tk.LEFT, padx=2)

        # 居中按钮，双语切换
        self.btn_center = tk.Button(
            row_mid,
            text=self.text_data[self.lang]["btn_center"],
            width=5,
            command=self.reset_offset,
            font=("微软雅黑", 11)
        )
        self.btn_center.pack(side=tk.LEFT, padx=2)

        tk.Button(row_mid, text="→", width=3, command=self.move_right, font=("微软雅黑", 11)).pack(side=tk.LEFT, padx=2)

        row_down = tk.Frame(move_frame)
        row_down.pack()
        tk.Button(row_down, text="↓", width=3, command=self.move_down, font=("微软雅黑", 11)).pack(padx=2)

        reset_scale_frame = tk.Frame(main_frame)
        reset_scale_frame.pack(pady=4)
        self.btn_reset_scale = tk.Button(
            reset_scale_frame,
            text=self.text_data[self.lang]["btn_reset_scale"],
            command=self.reset_scale,
            font=("微软雅黑", 11)
        )
        self.btn_reset_scale.pack()

        self.magic_frame = tk.LabelFrame(main_frame, text=self.text_data[self.lang]["magic_group"], padx=8, pady=6)
        self.magic_frame.pack(pady=6, fill=tk.X)

        self.chk_magic = tk.Checkbutton(
            self.magic_frame,
            text=self.text_data[self.lang]["magic_check"],
            variable=self.magic_mode,
            command=self.update_magic_cursor,
            font=("微软雅黑", 11)
        )
        self.chk_magic.pack(side=tk.LEFT)

        self.label_tolerance = tk.Label(self.magic_frame, text=self.text_data[self.lang]["tolerance_text"], font=("微软雅黑", 11))
        self.label_tolerance.pack(side=tk.LEFT, padx=(10, 0))
        self.tolerance_slider = tk.Scale(
            self.magic_frame,
            from_=0,
            to=80,
            resolution=1,
            orient=tk.HORIZONTAL,
            variable=self.tolerance_var,
            length=220
        )
        self.tolerance_slider.pack(side=tk.LEFT, padx=5)
        self.tolerance_label = tk.Label(self.magic_frame, text="15", font=("微软雅黑", 11), width=4)
        self.tolerance_label.pack(side=tk.LEFT)
        self.tolerance_var.trace_add("write", lambda *args: self.tolerance_label.config(text=str(self.tolerance_var.get())))

        self.btn_undo = tk.Button(
            self.magic_frame,
            text=self.text_data[self.lang]["btn_undo"],
            command=self.undo_erase,
            font=("微软雅黑", 11)
        )
        self.btn_undo.pack(side=tk.RIGHT)

        preview_frame = tk.Frame(main_frame)
        preview_frame.pack(pady=12, fill=tk.BOTH, expand=True)

        left_panel = tk.Frame(preview_frame, bd=2, relief=tk.SUNKEN)
        left_panel.pack(side=tk.LEFT, padx=12, fill=tk.BOTH, expand=True)
        self.label_left_preview = tk.Label(left_panel, text=self.text_data[self.lang]["left_preview"], font=("微软雅黑", 11))
        self.label_left_preview.pack(pady=4)

        self.left_canvas = tk.Canvas(left_panel, width=400, height=400, bg="#eeeeee", highlightthickness=0)
        self.left_canvas.pack(padx=4, pady=4)

        self.left_canvas.create_line(0, 200, 400, 200, fill="#00cc00", width=1, tags="guide")
        self.left_canvas.create_line(200, 0, 200, 400, fill="#00cc00", width=1, tags="guide")
        self.left_canvas.create_oval(197, 197, 203, 203, fill="#ffcc00", outline="#ffcc00", tags="guide")
        self.left_canvas.create_rectangle(0, 0, 399, 399, outline="#ffcc00", width=2, tags="guide")

        self.canvas_image_id = None
        self.left_canvas.bind("<Button-1>", self.on_canvas_click)

        right_panel = tk.Frame(preview_frame, bd=2, relief=tk.SUNKEN)
        right_panel.pack(side=tk.LEFT, padx=12, fill=tk.BOTH, expand=True)
        self.label_right_preview = tk.Label(right_panel, text=self.text_data[self.lang]["right_preview"], font=("微软雅黑", 11))
        self.label_right_preview.pack(pady=4)

        self.right_canvas = tk.Canvas(right_panel, width=400, height=400, bg="#eeeeee", highlightthickness=0)
        self.right_canvas.pack(padx=4, pady=4)
        self.right_canvas.create_line(0, 200, 400, 200, fill="#00cc00", width=1, tags="guide")
        self.right_canvas.create_line(200, 0, 200, 400, fill="#00cc00", width=1, tags="guide")
        self.right_canvas.create_oval(197, 197, 203, 203, fill="#ffcc00", outline="#ffcc00", tags="guide")
        self.right_canvas.create_rectangle(0, 0, 399, 399, outline="#00cc00", width=2, tags="guide")

        self.right_image_id = None

        tk.Label(
            main_frame,
            textvariable=self.status_var,
            font=("微软雅黑", 11)
        ).pack(pady=10)

        self.load_wheel_preview()

    def switch_language(self, event):
        sel = self.cb_lang.get()
        if sel == "中文":
            self.lang = "zh"
        else:
            self.lang = "en"
        t = self.text_data[self.lang]
        self.root.title(t["win_title"])
        self.label_main_title.config(text=t["main_title"])
        self.btn_select.config(text=t["btn_select"])
        self.btn_confirm.config(text=t["btn_confirm"])
        self.label_scale_text.config(text=t["scale_text"])
        self.label_pos_text.config(text=t["pos_text"])
        self.btn_center.config(text=t["btn_center"])
        self.btn_reset_scale.config(text=t["btn_reset_scale"])
        self.magic_frame.config(text=t["magic_group"])
        self.chk_magic.config(text=t["magic_check"])
        self.label_tolerance.config(text=t["tolerance_text"])
        self.btn_undo.config(text=t["btn_undo"])
        self.label_left_preview.config(text=t["left_preview"])
        self.label_right_preview.config(text=t["right_preview"])
        self.label_lang_text.config(text=t["lang_text"])
        self.status_var.set(t["status_default"])

        self.config["UI"] = {"language": self.lang}
        with open(self.config_path, "w", encoding="utf-8") as f:
            self.config.write(f)

    def enable_confirm_btn(self):
        if self.erased_pil_img is not None:
            self.btn_confirm.config(state=tk.NORMAL, bg="#7ccd7c")

    def update_magic_cursor(self):
        t = self.text_data[self.lang]
        if self.magic_mode.get():
            self.left_canvas.config(cursor="target")
            self.status_var.set(t["magic_on"])
        else:
            self.left_canvas.config(cursor="")
            self.status_var.set(t["magic_off"])

    def on_canvas_click(self, event):
        if not self.magic_mode.get():
            return
        if self.erased_pil_img is None:
            messagebox.showinfo(self.text_data[self.lang]["msg_title_tip"], self.text_data[self.lang]["tip_no_img"])
            return

        canvas_x = max(0, min(399, event.x))
        canvas_y = max(0, min(399, event.y))

        scale = self.scale_var.get()
        off_x = self.offset_x.get()
        off_y = self.offset_y.get()

        src_w, src_h = self.erased_pil_img.size
        new_w = max(1, int(src_w * scale))
        new_h = max(1, int(src_h * scale))

        base_x = (400 - new_w) // 2
        base_y = (400 - new_h) // 2

        img_x = canvas_x - base_x - off_x
        img_y = canvas_y - base_y - off_y

        if img_x < 0 or img_x >= new_w or img_y < 0 or img_y >= new_h:
            self.status_var.set(self.text_data[self.lang]["tip_click_out"])
            return

        orig_x = int(img_x / scale)
        orig_y = int(img_y / scale)

        self.apply_magic_erase_white(orig_x, orig_y)

    def apply_magic_erase_white(self, click_x, click_y):
        img = self.erased_pil_img
        tolerance = self.tolerance_var.get()
        w, h = img.size
        t = self.text_data[self.lang]
        try:
            r0, g0, b0, a0 = img.getpixel((click_x, click_y))
        except Exception:
            return
        if not (r0 >= 255 - tolerance and g0 >= 255 - tolerance and b0 >= 255 - tolerance):
            self.status_var.set(t["tip_not_white"])
            return
        if a0 == 0:
            self.status_var.set(t["tip_already_trans"])
            return

        from collections import deque
        visited = [[False] * h for _ in range(w)]
        q = deque()
        q.append((click_x, click_y))
        visited[click_x][click_y] = True
        alpha = img.split()[3]
        alpha_data = alpha.load()

        while q:
            x, y = q.popleft()
            r, g, b, a = img.getpixel((x, y))
            if r >= 255 - tolerance and g >= 255 - tolerance and b >= 255 - tolerance:
                alpha_data[x, y] = 0
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and not visited[nx][ny]:
                        visited[nx][ny] = True
                        q.append((nx, ny))
        img.putalpha(alpha)
        self.status_var.set(t["tip_erase_ok"])
        self.update_selected_preview()
        self.enable_confirm_btn()

    def undo_erase(self):
        t = self.text_data[self.lang]
        if self.original_pil_img is None:
            messagebox.showinfo(t["msg_title_tip"], t["tip_no_undo"])
            return
        self.erased_pil_img = self.original_pil_img.copy()
        self.status_var.set(t["tip_undo_ok"])
        self.update_selected_preview()
        self.enable_confirm_btn()

    def move_up(self):
        self.offset_y.set(self.offset_y.get() - self.move_step)
        self.update_selected_preview()
        self.enable_confirm_btn()

    def move_down(self):
        self.offset_y.set(self.offset_y.get() + self.move_step)
        self.update_selected_preview()
        self.enable_confirm_btn()

    def move_left(self):
        self.offset_x.set(self.offset_x.get() - self.move_step)
        self.update_selected_preview()
        self.enable_confirm_btn()

    def move_right(self):
        self.offset_x.set(self.offset_x.get() + self.move_step)
        self.update_selected_preview()
        self.enable_confirm_btn()

    def reset_offset(self):
        self.offset_x.set(0)
        self.offset_y.set(0)
        self.update_selected_preview()
        self.enable_confirm_btn()

    def reset_scale(self):
        self.scale_var.set(1.0)
        self.scale_label.config(text="1.00x")
        self.offset_x.set(0)
        self.offset_y.set(0)
        self.update_selected_preview()
        self.enable_confirm_btn()

    def on_scale_changed(self, value):
        scale = float(value)
        self.scale_label.config(text=f"{scale:.2f}x")
        self.update_selected_preview()
        self.enable_confirm_btn()

    def update_selected_preview(self):
        if self.erased_pil_img is None:
            return

        scale = self.scale_var.get()
        off_x = self.offset_x.get()
        off_y = self.offset_y.get()

        src_w, src_h = self.erased_pil_img.size
        new_w = max(1, int(src_w * scale))
        new_h = max(1, int(src_h * scale))
        scaled_img = self.erased_pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        preview_canvas = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
        base_x = (400 - new_w) // 2
        base_y = (400 - new_h) // 2
        paste_x = base_x + off_x
        paste_y = base_y + off_y
        preview_canvas.paste(scaled_img, (paste_x, paste_y), mask=scaled_img)

        self.tk_selected = ImageTk.PhotoImage(preview_canvas)

        if self.canvas_image_id is None:
            self.canvas_image_id = self.left_canvas.create_image(
                0, 0, anchor=tk.NW, image=self.tk_selected
            )
            self.left_canvas.tag_raise("guide")
        else:
            self.left_canvas.itemconfig(self.canvas_image_id, image=self.tk_selected)
        self.left_canvas.image = self.tk_selected

    def load_wheel_preview(self):
        if self.right_image_id is not None:
            self.right_canvas.delete(self.right_image_id)
            self.right_image_id = None
        self.tk_wheel = None

        target = os.path.join(self.app_dir, "wheelimage.png")
        if os.path.exists(target):
            try:
                with Image.open(target) as im:
                    im.load()
                    im = im.convert("RGBA")
                    bg = Image.new("RGBA", (400, 400), (238, 238, 238, 255))
                    im.thumbnail((400, 400), Image.Resampling.LANCZOS)
                    x = (400 - im.width) // 2
                    y = (400 - im.height) // 2
                    bg.paste(im, (x, y), mask=im)

                    self.tk_wheel = ImageTk.PhotoImage(bg)
                    self.right_image_id = self.right_canvas.create_image(
                        0, 0, anchor=tk.NW, image=self.tk_wheel
                    )
                    self.right_canvas.tag_raise("guide")
            except Exception as e:
                print(f"右侧预览加载异常:{e}")
                self.tk_wheel = None
        else:
            self.tk_wheel = None

    def on_select_file(self):
        filetypes = [
            ("所有图片文件", "*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.tiff"),
            ("PNG", "*.png"),
            ("JPG/JPEG", "*.jpg;*.jpeg"),
            ("BMP", "*.bmp"),
            ("GIF", "*.gif"),
            ("全部文件", "*.*")
        ]
        src = filedialog.askopenfilename(
            title="选择图片",
            filetypes=filetypes
        )
        t = self.text_data[self.lang]
        if not src:
            self.status_var.set(t["tip_no_file"])
            self.selected_src_path = None
            self.original_pil_img = None
            self.erased_pil_img = None
            self.btn_confirm.config(state=tk.DISABLED, bg="#cccccc")
            return

        try:
            self.original_pil_img = Image.open(src).convert("RGBA")
            self.erased_pil_img = self.original_pil_img.copy()
            self.selected_src_path = src
            self.scale_var.set(1.0)
            self.scale_label.config(text="1.00x")
            self.offset_x.set(0)
            self.offset_y.set(0)
            self.magic_mode.set(False)
            self.left_canvas.config(cursor="")
            self.update_selected_preview()
            self.btn_confirm.config(state=tk.NORMAL, bg="#7ccd7c")
            self.status_var.set(t["tip_selected"])
        except Exception as e:
            self.selected_src_path = None
            self.original_pil_img = None
            self.erased_pil_img = None
            self.btn_confirm.config(state=tk.DISABLED, bg="#cccccc")
            self.status_var.set(t["tip_read_fail"].format(e))

    def on_confirm(self):
        t = self.text_data[self.lang]
        if self.erased_pil_img is None:
            messagebox.showwarning(t["msg_title_tip"], t["msg_select_first"])
            return

        target_file = os.path.join(self.app_dir, "wheelimage.png")

        try:
            if os.path.exists(target_file):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_filename = f"wheelimage_backup_{timestamp}.png"
                backup_full_path = os.path.join(self.backup_dir, backup_filename)
                shutil.move(target_file, backup_full_path)
                self.status_var.set(t["tip_backup_ok"].format(backup_filename))

            scale = self.scale_var.get()
            off_x = self.offset_x.get()
            off_y = self.offset_y.get()

            src_w, src_h = self.erased_pil_img.size
            new_w = max(1, int(src_w * scale))
            new_h = max(1, int(src_h * scale))

            scaled_img = self.erased_pil_img.resize(
                (new_w, new_h),
                Image.Resampling.LANCZOS
            )

            final_img = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
            base_x = (400 - new_w) // 2
            base_y = (400 - new_h) // 2
            paste_x = base_x + off_x
            paste_y = base_y + off_y
            final_img.paste(scaled_img, (paste_x, paste_y), mask=scaled_img)
            final_img.save(target_file, format="PNG")

            time.sleep(0.1)
            refresh_explorer_file(target_file)

            self.status_var.set(t["tip_replace_ok"])
            messagebox.showinfo(t["msg_title_info"], t["msg_replace_info"])
            self.load_wheel_preview()

        except Exception as e:
            self.status_var.set(t["msg_fail"].format(e))
            messagebox.showerror(t["msg_title_err"], str(e))


if __name__ == "__main__":
    window = tk.Tk()
    app = ImageToolApp(window)
    window.mainloop()