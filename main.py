import flet as ft
import datetime
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
        
        self.setup_ui()

    def setup_ui(self):
        # Background
        self.page.bgcolor = "#F8F9FA" # Very light gray
        
        # Main Layout
        self.main_container = ft.Container(
            expand=True,
            content=ft.Column(
                controls=[
                    self.build_header(),
                    ft.Divider(height=1, color=ft.colors.with_opacity(0.1, ft.colors.BLACK)),
                    self.build_body()
                ],
                spacing=0
            )
        )
        
        self.page.add(self.main_container)
        
        if not self.user:
            self.show_login_overlay()

    def build_header(self):
        return ft.Container(
            padding=ft.padding.only(left=30, right=30, top=20, bottom=20),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text("Loom & Link", size=32, weight=ft.FontWeight.BOLD, color=PRIMARY),
                    ft.Row(
                        controls=[
                            ft.IconButton(ft.icons.SETTINGS, icon_color=ft.colors.BLACK54),
                            ft.ElevatedButton("Pair Partner", on_click=lambda _: self.show_pair_dialog(), bgcolor=SECONDARY, color=ft.colors.WHITE)
                        ]
                    )
                ]
            )
        )

    def build_body(self):
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
                            ft.Text(date.strftime("%d %b"), size=12, color=ft.colors.BLACK54)
                        ]
                    )
                ) for day, date in zip(days, dates)
            ]
        )
        
        grid_rows = []
        for slot in slots:
            row_controls = [ft.Container(width=60, content=ft.Text(slot, size=11, color=ft.colors.BLACK45))]
            for d in range(7):
                row_controls.append(
                    ft.Container(
                        expand=True,
                        height=40,
                        bgcolor=ft.colors.with_opacity(0.02, ft.colors.BLACK),
                        border=ft.border.all(0.5, ft.colors.with_opacity(0.05, ft.colors.BLACK)),
                        on_click=lambda e, day=d, time=slot: self.on_slot_click(day, time),
                        border_radius=4
                    )
                )
            grid_rows.append(ft.Row(spacing=10, controls=row_controls))

        return ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[header_row] + grid_rows
        )

    def show_login_overlay(self):
        def on_login(e):
            code = code_field.value
            if db.validate_code(code):
                self.user = db.login_user(code)
                self.couple_id = db.get_couple_id(self.user['id'])
                overlay.visible = False
                self.page.update()
                self.refresh_events()
            else:
                code_field.error_text = "Code must be 6-15 characters"
                self.page.update()

        code_field = ft.TextField(label="Enter Secret Code", width=300, password=True, can_reveal_password=True)
        
        overlay = ft.Container(
            expand=True,
            bgcolor=ft.colors.with_opacity(0.8, ft.colors.WHITE),
            content=ft.Column(
                main_alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("Welcome to Loom & Link", size=40, weight=ft.FontWeight.BOLD, color=PRIMARY),
                    ft.Text("Please enter your personal code to continue", color=ft.colors.BLACK54),
                    ft.VerticalDivider(height=20, color=ft.colors.TRANSPARENT),
                    code_field,
                    ft.ElevatedButton("Login / Sign Up", on_click=on_login, bgcolor=PRIMARY, color=ft.colors.WHITE, width=300)
                ]
            )
        )
        self.page.overlay.append(overlay)
        self.page.update()

    def show_pair_dialog(self):
        def on_pair(e):
            partner_code = partner_field.value
            if db.pair_partner(self.user['id'], partner_code):
                dialog.open = False
                self.couple_id = db.get_couple_id(self.user['id'])
                self.page.update()
                self.refresh_events()
            else:
                partner_field.error_text = "Partner code not found"
                self.page.update()

        partner_field = ft.TextField(label="Partner's Secret Code")
        dialog = ft.AlertDialog(
            title=ft.Text("Connect with your Partner"),
            content=partner_field,
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: setattr(dialog, "open", False)),
                ft.ElevatedButton("Link Hearts", on_click=on_pair, bgcolor=SECONDARY, color=ft.colors.WHITE)
            ]
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def on_slot_click(self, day, time):
        if not self.couple_id:
            self.page.snack_bar = ft.SnackBar(ft.Text("Please pair with a partner first!"))
            self.page.snack_bar.open = True
            self.page.update()
            return

        def save_event(e):
            # Simplified save for demo
            color_key = color_dropdown.value
            db.add_event(
                self.couple_id,
                title_field.value,
                desc_field.value,
                to_utc_str(datetime.datetime.now()), # Logic for actual day/time selection needed
                to_utc_str(datetime.datetime.now() + datetime.timedelta(minutes=30)),
                list(PASTEL_PALETTE.keys()).index(color_key)
            )
            dialog.open = False
            self.refresh_events()

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
                ft.TextButton("Cancel", on_click=lambda _: setattr(dialog, "open", False)),
                ft.ElevatedButton("Add to Schedule", on_click=save_event, bgcolor=PRIMARY, color=ft.colors.WHITE)
            ]
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def refresh_events(self):
        if self.couple_id:
            self.events = db.fetch_events(self.couple_id)
            # Re-render logic for events would go here
            # For now just update the UI state
            self.page.update()

def main(page: ft.Page):
    app = LoomLinkApp(page)

if __name__ == "__main__":
    ft.app(target=main)
