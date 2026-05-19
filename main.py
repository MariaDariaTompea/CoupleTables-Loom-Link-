import flet as ft
import datetime
import threading
import time
from styles import PASTEL_PALETTE, GLASS_STYLE, PRIMARY, SECONDARY, ACCENT, get_glass_container
from database import db
from utils import get_week_days, get_time_slots, to_utc_str, get_local_time

class LoomLinkApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Loom & Link: LDR Schedule Maker"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 0
        self.page.window_width = 1200
        self.page.window_height = 800
        
        self.user = None
        self.couple_id = None
        self.events = []
        
        if not self.user:
            self.show_login_screen()
        else:
            self.page.on_error = lambda e: print(f"FLET ERROR: {e.data}")
            self.show_main_screen()

    def show_login_screen(self):
        def on_login(e):
            print("on_login triggered")
            code = code_field.value
            if db.validate_code(code):
                try:
                    self.user = db.login_user(code)
                    if self.user:
                        self.couple_id = db.get_couple_id(self.user['id'])
                        snack = ft.SnackBar(ft.Text(f"Welcome back, {self.user.get('name', 'User')}!"), bgcolor=ft.Colors.GREEN)
                        self.page.show_dialog(snack)
                        self.show_main_screen()
                    else:
                        snack = ft.SnackBar(ft.Text("Login failed: User not found."), bgcolor=ft.Colors.RED)
                        self.page.show_dialog(snack)
                except Exception as ex:
                    snack = ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED)
                    self.page.show_dialog(snack)
            else:
                code_field.error_text = "Code must be 5-15 characters"
                self.page.update()

        code_field = ft.TextField(
            label="Enter Secret Code", 
            width=300, 
            password=True, 
            can_reveal_password=True,
            on_submit=on_login,
            autofocus=True
        )

        self.page.controls.clear()
        self.page.add(
            ft.Container(
                expand=True,
                alignment=ft.Alignment.CENTER,
                bgcolor="#F8F9FA",
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("Welcome to Loom & Link", size=40, weight=ft.FontWeight.BOLD, color=PRIMARY),
                        ft.Text("Login to continue", color=ft.Colors.BLACK_54),
                        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                        code_field,
                        ft.FilledButton(
                            "Login", 
                            on_click=on_login, 
                            bgcolor=PRIMARY, 
                            color=ft.Colors.WHITE, 
                            width=300,
                            height=50
                        ),
                        ft.TextButton(
                            "Don't have an account? Sign Up", 
                            on_click=lambda _: self.show_signup_screen()
                        )
                    ]
                )
            )
        )
        self.page.update()

    def show_signup_screen(self):
        def on_signup(e):
            name = name_field.value
            code = code_field.value
            if not name:
                name_field.error_text = "Name is required"
                self.page.update()
                return
            if db.validate_code(code):
                try:
                    self.user = db.create_user(name, code)
                    if self.user:
                        snack = ft.SnackBar(ft.Text("Account created successfully!"), bgcolor=ft.Colors.GREEN)
                        self.page.show_dialog(snack)
                        self.show_main_screen()
                    else:
                        snack = ft.SnackBar(ft.Text("Signup failed. Code might already be in use."), bgcolor=ft.Colors.RED)
                        self.page.show_dialog(snack)
                except Exception as ex:
                    snack = ft.SnackBar(ft.Text(f"Signup error: {ex}"), bgcolor=ft.Colors.RED)
                    self.page.show_dialog(snack)
            else:
                code_field.error_text = "Code must be 5-15 characters"
                self.page.update()

        name_field = ft.TextField(label="Your Name", width=300)
        code_field = ft.TextField(label="Secret Code (5-15 chars)", width=300, password=True, can_reveal_password=True)

        self.page.controls.clear()
        self.page.add(
            ft.Container(
                expand=True,
                alignment=ft.Alignment.CENTER,
                bgcolor="#F8F9FA",
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("Join Loom & Link", size=40, weight=ft.FontWeight.BOLD, color=PRIMARY),
                        ft.Text("Create your account", color=ft.Colors.BLACK_54),
                        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                        name_field,
                        code_field,
                        ft.FilledButton(
                            "Sign Up", 
                            on_click=on_signup, 
                            bgcolor=PRIMARY, 
                            color=ft.Colors.WHITE, 
                            width=300,
                            height=50
                        ),
                        ft.TextButton(
                            "Already have an account? Login", 
                            on_click=lambda _: self.show_login_screen()
                        )
                    ]
                )
            )
        )
        self.page.update()

    def show_main_screen(self):
        self.page.controls.clear()
        
        # Re-build main layout
        self.main_container = ft.Container(
            expand=True,
            content=ft.Column(
                controls=[
                    self.build_header(),
                    ft.Divider(height=1, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
                    self.build_body()
                ],
                spacing=0
            )
        )
        
        self.page.add(self.main_container)
        self.page.update()
        self.refresh_events()

    def on_pair_click(self, e):
        print(f"DEBUG: Pair Partner button clicked by {self.user.get('name', 'unknown')}")
        self.show_pair_dialog()

    def build_header(self):
        return ft.Container(
            padding=ft.Padding(30, 20, 30, 20),
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text("Loom & Link", size=32, weight=ft.FontWeight.BOLD, color=PRIMARY),
                    ft.Row(
                        controls=[
                            ft.IconButton(ft.Icons.SETTINGS, icon_color=ft.Colors.BLACK_54),
                            ft.Button(
                                "Pair Partner", 
                                on_click=self.on_pair_click, 
                                bgcolor=SECONDARY, 
                                color=ft.Colors.WHITE
                            )
                        ]
                    )
                ]
            )
        )

    def build_body(self):
        if not self.couple_id:
            return ft.Container(
                expand=True,
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.FAVORITE_BORDER, size=100, color=SECONDARY),
                        ft.Text("You're not paired yet!", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text("Pair with your partner to start sharing your schedule.", color=ft.Colors.BLACK_54),
                        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                        ft.FilledButton(
                            "Pair Partner Now", 
                            on_click=self.on_pair_click, 
                            bgcolor=PRIMARY, 
                            color=ft.Colors.WHITE,
                            width=300,
                            height=50
                        )
                    ]
                )
            )
        
        self.grid_container = ft.Container(
            expand=True,
            padding=20,
            content=self.build_schedule_grid()
        )
        return self.grid_container

    def build_schedule_grid(self):
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        dates = get_week_days()
        slots = get_time_slots()
        
        header_row = ft.Row(
            spacing=10,
            controls=[ft.Container(width=60)] + [
                ft.Container(
                    expand=True,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(day, weight=ft.FontWeight.BOLD),
                            ft.Text(date.strftime("%d %b"), size=12, color=ft.Colors.BLACK_54)
                        ]
                    )
                ) for day, date in zip(days, dates)
            ]
        )
        
        grid_rows = []
        # Prepare event map for quick lookup: {(day_index, time_slot): event}
        event_map = {}
        for event in self.events:
            # Convert UTC start_time to user's local time
            local_start = get_local_time(event['start_time'], self.user.get('region', 'UTC'))
            day_idx = local_start.weekday()
            # Find the closest 30-min slot
            hour = local_start.hour
            minute = "00" if local_start.minute < 30 else "30"
            slot_key = f"{hour:02d}:{minute}"
            event_map[(day_idx, slot_key)] = event

        for slot in slots:
            row_controls = [ft.Container(width=60, content=ft.Text(slot, size=11, color=ft.Colors.BLACK_45))]
            for d in range(7):
                cell_content = None
                bgcolor = ft.Colors.with_opacity(0.02, ft.Colors.BLACK)
                
                if (d, slot) in event_map:
                    ev = event_map[(d, slot)]
                    color = list(PASTEL_PALETTE.values())[ev.get('color_index', 0)]
                    cell_content = ft.Text(ev['title'], size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87, no_wrap=True)
                    bgcolor = color

                row_controls.append(
                    ft.Container(
                        expand=True,
                        height=40,
                        bgcolor=bgcolor,
                        content=cell_content,
                        alignment=ft.alignment.center,
                        border=ft.Border.all(0.5, ft.Colors.with_opacity(0.05, ft.Colors.BLACK)),
                        on_click=lambda e, day=d, time=slot: self.on_slot_click(day, time),
                        border_radius=4
                    )
                )
            grid_rows.append(ft.Row(spacing=10, controls=row_controls))

        return ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[header_row] + grid_rows
        )

    def show_pair_dialog(self):
        dialog_content = ft.Column(tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self._pair_dialog_open = True
        dialog = ft.AlertDialog(
            title=ft.Text("Connect with your Partner"),
            content=dialog_content,
            on_dismiss=lambda e: setattr(self, '_pair_dialog_open', False),
        )
        self._pair_dialog = dialog
        
        def start_pairing_flow():
            # Phase 1: Wait 5 seconds
            dialog_content.controls = [
                ft.ProgressRing(width=40, height=40, stroke_width=2),
                ft.Text("Preparing pairing link... please wait 5 seconds")
            ]
            self.page.update()
            time.sleep(5)

            # Phase 2: Generate code and start 5-minute timer
            pairing_code = db.generate_pairing_code(self.user['id'])
            if not pairing_code:
                dialog_content.controls = [ft.Text("Error generating code. Please try again.", color=ft.Colors.RED)]
                self.page.update()
                return

            # Phase 3: Display code and timer
            progress_bar = ft.ProgressBar(width=300, value=1.0, color=SECONDARY)
            timer_text = ft.Text("Code expires in: 5:00", size=12, color=ft.Colors.BLACK_54)
            
            existing_code_field = ft.TextField(label="Enter Partner's Code", width=300)
            
            def on_connect_existent(e):
                if db.pair_with_code(self.user['id'], existing_code_field.value):
                    self._pair_dialog_open = False
                    self.page.pop_dialog()
                    self.couple_id = db.get_couple_id(self.user['id'])
                    self.show_main_screen()
                else:
                    existing_code_field.error_text = "Invalid or expired code"
                    self.page.update()

            dialog_content.controls = [
                ft.Text("Your Pairing Code:", weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Text(pairing_code, size=24, weight=ft.FontWeight.BOLD, color=PRIMARY, selectable=True),
                    padding=10,
                    bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
                    border_radius=8
                ),
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                timer_text,
                progress_bar,
                ft.Divider(height=30),
                ft.Text("Connect to partner with existent code", size=14, weight=ft.FontWeight.W_500),
                existing_code_field,
                ft.FilledButton("Connect", on_click=on_connect_existent, bgcolor=SECONDARY, color=ft.Colors.WHITE, width=300)
            ]
            self.page.update()

            # Countdown logic
            total_seconds = 300
            for i in range(total_seconds, -1, -1):
                if not self._pair_dialog_open: break
                minutes = i // 60
                seconds = i % 60
                timer_text.value = f"Code expires in: {minutes}:{seconds:02d}"
                progress_bar.value = i / total_seconds
                self.page.update()
                time.sleep(1)
            
            if self._pair_dialog_open and i == 0:
                dialog_content.controls = [ft.Text("Code expired. Please restart pairing.", color=ft.Colors.RED)]
                self.page.update()

        self.page.show_dialog(dialog)
        threading.Thread(target=start_pairing_flow, daemon=True).start()

    def on_slot_click(self, day, time):
        if not self.couple_id:
            snack = ft.SnackBar(ft.Text("Please pair with a partner first!"))
            self.page.show_dialog(snack)
            return

        title_field = ft.TextField(label="Activity Name")
        desc_field = ft.TextField(label="Description", multiline=True)
        color_dropdown = ft.Dropdown(
            label="Pick a Color",
            options=[ft.dropdown.Option(k) for k in PASTEL_PALETTE.keys()]
        )
        
        dialog = ft.AlertDialog(
            title=ft.Text(f"Add Activity for {time}"),
            content=ft.Column(
                tight=True,
                controls=[title_field, desc_field, color_dropdown]
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.page.pop_dialog()),
                ft.FilledButton("Add to Schedule", on_click=lambda e: self._save_and_close(dialog, title_field, desc_field, color_dropdown), bgcolor=PRIMARY, color=ft.Colors.WHITE)
            ]
        )
        self.page.show_dialog(dialog)

    def _save_and_close(self, dialog, title_field, desc_field, color_dropdown):
        color_key = color_dropdown.value
        db.add_event(
            self.couple_id,
            title_field.value,
            desc_field.value,
            to_utc_str(datetime.datetime.now()),
            to_utc_str(datetime.datetime.now() + datetime.timedelta(minutes=30)),
            list(PASTEL_PALETTE.keys()).index(color_key)
        )
        self.page.pop_dialog()
        self.refresh_events()

    def refresh_events(self):
        if self.couple_id:
            self.events = db.fetch_events(self.couple_id)
            # Re-render logic for events would go here
            # For now just update the UI state
            self.page.update()

def main(page: ft.Page):
    app = LoomLinkApp(page)

if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER, port=8550)
