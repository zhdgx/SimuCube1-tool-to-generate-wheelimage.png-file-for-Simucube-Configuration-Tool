# -*- coding: utf-8 -*-
import shutil
import os
import sys
import time
from datetime import datetime
import ctypes
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from collections import deque


def refresh_explorer_file(filepath):
    if sys.platform != "win32":
        return
    SHCNE_UPDATEITEM = 0x00002000
    SHCNF_PATH = 0x0005
    ctypes.windll.shell32.SHChangeNotify(SHCNE_UPDATEITEM, SHCNF_PATH, filepath, None)


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
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

        self.root.title("SimuCUBE方向盘更换工具")
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

        self.status_var = tk.StringVar(value="点击【选择图片】按钮进行选择")
        self.scale_var = tk.DoubleVar(value=1.0)
        self.offset_x = tk.IntVar(value=0)
        self.offset_y = tk.IntVar(value=0)
        self.move_step = 1

        self.magic_mode = tk.BooleanVar(value=False)
        self.tolerance_var = tk.IntVar(value=15)

        main_frame = tk.Frame(root, padx=16, pady=16)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            main_frame,
            text="SimuCUBE方向盘更换工具",
            font=("微软雅黑", 18)
        ).pack(pady=8)

        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(pady=10)

        self.btn_select = tk.Button(
            btn_frame,
            text="选择图片",
            command=self.on_select_file,
            font=("微软雅黑", 12)
        )
        self.btn_select.pack(side=tk.LEFT, padx=8)

        self.btn_confirm = tk.Button(
            btn_frame,
            text="确定执行替换",
            command=self.on_confirm,
            font=("微软雅黑", 12),
            state=tk.DISABLED,
            bg="#cccccc"
        )
        self.btn_confirm.pack(side=tk.LEFT, padx=8)

        tk.Button(
            btn_frame,
            text="刷新预览",
            command=self.load_wheel_preview,
            font=("微软雅黑", 12)
        ).pack(side=tk.LEFT, padx=8)

        scale_frame = tk.Frame(main_frame)
        scale_frame.pack(pady=8, fill=tk.X)

        tk.Label(
            scale_frame,
            text="缩放比例：",
            font=("微软雅黑", 11)
        ).pack(side=tk.LEFT)

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
        tk.Label(move_frame, text="图片位置调整：", font=("微软雅黑", 11)).pack(side=tk.LEFT, padx=5)

        row_up = tk.Frame(move_frame)
        row_up.pack()
        tk.Button(row_up, text="↑", width=3, command=self.move_up, font=("微软雅黑", 11)).pack(padx=2)

        row_mid = tk.Frame(move_frame)
        row_mid.pack()
        tk.Button(row_mid, text="←", width=3, command=self.move_left, font=("微软雅黑", 11)).pack(side=tk.LEFT, padx=2)
        tk.Button(row_mid, text="居中", width=5, command=self.reset_offset, font=("微软雅黑", 11)).pack(side=tk.LEFT, padx=2)
        tk.Button(row_mid, text="→", width=3, command=self.move_right, font=("微软雅黑", 11)).pack(side=tk.LEFT, padx=2)

        row_down = tk.Frame(move_frame)
        row_down.pack()
        tk.Button(row_down, text="↓", width=3, command=self.move_down, font=("微软雅黑", 11)).pack(padx=2)

        reset_scale_frame = tk.Frame(main_frame)
        reset_scale_frame.pack(pady=4)
        tk.Button(
            reset_scale_frame,
            text="重置缩放(恢复1.0倍+居中)",
            command=self.reset_scale,
            font=("微软雅黑", 11)
        ).pack()

        magic_frame = tk.LabelFrame(main_frame, text="魔术橡皮擦（仅擦连通白色区域）", padx=8, pady=6)
        magic_frame.pack(pady=6, fill=tk.X)

        tk.Checkbutton(
            magic_frame,
            text="启用魔术橡皮擦（点击白色区域，只擦除相连白色，变成透明）",
            variable=self.magic_mode,
            command=self.update_magic_cursor,
            font=("微软雅黑", 11)
        ).pack(side=tk.LEFT)

        tk.Label(magic_frame, text="白色容差：", font=("微软雅黑", 11)).pack(side=tk.LEFT, padx=(10, 0))
        self.tolerance_slider = tk.Scale(
            magic_frame,
            from_=0,
            to=80,
            resolution=1,
            orient=tk.HORIZONTAL,
            variable=self.tolerance_var,
            length=220
        )
        self.tolerance_slider.pack(side=tk.LEFT, padx=5)
        self.tolerance_label = tk.Label(magic_frame, text="15", font=("微软雅黑", 11), width=4)
        self.tolerance_label.pack(side=tk.LEFT)
        self.tolerance_var.trace_add("write", lambda *args: self.tolerance_label.config(text=str(self.tolerance_var.get())))

        tk.Button(
            magic_frame,
            text="撤销本次擦除",
            command=self.undo_erase,
            font=("微软雅黑", 11)
        ).pack(side=tk.RIGHT)

        preview_frame = tk.Frame(main_frame)
        preview_frame.pack(pady=12, fill=tk.BOTH, expand=True)

        # 左侧预览画布
        left_panel = tk.Frame(preview_frame, bd=2, relief=tk.SUNKEN)
        left_panel.pack(side=tk.LEFT, padx=12, fill=tk.BOTH, expand=True)
        tk.Label(left_panel, text="待替换图片(400×400预览)", font=("微软雅黑", 11)).pack(pady=4)

        self.left_canvas = tk.Canvas(left_panel, width=400, height=400, bg="#eeeeee", highlightthickness=0)
        self.left_canvas.pack(padx=4, pady=4)

        self.left_canvas.create_line(0, 200, 400, 200, fill="#00cc00", width=1, tags="guide")
        self.left_canvas.create_line(200, 0, 200, 400, fill="#00cc00", width=1, tags="guide")
        self.left_canvas.create_oval(197, 197, 203, 203, fill="#ffcc00", outline="#ffcc00", tags="guide")
        self.left_canvas.create_rectangle(0, 0, 399, 399, outline="#ffcc00", width=2, tags="guide")

        self.canvas_image_id = None
        self.left_canvas.bind("<Button-1>", self.on_canvas_click)

        # 右侧预览画布
        right_panel = tk.Frame(preview_frame, bd=2, relief=tk.SUNKEN)
        right_panel.pack(side=tk.LEFT, padx=12, fill=tk.BOTH, expand=True)
        tk.Label(right_panel, text="wheelimage.png(当前)", font=("微软雅黑", 11)).pack(pady=4)

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

    # ==========工具函数：启用确认按钮==========
    def enable_confirm_btn(self):
        if self.erased_pil_img is not None:
            self.btn_confirm.config(state=tk.NORMAL, bg="#7ccd7c")

    def update_magic_cursor(self):
        if self.magic_mode.get():
            self.left_canvas.config(cursor="target")
            self.status_var.set("魔术橡皮擦已启用：点击白色连通区域，擦为透明")
        else:
            self.left_canvas.config(cursor="")
            self.status_var.set("魔术橡皮擦已关闭")

    def on_canvas_click(self, event):
        if not self.magic_mode.get():
            return
        if self.erased_pil_img is None:
            messagebox.showinfo("提示", "请先选择图片")
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
            self.status_var.set("点击位置不在图片区域内")
            return

        orig_x = int(img_x / scale)
        orig_y = int(img_y / scale)

        self.apply_magic_erase_white(orig_x, orig_y)

    def apply_magic_erase_white(self, click_x, click_y):
        """BFS泛洪填充，擦除连通近似白色区域为透明，全Pillow兼容"""
        img = self.erased_pil_img
        tolerance = self.tolerance_var.get()
        w, h = img.size
        try:
            r0, g0, b0, a0 = img.getpixel((click_x, click_y))
        except Exception:
            return
        if not (r0 >= 255 - tolerance and g0 >= 255 - tolerance and b0 >= 255 - tolerance):
            self.status_var.set("点击点不是接近白色，跳过擦除")
            return
        if a0 == 0:
            self.status_var.set("当前区域已经透明")
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
        self.status_var.set("已擦除连通白色区域")
        self.update_selected_preview()
        self.enable_confirm_btn() #擦除后，重新启用确认按钮

    def undo_erase(self):
        if self.original_pil_img is None:
            messagebox.showinfo("提示", "没有可撤销的擦除")
            return
        self.erased_pil_img = self.original_pil_img.copy()
        self.status_var.set("已撤销本次擦除")
        self.update_selected_preview()
        self.enable_confirm_btn() #撤销后启用确认按钮

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

        if not src:
            self.status_var.set("未选择图片")
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
            self.status_var.set("已选中图片，可缩放、移动、启用魔术橡皮擦")
        except Exception as e:
            self.selected_src_path = None
            self.original_pil_img = None
            self.erased_pil_img = None
            self.btn_confirm.config(state=tk.DISABLED, bg="#cccccc")
            self.status_var.set(f"图片读取失败：{e}")

    def on_confirm(self):
        if self.erased_pil_img is None:
            messagebox.showwarning("提示", "请先选择一张图片！")
            return

        target_file = os.path.join(self.app_dir, "wheelimage.png")

        try:
            if os.path.exists(target_file):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_filename = f"wheelimage_backup_{timestamp}.png"
                backup_full_path = os.path.join(self.backup_dir, backup_filename)
                shutil.move(target_file, backup_full_path)
                refresh_explorer_file(backup_full_path)
                self.status_var.set(f"旧文件已备份至 wheel_backup\\{backup_filename}")

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

            self.status_var.set("替换完成，已生成400×400 wheelimage.png，可继续调整图片再次替换")
            messagebox.showinfo(
                "完成",
                "替换完成！\n新wheelimage.png位于程序根目录\n历史备份保存在 wheel_backup 文件夹\n当前图片保留，可继续编辑后再次替换"
            )
            self.load_wheel_preview()

            # =========【重点改动】注释掉清空图片的代码，图片保留，不重置 =========
            # self.selected_src_path = None
            # self.original_pil_img = None
            # self.erased_pil_img = None
            # self.btn_confirm.config(state=tk.DISABLED, bg="#cccccc")

        except Exception as e:
            self.status_var.set(f"操作失败：{e}")
            messagebox.showerror("错误", str(e))


if __name__ == "__main__":
    window = tk.Tk()
    app = ImageToolApp(window)
    window.mainloop()