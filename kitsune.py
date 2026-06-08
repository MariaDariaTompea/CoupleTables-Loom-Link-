import flet as ft
import threading
import time
import random

class KitsuneChibi(ft.Container):
    def __init__(self, size=200, is_success_mode=False):
        super().__init__()
        self.size_val = size
        self.is_success_mode = is_success_mode
        self.alignment = ft.alignment.Alignment(0, 0)
        self.running = False
        
        # Color Palette
        self.white_color = ft.Colors.WHITE
        self.outline_color = "#FF9EB5"
        self.pink_inner = "#FFD1DC"
        self.cheek_pink = "#FFA3B1"
        
        # Components
        # Left Ear
        self.left_ear_inner = ft.Container(
            width=22,
            height=22,
            bgcolor=self.pink_inner,
            border_radius=ft.BorderRadius.only(top_left=12, bottom_right=12),
            alignment=ft.alignment.Alignment(0, 0),
        )
        self.left_ear = ft.Container(
            content=self.left_ear_inner,
            width=38,
            height=38,
            bgcolor=self.white_color,
            border=ft.Border.all(1.5, self.outline_color),
            border_radius=ft.BorderRadius.only(top_left=22, bottom_right=22),
            rotate=-0.35,
            animate_rotation=ft.Animation(400, ft.AnimationCurve.EASE_IN_OUT),
            alignment=ft.alignment.Alignment(0, 0),
        )
        
        # Right Ear
        self.right_ear_inner = ft.Container(
            width=22,
            height=22,
            bgcolor=self.pink_inner,
            border_radius=ft.BorderRadius.only(top_right=12, bottom_left=12),
            alignment=ft.alignment.Alignment(0, 0),
        )
        self.right_ear = ft.Container(
            content=self.right_ear_inner,
            width=38,
            height=38,
            bgcolor=self.white_color,
            border=ft.Border.all(1.5, self.outline_color),
            border_radius=ft.BorderRadius.only(top_right=22, bottom_left=22),
            rotate=0.35,
            animate_rotation=ft.Animation(400, ft.AnimationCurve.EASE_IN_OUT),
            alignment=ft.alignment.Alignment(0, 0),
        )
        
        # Head (Face)
        self.eyes_text = ft.Text("^ ◡ ^" if not self.is_success_mode else "♥ ◡ ♥", size=14, weight=ft.FontWeight.BOLD, color="#8B4F58")
        self.blush_l = ft.Container(width=10, height=6, bgcolor=self.cheek_pink, border_radius=3)
        self.blush_r = ft.Container(width=10, height=6, bgcolor=self.cheek_pink, border_radius=3)
        
        self.face = ft.Container(
            content=ft.Stack([
                ft.Container(
                    content=self.eyes_text,
                    alignment=ft.alignment.Alignment(0, 0),
                    margin=ft.margin.Margin(top=10)
                ),
                # Left cheek
                ft.Container(
                    content=self.blush_l,
                    margin=ft.margin.Margin(left=20, top=32)
                ),
                # Right cheek
                ft.Container(
                    content=self.blush_r,
                    margin=ft.margin.Margin(right=20, top=32)
                )
            ]),
            width=100,
            height=70,
            bgcolor=self.white_color,
            border=ft.Border.all(1.5, self.outline_color),
            border_radius=35,
            alignment=ft.alignment.Alignment(0, 0),
            offset=ft.Offset(0, 0),
            animate_offset=ft.Animation(600, ft.AnimationCurve.EASE_IN_OUT),
            animate_scale=ft.Animation(600, ft.AnimationCurve.EASE_IN_OUT),
        )
        
        # Body
        self.body = ft.Container(
            width=65,
            height=60,
            bgcolor=self.white_color,
            border=ft.Border.all(1.5, self.outline_color),
            border_radius=25,
            animate_scale=ft.Animation(600, ft.AnimationCurve.EASE_IN_OUT),
        )
        
        # Tail
        self.tail_tip = ft.Container(
            width=20,
            height=20,
            bgcolor=self.cheek_pink,
            border_radius=ft.BorderRadius.only(top_right=12, bottom_left=12),
        )
        self.tail = ft.Container(
            content=ft.Stack([
                ft.Container(
                    content=self.tail_tip,
                    alignment=ft.alignment.Alignment(1, -1)
                )
            ]),
            width=32,
            height=50,
            bgcolor=self.white_color,
            border=ft.Border.all(1.5, self.outline_color),
            border_radius=ft.BorderRadius.only(top_right=16, bottom_left=16),
            rotate=0.2,
            animate_rotation=ft.Animation(500, ft.AnimationCurve.EASE_IN_OUT),
            alignment=ft.alignment.Alignment(0, 0),
        )
        
        # Floating Hearts for Success Mode or Idle Cuteness
        self.hearts = []
        for i in range(3):
            heart = ft.Icon(
                ft.Icons.FAVORITE,
                color="#FF5E7E",
                size=random.randint(12, 18),
                opacity=0.0 if not self.is_success_mode else 0.8,
                offset=ft.Offset(random.uniform(-0.8, 0.8), random.uniform(-0.5, 0.5)),
                animate_offset=ft.Animation(1000, ft.AnimationCurve.DECELERATE),
                animate_opacity=ft.Animation(1000, ft.AnimationCurve.EASE_IN_OUT)
            )
            self.hearts.append(heart)

        # Assemble Assembly Stack
        # We place ears behind head, body below head, tail behind body/ears.
        self.chibi_assembly = ft.Stack(
            controls=[
                # Tail (back layer)
                ft.Container(
                    content=self.tail,
                    margin=ft.margin.Margin(left=85, top=70)
                ),
                # Left Ear
                ft.Container(
                    content=self.left_ear,
                    margin=ft.margin.Margin(left=18, top=0)
                ),
                # Right Ear
                ft.Container(
                    content=self.right_ear,
                    margin=ft.margin.Margin(left=74, top=0)
                ),
                # Body
                ft.Container(
                    content=self.body,
                    margin=ft.margin.Margin(left=33, top=55)
                ),
                # Face
                ft.Container(
                    content=self.face,
                    margin=ft.margin.Margin(left=15, top=18)
                ),
                # Floating Hearts
                * [ft.Container(content=h, margin=ft.margin.Margin(left=50, top=10)) for h in self.hearts]
            ],
            width=135,
            height=130
        )
        
        # Wrap everything in a nice centered box
        self.content = ft.Container(
            content=self.chibi_assembly,
            alignment=ft.alignment.Alignment(0, 0),
            width=self.size_val,
            height=self.size_val,
        )

    def did_mount(self):
        self.running = True
        self.thread = threading.Thread(target=self._animate_loop, daemon=True)
        self.thread.start()

    def will_unmount(self):
        self.running = False

    def _animate_loop(self):
        cycle = 0
        while self.running:
            try:
                # Breathing and tail wagging animation
                if cycle % 2 == 0:
                    # Breathe In
                    self.body.scale = 1.05
                    self.face.scale = 1.02
                    self.face.offset = ft.Offset(0, -0.03)
                    self.tail.rotate = 0.5
                    self.left_ear.rotate = -0.42
                    self.right_ear.rotate = 0.42
                    
                    if self.is_success_mode:
                        # Hearts expand and float up
                        for h in self.hearts:
                            h.opacity = random.uniform(0.6, 0.9)
                            h.offset = ft.Offset(random.uniform(-1.0, 1.0), random.uniform(-1.2, -0.6))
                else:
                    # Breathe Out
                    self.body.scale = 1.0
                    self.face.scale = 1.0
                    self.face.offset = ft.Offset(0, 0)
                    self.tail.rotate = 0.1
                    self.left_ear.rotate = -0.28
                    self.right_ear.rotate = 0.28
                    
                    if self.is_success_mode:
                        # Hearts fade out slightly and lower down
                        for h in self.hearts:
                            h.opacity = 0.2
                            h.offset = ft.Offset(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.2))
                
                self.update()
                time.sleep(1.0)
                cycle += 1
            except Exception:
                break
