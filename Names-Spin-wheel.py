import tkinter as tk
import json, math, random, os

NAMES_FILE = "Names.json"
SETTINGS_FILE = "Names-Settings.json"

DEFAULT_NAMES = ["SETH","CHAD"]
DEFAULT_SETTINGS = {"theme": "Dark","themes": {"Light":{"bg":"#777777","fg":"#000000","wheel_colors":["#FF9999","#99CCFF","#99FF99","#FFCC99","#CC99FF"]},"Dark":{"bg":"#2b2b2b","fg":"#ffffff","wheel_colors":["#d32f2f","#1976d2","#388e3c","#f57c00","#7b1fa2"]},"Hacker":{"bg":"#000000","fg":"#00ff00","wheel_colors":["#003300","#004400","#005500","#006600","#007700"]}}}

class SpinningWheelApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Who Has To...")
        self.root.geometry("600x650")
        self.names = self.load_json(NAMES_FILE, DEFAULT_NAMES)
        self.settings = self.load_json(SETTINGS_FILE, DEFAULT_SETTINGS)
        self.current_angle = 0.0
        self.speed = 0.0
        self.is_spinning = False
        self.setup_menu()
        self.setup_canvas()
        self.apply_theme()
        
    def load_json(self, filepath, default_data):
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                json.dump(default_data, f, indent=4)
            return default_data
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return default_data

    def save_json(self, filepath, data):
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)

    def setup_menu(self):
        menubar = tk.Menu(self.root)
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Names", command=self.open_edit_names_menu)
        edit_menu.add_command(label="Theme", command=self.open_theme_menu)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        self.root.config(menu=menubar)

    def setup_canvas(self):
        self.canvas = tk.Canvas(self.root, width=500, height=500, highlightthickness=0)
        self.canvas.pack(pady=20)
        self.spin_btn = tk.Button(self.root, text="SPIN THE WHEEL", font=("Helvetica", 16, "bold"), command=self.start_spin)
        self.spin_btn.pack(pady=10)
        self.winner_label = tk.Label(self.root, text="", font=("Helvetica", 18, "bold"))
        self.winner_label.pack()

    def apply_theme(self):
        theme_name = self.settings.get("theme", "Light")
        theme_data = self.settings["themes"][theme_name]
        self.root.config(bg=theme_data["bg"])
        self.canvas.config(bg=theme_data["bg"])
        self.winner_label.config(bg=theme_data["bg"], fg=theme_data["fg"])
        self.draw_wheel()

    def draw_wheel(self):
        self.canvas.delete("all")
        if not self.names:
            self.canvas.create_text(250, 250, text="Add names to spin!", font=("Arial", 16))
            return

        num_names = len(self.names)
        arc_angle = 360 / num_names
        theme_name = self.settings.get("theme", "Light")
        colors = self.settings["themes"][theme_name]["wheel_colors"]
        
        cx, cy, r = 250, 250, 200
        
        for i, name in enumerate(self.names):
            start = (self.current_angle + i * arc_angle) % 360
            color = colors[i % len(colors)]
            
            # Draw slice
            self.canvas.create_arc(
                cx - r, cy - r, cx + r, cy + r,
                start=start, extent=arc_angle, fill=color, outline="black", width=2
            )
            
            # Draw text
            mid_angle = math.radians(start + arc_angle / 2)
            # Adjusting for tkinter's canvas coordinates (Y is down)
            tx = cx + (r * 0.6) * math.cos(mid_angle)
            ty = cy - (r * 0.6) * math.sin(mid_angle)
            
            self.canvas.create_text(tx, ty, text=name, font=("Arial", 12, "bold"), angle=math.degrees(mid_angle))

        # Draw Pointer (Fixed at 0 degrees / Right Side)
        self.canvas.create_polygon(cx + r - 10, cy - 15, cx + r + 20, cy, cx + r - 10, cy + 15, fill="black")

    def start_spin(self):
        if self.is_spinning or not self.names:
            return
        self.is_spinning = True
        self.winner_label.config(text="")
        # Random initial velocity determines both speed and total distance
        self.speed = random.uniform(18.0, 28.0) 
        self.animate_wheel()

    def animate_wheel(self):
        if self.speed > 0.1:
            self.current_angle = (self.current_angle + self.speed) % 360
            self.speed *= 0.982  # Friction coefficient
            self.draw_wheel()
            self.root.after(20, self.animate_wheel) # 50 FPS
        else:
            self.speed = 0
            self.is_spinning = False
            self.determine_winner()

    def determine_winner(self):
        if not self.names:
            return
        arc_angle = 360 / len(self.names)
        # Calculate which slice landed on the 0-degree mark (the right-side pointer)
        # Because the wheel rotates counter-clockwise, the slices pass 0 in reverse order
        winning_index = int(((360 - self.current_angle) % 360) / arc_angle)
        winner = self.names[winning_index]
        self.winner_label.config(text=f"Winner: {winner}!")

    def open_edit_names_menu(self):
        top = tk.Toplevel(self.root)
        top.title("Edit Names")
        top.geometry("300x400")
        listbox = tk.Listbox(top, font=("Arial", 12))
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        for name in self.names:
            listbox.insert(tk.END, name)
        entry = tk.Entry(top, font=("Arial", 12))
        entry.pack(padx=10, pady=5, fill=tk.X)
        def add_name():
            new_name = entry.get().strip()
            if new_name:
                listbox.insert(tk.END, new_name)
                entry.delete(0, tk.END)
        def delete_name():
            selected = listbox.curselection()
            if selected:
                listbox.delete(selected)
        def save_names():
            self.names = list(listbox.get(0, tk.END))
            self.save_json(NAMES_FILE, self.names)
            self.draw_wheel()
            top.destroy()
        btn_frame = tk.Frame(top)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Add", command=add_name).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete", command=delete_name).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="Save & Close", command=save_names, bg="lightgreen").pack(pady=5)

    def open_theme_menu(self):
        top = tk.Toplevel(self.root)
        top.title("Theme Settings")
        top.geometry("250x150")
        tk.Label(top, text="Select Theme:", font=("Arial", 12)).pack(pady=10)
        theme_var = tk.StringVar(value=self.settings.get("theme", "Light"))
        themes = list(self.settings["themes"].keys())
        dropdown = tk.OptionMenu(top, theme_var, *themes)
        dropdown.pack(pady=10)
        def save_theme():
            self.settings["theme"] = theme_var.get()
            self.save_json(SETTINGS_FILE, self.settings)
            self.apply_theme()
            top.destroy()
        tk.Button(top, text="Apply & Save", command=save_theme, bg="lightblue").pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = SpinningWheelApp(root)
    root.mainloop()