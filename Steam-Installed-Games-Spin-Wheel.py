import os,platform,random,math,json,vdf
import tkinter as tk

EXCLUDED_GAMES_FILE = "Games.json"
SETTINGS_FILE = "Steam-Settings.json"

BG_COLOR = "#121212"
PANEL_COLOR = "#1E1E1E"
TEXT_COLOR = "#FFFFFF"
BTN_BG = "#03DAC6"
BTN_FG = "#000000"

DEFAULT_CONFIG = {
    "available_wheel_colors": "#FF595E,#FFCA3A,#8AC926,#1982C4,#6A4C93,#F564A9",
	"wheel_size": 750,
    "wheel_text_size": 8,
    "wheel_text_color": "black",
    "wheel_text_font": "Helvetica",
    "winner_text_color": "#bb86fc",
    "winner_text_font": "Helvetica",
    "winner_text_size": 22,
    "spin_button_text_color": "#000000",
    "spin_button_text_font": "Helvetica",
    "spin_button_text_size": 16,
    "spin_button_color": "#03DAC6",
    "spin_button_rounded_corners": 10,
    "pointer_color": "#FFFFFF",
    "hub_ring_color": "#bb86fc",
    "hub_ring_width": 5
}

def get_steam_path():
    system = platform.system()
    if system == "Windows":
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r"SOFTWARE\WOW6432Node\Valve\Steam")
            path,_ = winreg.QueryValueEx(key,"InstallPath")
            return path
        except FileNotFoundError:
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r"SOFTWARE\Valve\Steam")
                path,_ = winreg.QueryValueEx(key,"InstallPath")
                return path
            except FileNotFoundError:
                return r"C:\Program Files (x86)\Steam"
    elif system == "Linux":
        return os.path.expanduser("~/.local/share/Steam")
    elif system == "Darwin":
        return os.path.expanduser("~/Library/Application Support/Steam")
    return None

def get_installed_games():
    steam_path = get_steam_path()
    if not steam_path or not os.path.exists(steam_path): return []
    library_folders_path = os.path.join(steam_path,"steamapps","libraryfolders.vdf")
    if not os.path.exists(library_folders_path): return []
    try:
        with open(library_folders_path,'r',encoding='utf-8') as f:
            data = vdf.load(f)
    except Exception:
        return []
    games = []
    library_folders = data.get("libraryfolders",{})
    for folder_data in library_folders.values():
        lib_path = folder_data.get("path") if isinstance(folder_data,dict) else (folder_data if isinstance(folder_data,str) and os.path.isabs(folder_data) else None)
        if not lib_path: continue
        steamapps_path = os.path.join(lib_path,"steamapps")
        if not os.path.exists(steamapps_path): continue
        for file in os.listdir(steamapps_path):
            if file.startswith("appmanifest_") and file.endswith(".acf"):
                acf_path = os.path.join(steamapps_path,file)
                try:
                    with open(acf_path,'r',encoding='utf-8') as af:
                        name = vdf.load(af).get("AppState",{}).get("name")
                        if name:
                            ignore_keywords = ["proton","steamworks","steam linux runtime","redistributable"]
                            if not any(k in name.lower() for k in ignore_keywords):
                                games.append(name)
                except Exception:
                    pass
    return sorted(list(set(games)))

class SpinWheelApp(tk.Tk):
    def __init__(self,games):
        super().__init__()
        self.title("Steam Game Randomizer")
        self.configure(bg=BG_COLOR)
        self.all_games = games if games else ["No Games Found"]
        self.filtered_games = list(self.all_games)
        self.excluded_games = set()
        self.is_spinning = False
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.settings_file = os.path.join(self.base_dir,EXCLUDED_GAMES_FILE)
        self.visual_file = os.path.join(self.base_dir,SETTINGS_FILE)
        self.load_data()
        self.canvas = tk.Canvas(self,bg=BG_COLOR,highlightthickness=0)
        self.canvas.pack(pady=(40,0))
        self.winner_label = tk.Label(self,text="",bg=BG_COLOR,justify="center")
        self.winner_label.pack(pady=(20,20))
        self.apply_winner_font()
        self.filter_btn = tk.Button(self,text="⚙",command=self.open_game_filters,font=("Helvetica",20),bg=BG_COLOR,fg=TEXT_COLOR,activebackground=PANEL_COLOR,borderwidth=0,cursor="hand2")
        self.filter_btn.place(x=15,y=15)
        self.visual_btn = tk.Button(self,text="🎨",command=self.open_visual_settings,font=("Helvetica",20),bg=BG_COLOR,fg=TEXT_COLOR,activebackground=PANEL_COLOR,borderwidth=0,cursor="hand2")
        self.visual_btn.place(x=60,y=15)
        self.angle_offset = 0
        self.bind("<Configure>",self.on_resize)
        self.update_filtered_games()
        self.redraw_everything()
        self.after(50,self.center_window)

    def on_resize(self,event):
        if event.widget == self:
            self.winner_label.config(wraplength=max(100,event.width-40))

    def center_window(self):
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw-w)//2
        y = (sh-h)//2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def load_data(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file,"r") as f:
                    self.excluded_games = set(json.load(f))
            except Exception: pass
        self.cfg = DEFAULT_CONFIG.copy()
        if os.path.exists(self.visual_file):
            try:
                with open(self.visual_file,"r") as f:
                    self.cfg.update(json.load(f))
            except Exception: pass

    def save_data(self):
        try:
            with open(self.settings_file,"w") as f: json.dump(list(self.excluded_games),f)
            with open(self.visual_file,"w") as f: json.dump(self.cfg,f)
        except Exception as e: print(f"Save error: {e}")

    def apply_winner_font(self):
        self.winner_label.config(font=(self.cfg["winner_text_font"],int(self.cfg["winner_text_size"]),"bold"),fg=self.cfg["winner_text_color"])

    def redraw_everything(self):
        ws = int(self.cfg["wheel_size"])
        self.canvas.config(width=ws,height=ws)
        self.apply_winner_font()
        self.draw_wheel()
        self.draw_spin_button()
        self.draw_pointer()

    def update_filtered_games(self):
        self.filtered_games = [g for g in self.all_games if g not in self.excluded_games]
        if not self.filtered_games: self.filtered_games = ["No Games Selected"]
        self.draw_wheel()

    def open_game_filters(self):
        if self.is_spinning: return
        win = tk.Toplevel(self)
        win.title("Filter Games")
        win.configure(bg=BG_COLOR)
        win.geometry("350x500")
        tk.Label(win,text="Select games to include:",bg=BG_COLOR,fg=TEXT_COLOR,font=("Helvetica",12,"bold")).pack(pady=10)
        frame = tk.Frame(win,bg=BG_COLOR)
        frame.pack(fill=tk.BOTH,expand=True,padx=15,pady=5)
        scroll = tk.Scrollbar(frame)
        scroll.pack(side=tk.RIGHT,fill=tk.Y)
        lb = tk.Listbox(frame,selectmode=tk.MULTIPLE,yscrollcommand=scroll.set,bg=PANEL_COLOR,fg=TEXT_COLOR,selectbackground="#bb86fc",highlightthickness=0,font=("Helvetica",10))
        lb.pack(side=tk.LEFT,fill=tk.BOTH,expand=True)
        scroll.config(command=lb.yview)
        for i,game in enumerate(self.all_games):
            lb.insert(tk.END,game)
            if game not in self.excluded_games: lb.select_set(i)
        # Prevent invalid save logic - just in case
        def save():
            try:
                for k,var in vars_dict.items():
                    self.cfg[k] = var.get()
            except tk.TclError:
                print("Invalid! Please use numeric valid numbers.")
                return
            self.save_data()
            self.redraw_everything()
            self.center_window()
            win.destroy()
        tk.Button(win,text="Save Filters",command=save,bg=BTN_BG,fg=BTN_FG,font=("Helvetica",11,"bold"),borderwidth=0,padx=10,pady=5).pack(pady=15)

    def open_visual_settings(self):
        if self.is_spinning: return
        win = tk.Toplevel(self)
        win.title("Visual Settings")
        win.configure(bg=BG_COLOR)
        win.geometry("450x600")
        canvas = tk.Canvas(win,bg=BG_COLOR,highlightthickness=0)
        scroll = tk.Scrollbar(win,orient="vertical",command=canvas.yview)
        frame = tk.Frame(canvas,bg=BG_COLOR)
        frame.bind("<Configure>",lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0),window=frame,anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left",fill="both",expand=True,padx=10,pady=10)
        scroll.pack(side="right",fill="y")
        vars_dict = {}
        row = 0
        for key,val in self.cfg.items():
            tk.Label(frame,text=key.replace("_"," ").title()+":",bg=BG_COLOR,fg=TEXT_COLOR,font=("Helvetica",10)).grid(row=row,column=0,sticky="w",pady=5)
            if isinstance(val,int):
                var = tk.IntVar(value=val)
                ent = tk.Spinbox(frame,from_=0,to=3000,textvariable=var,width=15)
            else:
                var = tk.StringVar(value=str(val))
                ent = tk.Entry(frame,textvariable=var,width=28)
            ent.grid(row=row,column=1,padx=10,pady=5)
            vars_dict[key] = var
            row += 1
        def save():
            for k,var in vars_dict.items():
                self.cfg[k] = var.get() if isinstance(self.cfg[k],int) else var.get()
            self.save_data()
            self.redraw_everything()
            self.center_window()
            win.destroy()
        tk.Button(frame,text="Save & Apply",command=save,bg=BTN_BG,fg=BTN_FG,font=("Helvetica",11,"bold"),borderwidth=0,padx=10,pady=5).grid(row=row,column=0,columnspan=2,pady=20)

    def draw_wheel(self):
        self.canvas.delete("wheel")
        num_games = len(self.filtered_games)
        
        # JUST in case there are no games installed - error handling.
        if num_games == 0:
            return
            
        arc_angle = 360 / num_games
        ws = int(self.cfg["wheel_size"])
        cx, cy = ws / 2, ws / 2
        r = ws * (250 / 600)
        colors = [c.strip() for c in str(self.cfg["available_wheel_colors"]).split(",")]
        
        for i, game in enumerate(self.filtered_games):
            start_angle = self.angle_offset + i * arc_angle
            
            color_idx = i % len(colors)
            # Last slice could be the same color as the first slice.. this prevents that.
            if i == num_games - 1 and color_idx == 0 and num_games > 1:
                color_idx = 1 % len(colors)
                
            col = colors[color_idx]
            self.canvas.create_arc(cx - r, cy - r, cx + r, cy + r, start=start_angle, extent=arc_angle, fill=col, outline="", tags="wheel")
            
            mid_angle = start_angle + arc_angle / 2
            r_text = r - 25 
            tx = cx + r_text * math.cos(math.radians(mid_angle))
            ty = cy - r_text * math.sin(math.radians(mid_angle)) 
            
            name = game[:18] + ".." if len(game) > 18 else game
            self.canvas.create_text(tx, ty, text=name, font=(self.cfg["wheel_text_font"], int(self.cfg["wheel_text_size"]), "bold"), fill=self.cfg["wheel_text_color"], angle=(mid_angle + 180) % 360, anchor="w", tags="wheel")
            
        self.canvas.tag_lower("wheel")

    def create_rounded_rect(self,x1,y1,x2,y2,radius,**kwargs):
        if radius<=0:
            self.canvas.create_rectangle(x1,y1,x2,y2,outline="",**kwargs)
            return
        self.canvas.create_oval(x1,y1,x1+2*radius,y1+2*radius,outline="",**kwargs)
        self.canvas.create_oval(x2-2*radius,y1,x2,y1+2*radius,outline="",**kwargs)
        self.canvas.create_oval(x1,y2-2*radius,x1+2*radius,y2,outline="",**kwargs)
        self.canvas.create_oval(x2-2*radius,y2-2*radius,x2,y2,outline="",**kwargs)
        self.canvas.create_rectangle(x1+radius,y1,x2-radius,y2,outline="",**kwargs)
        self.canvas.create_rectangle(x1,y1+radius,x2,y2-radius,outline="",**kwargs)

    def draw_spin_button(self):
        self.canvas.delete("hub")
        ws = int(self.cfg["wheel_size"])
        cx, cy = ws/2,ws/2
        r_hub = 65
        self.canvas.create_oval(cx-r_hub,cy-r_hub,cx+r_hub,cy+r_hub,fill=PANEL_COLOR,outline=self.cfg["hub_ring_color"],width=int(self.cfg["hub_ring_width"]),tags="hub")
        btn_w,btn_h = 90,45
        btn_r = int(self.cfg["spin_button_rounded_corners"])
        btn_r = min(btn_r,btn_w/2,btn_h/2)
        x1,y1 = cx-btn_w/2,cy-btn_h/2
        x2,y2 = cx+btn_w/2,cy+btn_h/2
        self.create_rounded_rect(x1,y1,x2,y2,btn_r,fill=self.cfg["spin_button_color"],tags=("hub","clickable"))
        self.canvas.create_text(cx,cy,text="SPIN",font=(self.cfg["spin_button_text_font"],int(self.cfg["spin_button_text_size"]),"bold"),fill=self.cfg["spin_button_text_color"],tags=("hub","clickable"))
        self.canvas.tag_bind("clickable","<Button-1>",lambda e: self.spin())
        self.canvas.tag_bind("clickable","<Enter>",lambda e: self.canvas.config(cursor="hand2"))
        self.canvas.tag_bind("clickable","<Leave>",lambda e: self.canvas.config(cursor=""))

    def draw_pointer(self):
        self.canvas.delete("pointer")
        ws = int(self.cfg["wheel_size"])
        cx,cy = ws/2,ws/2
        r = ws*(250/600)
        base_x = cx-r-25
        base_y = cy
        tip_x = cx-r+15
        p1 = (tip_x,cy)
        p2 = (base_x,cy-15)
        p3 = (base_x,cy+15)
        self.canvas.create_polygon(*p1,*p2,*p3,fill=self.cfg["pointer_color"],outline="",tags="pointer")

    def spin(self):
        if self.is_spinning: return
        self.is_spinning = True
        self.winner_label.config(text="")
        self.canvas.config(cursor="")
        target_rotation = random.randint(1800,3000)
        self.animate_spin(target=target_rotation,current=0,speed=45)

    def animate_spin(self, target, current, speed):
        # Decelerate wheel instead of immediatley stopping it.
        if current < target:
            remaining_distance = target - current
            speed = min(45.0, remaining_distance / 25.0)
            
            speed = max(0.5, speed)
            
            self.angle_offset = (self.angle_offset + speed) % 360
            self.draw_wheel()
            self.canvas.tag_raise("pointer")
            
            current += speed
            
            self.after(20, self.animate_spin, target, current, speed)
        else:
            self.is_spinning = False
            self.announce_winner()

    def announce_winner(self):
        arc_angle = 360/len(self.filtered_games)
        target_angle = (180-self.angle_offset)%360
        winner_idx = int(target_angle//arc_angle)
        winner = self.filtered_games[winner_idx]
        self.winner_label.config(text=f"{winner}")

if __name__ == "__main__":
    games_list = get_installed_games()
    app = SpinWheelApp(games_list)
    app.mainloop()