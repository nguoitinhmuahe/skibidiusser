import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os, json, datetime
import tkinter as tk
import time

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

ITEM_FILE = "items.json"
BILL_DIR = "bills"
HISTORY_FILE = "history.txt"

class CurrencyCTkEntry(ctk.CTkEntry):
    def __init__(self, master=None, **kwargs):
        self.var = tk.StringVar()
        super().__init__(master, textvariable=self.var, **kwargs)
        self.var.set("0")
        self.bind("<KeyRelease>", self.on_key_release)
        self.bind("<Button-1>", self.allow_cursor_move)
        self.cursor_locked = True
        self.last_key_time = time.time()
        self.after(200, self.check_format_timeout)

    def format_number(self, value):
        digits = ''.join(filter(str.isdigit, value))
        if not digits:
            return "0"
        return "{:,}".format(int(digits))

    def on_key_release(self, event):
        self.last_key_time = time.time()
        return "break"

    def check_format_timeout(self):
        if time.time() - self.last_key_time > 0.5:
            raw = ''.join(filter(str.isdigit, self.var.get()))
            formatted = self.format_number(raw)
            self.var.set(formatted)
            if self.cursor_locked:
                self.icursor(tk.END)
        self.after(200, self.check_format_timeout)

    def allow_cursor_move(self, event):
        self.cursor_locked = False
        self.after(100, self.relock_cursor)

    def relock_cursor(self):
        self.cursor_locked = True

    def get_raw(self):
        return ''.join(filter(str.isdigit, self.var.get()))

class Item:
    def __init__(self, name, price, image_path):
        self.name = name
        self.price = float(price)
        self.image_path = image_path

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("💰 App Tính Tiền Nhanh")
        self.after(100, lambda: self.state("zoomed"))

        os.makedirs(BILL_DIR, exist_ok=True)

        self.items = []
        self.cart = {}
        self.bill_count = 1
        self.selected_item = None
        self.selected_item_frame = None
        self.click_count = {}

        self.load_items()

        # Tabs
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)

        self.menu_tab = self.tab_view.add("📋 Menu")
        self.credit_tab = self.tab_view.add("🎁 Credit")

        self.setup_menu_tab()
        self.setup_credit_tab()

    def setup_menu_tab(self):
        left_frame = ctk.CTkFrame(self.menu_tab, width=300)
        left_frame.pack(side="left", fill="y", padx=10, pady=10)

        right_frame = ctk.CTkFrame(self.menu_tab)
        right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.menu_frame = ctk.CTkScrollableFrame(right_frame)
        self.menu_frame.pack(fill="both", expand=True, pady=10)

        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(left_frame, placeholder_text="🔍 Tìm hàng...", textvariable=self.search_var)
        self.search_entry.pack(padx=10, pady=(10, 5), fill="x")
        self.search_entry.bind("<KeyRelease>", self.update_menu)

        ctk.CTkButton(left_frame, text="➕ Thêm hàng", command=self.open_add_window).pack(padx=10, pady=2, fill="x")
        ctk.CTkButton(left_frame, text="Cập nhật hàng", command=self.open_update_window).pack(padx=10, pady=2, fill="x")
        ctk.CTkButton(left_frame, text="📊 Tổng kết hôm nay", command=self.export_summary).pack(padx=10, pady=10, fill="x")

        ctk.CTkLabel(left_frame, text="🛒 Giỏ hàng", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(5, 2))

        self.cart_frame = ctk.CTkScrollableFrame(left_frame, height=350)
        self.cart_frame.pack(padx=10, pady=5, fill="both", expand=True)

        self.total_label = ctk.CTkLabel(left_frame, text="💵 Tổng: 0đ", font=ctk.CTkFont(size=14, weight="bold"))
        self.total_label.pack(pady=(5, 2))

        ctk.CTkButton(left_frame, text="✅ Thanh toán", command=self.checkout).pack(padx=10, pady=(5, 10), fill="x")

        self.update_menu()

    def setup_credit_tab(self):
        frame = ctk.CTkFrame(self.credit_tab)
        frame.pack(pady=20, padx=20, fill="both", expand=True)

        try:
            image = Image.open("donate.png").resize((500, 500))
            donate_img = ImageTk.PhotoImage(image)
        except:
            donate_img = ImageTk.PhotoImage(Image.new("RGB", (200, 200), "gray"))

        img_label = ctk.CTkLabel(frame, image=donate_img, text="")
        img_label.image = donate_img
        img_label.pack(side="left", padx=20)

        info = [
            "👤 Tạo bởi - nguoitinhmuahe0000.",
            "📘 Facebook - TranThang",
            "💬 Discord - nguoitinhmuahe0000.#0",
            "",
            "❤️ Nếu Bạn Ưng Ý Thì Có Thể Donate Cho Mình Tí Tiền Cơm Cháo <3",
            "",
            "📩 Nếu Bạn Muốn Mình Làm Thêm App Gì Đó Đơn Giản Hãy Liên Hệ Discord, Facebook Nhé",
            "🔗 Link Facebook: https://www.facebook.com/profile.php?id=61572313778082"
        ]
        label = ctk.CTkLabel(frame, text="\n".join(info), justify="left", anchor="w", font=ctk.CTkFont(size=14))
        label.pack(side="left", fill="both", expand=True)

    def load_items(self):
        if os.path.exists(ITEM_FILE):
            with open(ITEM_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for d in data:
                    self.items.append(Item(d["name"], d["price"], d["image_path"]))

    def save_items(self):
        with open(ITEM_FILE, "w", encoding="utf-8") as f:
            json.dump([vars(i) for i in self.items], f, ensure_ascii=False, indent=2)

    def update_menu(self, *args):
        for widget in self.menu_frame.winfo_children():
            widget.destroy()
        query = self.search_var.get().lower()
        for item in self.items:
            if query in item.name.lower():
                self.create_item_card(item)

    def create_item_card(self, item: Item):
        frame = ctk.CTkFrame(self.menu_frame, border_width=2, border_color="gray")
        frame.pack(fill="x", pady=5, padx=10)

        try:
            img = Image.open(item.image_path).resize((64, 64))
            photo = ImageTk.PhotoImage(img)
        except:
            photo = ImageTk.PhotoImage(Image.new("RGB", (64, 64), "gray"))

        label_img = ctk.CTkLabel(frame, image=photo, text="")
        label_img.image = photo
        label_img.pack(side="left", padx=5)

        text = f"{item.name}\n{item.price:,.0f}đ"
        label = ctk.CTkLabel(frame, text=text, anchor="w", justify="left")
        label.pack(side="left", fill="x", expand=True)

        def select():
            if self.selected_item_frame:
                self.selected_item_frame.configure(border_color="gray")
            self.selected_item_frame = frame
            frame.configure(border_color="green")
            self.selected_item = item

            self.click_count[item.name] = self.click_count.get(item.name, 0) + 1
            if self.click_count[item.name] == 2:
                self.add_to_cart(item)
                self.click_count[item.name] = 0

        frame.bind("<Button-1>", lambda e: select())
        label.bind("<Button-1>", lambda e: select())
        label_img.bind("<Button-1>", lambda e: select())

    def add_to_cart(self, item: Item):
        if item.name in self.cart:
            self.cart[item.name]["qty"] += 1
        else:
            self.cart[item.name] = {"item": item, "qty": 1}
        self.update_cart_display()

    def update_cart_display(self):
        for widget in self.cart_frame.winfo_children():
            widget.destroy()

        total = 0
        for name, info in self.cart.items():
            item = info["item"]
            qty = info["qty"]
            item_total = item.price * qty
            total += item_total

            row = ctk.CTkFrame(self.cart_frame)
            row.pack(fill="x", pady=4, padx=5)

            name_label = ctk.CTkLabel(row, text=item.name, width=100, anchor="w")
            name_label.grid(row=0, column=0, rowspan=3, padx=5, sticky="w")

            btn_add = ctk.CTkButton(row, text="+", width=30, height=20,
                                     command=lambda n=name: self.change_qty(n, 1))
            btn_add.grid(row=0, column=1, pady=2)

            qty_var = ctk.StringVar(value=str(qty))

            def update_qty(event=None, item_name=name, var=qty_var):
                val = var.get()
                if val.isdigit():
                    self.cart[item_name]["qty"] = int(val)
                    if self.cart[item_name]["qty"] <= 0:
                        del self.cart[item_name]
                    self.update_cart_display()

            qty_entry = ctk.CTkEntry(row, textvariable=qty_var, width=40, justify="center")
            qty_entry.grid(row=1, column=1)
            qty_entry.bind("<Return>", update_qty)

            btn_sub = ctk.CTkButton(row, text="-", width=30, height=20,
                                     command=lambda n=name: self.change_qty(n, -1))
            btn_sub.grid(row=2, column=1, pady=2)

            btn_del = ctk.CTkButton(row, text="❌", width=30, height=20, fg_color="red",
                                     command=lambda n=name: self.remove_item(n))
            btn_del.grid(row=1, column=2, padx=5)

        self.total_label.configure(text=f"💵 Tổng: {total:,.0f}đ")

    def change_qty(self, name, delta):
        if name in self.cart:
            self.cart[name]["qty"] += delta
            if self.cart[name]["qty"] <= 0:
                del self.cart[name]
            self.update_cart_display()

    def remove_item(self, name):
        if name in self.cart:
            del self.cart[name]
            self.update_cart_display()

    def open_add_window(self):
        self.open_item_window(is_update=False)

    def open_update_window(self):
        if not self.selected_item:
            messagebox.showinfo("Thông báo", "❗ Chọn hàng cần sửa bằng cách bấm vào thẻ hàng.")
            return
        self.open_item_window(is_update=True)

    def open_item_window(self, is_update=False):
        win = ctk.CTkToplevel(self)
        win.title("Cập nhật hàng" if is_update else "Thêm hàng")
        win.geometry("300x400")
        win.grab_set()

        name_var = ctk.StringVar()
        price_var = tk.StringVar()
        image_path = ctk.StringVar()

        if is_update:
            name_var.set(self.selected_item.name)
            price_var.set(f"{int(self.selected_item.price):,}")
            image_path.set(self.selected_item.image_path)

        ctk.CTkLabel(win, text="Tên hàng:").pack(pady=(10, 0))
        name_entry = ctk.CTkEntry(win, textvariable=name_var)
        name_entry.pack(pady=5)

        ctk.CTkLabel(win, text="Giá tiền:").pack(pady=(10, 0))
        price_entry = CurrencyCTkEntry(win)
        price_entry.var = price_var
        price_entry.configure(textvariable=price_var)
        price_entry.pack(pady=5)

        img_label = ctk.CTkLabel(win, text="(Ảnh hiện tại)")
        img_label.pack(pady=5)

        def show_preview(path):
            try:
                img = Image.open(path).resize((100, 100))
                thumb = ImageTk.PhotoImage(img)
                img_label.configure(image=thumb, text="")
                img_label.image = thumb
            except:
                pass

        if is_update:
            show_preview(image_path.get())

        def choose_image():
            path = filedialog.askopenfilename(filetypes=[("Ảnh", "*.png *.jpg *.jpeg")])
            if path:
                image_path.set(path)
                show_preview(path)

        ctk.CTkButton(win, text="📷 Chọn ảnh", command=choose_image).pack(pady=10)

        def save_item():
            try:
                raw_price = price_entry.get_raw()
                if is_update:
                    self.selected_item.name = name_var.get()
                    self.selected_item.price = float(raw_price)
                    self.selected_item.image_path = image_path.get()
                else:
                    new_item = Item(name_var.get(), float(raw_price), image_path.get())
                    self.items.append(new_item)
                self.update_menu()
                self.save_items()
                win.destroy()
            except:
                messagebox.showerror("Lỗi", "Vui lòng nhập tên và giá hợp lệ!")

        ctk.CTkButton(win, text="💾 Lưu", command=save_item).pack(pady=10)

    def checkout(self):
        if not self.cart:
            messagebox.showinfo("Thông báo", "🛒 Giỏ hàng trống!")
            return

        now = datetime.datetime.now()
        hour = now.strftime("%I_%M%p").lstrip("0")
        date = f"{now.day}_{now.month}_{now.year}"

        filename = f"{hour}_{date}_b{self.bill_count}.txt"
        self.bill_count += 1

        total = 0
        lines = []
        for name, info in self.cart.items():
            line = f"{name} x{info['qty']} - {info['item'].price * info['qty']:,.0f}đ"
            total += info['item'].price * info['qty']
            lines.append(line)

        messagebox.showinfo("🧾 Hóa đơn", "\n".join(lines) + f"\n\n💰 Tổng: {total:,.0f}đ")

        with open(os.path.join(BILL_DIR, filename), "w", encoding="utf-8") as f:
            f.write("===== HÓA ĐƠN =====\n")
            f.write("\n".join(lines))
            f.write(f"\n\nTỔNG: {total:,.0f}đ\n")

        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(f"{now.hour % 12 or 12}:{now.minute:02d} {'AM' if now.hour < 12 else 'PM'} {now.day}/{now.month}/{now.year}\n")
            for name, info in self.cart.items():
                f.write(f"{name} | {info['qty']} | tổng: {int(info['qty']*info['item'].price):,}đ\n")
            f.write("\n")

        self.cart.clear()
        self.update_cart_display()

    def export_summary(self):
        confirm = messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xuất tổng kết hôm nay không?")
        if not confirm: return
        confirm2 = messagebox.askyesno("Xác nhận lại", "Xác nhận lần 2. Tiếp tục?")
        if not confirm2: return

        now = datetime.datetime.now()
        today = f"{now.day}_{now.month}_{now.year}"
        out_path = f"tongket_{today}.txt"
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = f.readlines()

            with open(out_path, "w", encoding="utf-8") as out:
                out.writelines(data)

            messagebox.showinfo("Thành công", f"Đã xuất tổng kết: {out_path}")
        else:
            messagebox.showwarning("Lỗi", "Không tìm thấy lịch sử để xuất.")

if __name__ == "__main__":
    app = App()
    app.mainloop()
