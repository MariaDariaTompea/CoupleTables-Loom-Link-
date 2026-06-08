import flet as ft
import datetime
import threading
import time
import pytz
import json
import styles
from database import db
from utils import get_week_days, get_time_slots, to_utc_str, get_local_time
from kitsune import KitsuneChibi

class LoomLinkApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Loom & Link: LDR Schedule Maker"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 0
        self.page.window_width = 1200
        self.page.window_height = 800
        
        self.user = None
        self.selected_bond_id = None
        self.selected_partner_name = ""
        self.bonds = []
        self.events = []
        self.pairing_dialog_open = False
        
        # Go straight to login
        self.show_login_screen()

    # Loading screen removed - SharedPreferences not supported in web mode

    # Auto-login removed - SharedPreferences not supported in web mode

    # --- HELPER ACTIONS ---
    def show_dialog(self, dialog):
        self.page.show_dialog(dialog)

    def close_dialog(self, dialog):
        self.page.pop_dialog()

    def show_snack(self, text, is_error=False):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(text, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
            bgcolor=styles.PRIMARY if not is_error else ft.Colors.RED_ACCENT
        )
        self.page.snack_bar.open = True
        self.page.update()

    def copy_to_clipboard(self, text):
        async def do_copy():
            try:
                clip = ft.Clipboard()
                self.page.overlay.append(clip)
                self.page.update()
                await clip.set(text)
                self.page.overlay.remove(clip)
                self.page.update()
                self.show_snack("Pairing code copied to clipboard! ♥")
            except Exception:
                self.show_snack("Clipboard copy failed. Please copy manually (Ctrl+C).", is_error=True)
            
        self.page.run_task(do_copy)

    # --- LOGIN & SIGNUP VIEWS ---
    def show_login_screen(self):
        def on_login(e):
            username = name_field.value.strip()
            password = password_field.value.strip()
            
            if not username or not password:
                self.show_snack("Username and Password are required!", is_error=True)
                return
                
            try:
                self.user = db.login_user(username, password)
                if self.user:
                    
                    self.show_snack(f"Welcome back, {self.user['name']}! ♥")
                    self.show_main_screen()
                else:
                    self.show_snack("Login failed: Invalid credentials.", is_error=True)
            except Exception as ex:
                self.show_snack(f"Login error: {ex}", is_error=True)

        name_field = ft.TextField(
            label="Name (Username)", 
            width=300, 
            autofocus=True,
            on_submit=lambda _: password_field.focus(),
            **styles.LOVE_INPUT_STYLE
        )
        
        password_field = ft.TextField(
            label="Password", 
            width=300, 
            password=True, 
            can_reveal_password=True,
            on_submit=on_login,
            **styles.LOVE_INPUT_STYLE
        )

        login_card = styles.get_postcard_container(
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15,
                controls=[
                    ft.Row([
                        ft.Icon(ft.Icons.FAVORITE, color=styles.PRIMARY, size=24),
                        ft.Text("Loom & Link", size=32, weight=ft.FontWeight.BOLD, color=styles.PRIMARY),
                        ft.Icon(ft.Icons.FAVORITE, color=styles.PRIMARY, size=24)
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Text("Syncing Hearts Across Timezones", color="#8B5F6C", size=13, weight=ft.FontWeight.W_500),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    name_field,
                    password_field,
                    ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                    ft.ElevatedButton(
                        "Login", 
                        on_click=on_login, 
                        bgcolor=styles.PRIMARY, 
                        color=ft.Colors.WHITE, 
                        width=300,
                        height=45,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=22))
                    ),
                    ft.TextButton(
                        "Don't have an account? Sign Up", 
                        on_click=self.show_signup_dialog,
                        style=ft.ButtonStyle(color=styles.PRIMARY)
                    )
                ]
            ),
            width=400,
            padding=35
        )

        self.page.controls.clear()
        self.page.add(
            ft.Container(
                expand=True,
                alignment=ft.Alignment.CENTER,
                bgcolor=styles.BG_CREAM,
                content=login_card
            )
        )
        self.page.update()

    def show_signup_dialog(self, e=None):
        name_field = ft.TextField(label="Name (Username)", **styles.LOVE_INPUT_STYLE)
        email_field = ft.TextField(label="Email", **styles.LOVE_INPUT_STYLE)
        password_field = ft.TextField(label="Password", password=True, can_reveal_password=True, **styles.LOVE_INPUT_STYLE)
        
        region_dropdown = ft.Dropdown(
            label="Region (Timezone)",
            options=[ft.dropdown.Option(r) for r in ["Europe/Rome", "America/New_York", "UTC", "Asia/Tokyo", "Europe/London", "Australia/Sydney"]],
            value="Europe/Rome",
            **styles.LOVE_INPUT_STYLE
        )
        
        signup_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.FAVORITE, color=styles.PRIMARY),
                ft.Text("Create Account", color=styles.TEXT_DARK, weight=ft.FontWeight.BOLD),
                ft.Icon(ft.Icons.FAVORITE, color=styles.PRIMARY)
            ], alignment=ft.MainAxisAlignment.CENTER),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Create your account and start pairing!", color=styles.TEXT_DARK, size=12),
                    name_field,
                    email_field,
                    password_field,
                    region_dropdown
                ], tight=True, spacing=15),
                width=320,
                padding=10
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.close_dialog(signup_dialog), style=ft.ButtonStyle(color=styles.TEXT_DARK)),
                ft.ElevatedButton("Sign Up", on_click=lambda e: self.process_signup(signup_dialog, name_field, email_field, password_field, region_dropdown), bgcolor=styles.PRIMARY, color=ft.Colors.WHITE)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor="#FFFDFE",
            shape=ft.RoundedRectangleBorder(radius=16)
        )
        self.show_dialog(signup_dialog)

    def process_signup(self, dialog, name_field, email_field, password_field, region_dropdown):
        name = name_field.value.strip()
        email = email_field.value.strip()
        password = password_field.value
        region = region_dropdown.value
        
        if not name or not password or not email:
            self.show_snack("All fields are required!", is_error=True)
            return
            
        if not db.validate_code(password):
            password_field.error_text = "Password must be 4-25 characters"
            self.page.update()
            return
            
        try:
            new_user = db.create_user(name, email, password, region)
            if new_user:
                self.close_dialog(dialog)
                self.show_signup_success_animation()
            else:
                self.show_snack("Signup failed. Username might be taken.", is_error=True)
        except Exception as ex:
            self.show_snack(f"Signup error: {ex}", is_error=True)

    def show_signup_success_animation(self):
        success_chibi = KitsuneChibi(size=140, is_success_mode=True)
        success_dialog = ft.AlertDialog(
            modal=True,
            content=ft.Container(
                content=ft.Column([
                    success_chibi,
                    ft.Text("Success!", size=22, color=styles.PRIMARY, weight=ft.FontWeight.BOLD),
                    ft.Text("Account created successfully!\nWelcome to Loom & Link.", text_align=ft.TextAlign.CENTER, color=styles.TEXT_DARK),
                ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=260,
                padding=10,
                alignment=ft.alignment.Alignment(0, 0)
            ),
            bgcolor="#FFFDFE",
            shape=ft.RoundedRectangleBorder(radius=16)
        )
        self.show_dialog(success_dialog)
        
        def dismiss_and_go_login():
            time.sleep(3.5)
            self.close_dialog(success_dialog)
            self.show_login_screen()
            
        threading.Thread(target=dismiss_and_go_login, daemon=True).start()

    # --- MAIN SCREEN INTERFACE ---
    def show_main_screen(self):
        self.page.controls.clear()
        
        # Load bonds from DB
        self.bonds = db.fetch_user_bonds(self.user['id'])
        
        # Layout components
        self.sidebar_container = ft.Container(
            content=self.build_sidebar(),
            width=280,
            bgcolor="#FFFDFE",
            border=ft.Border(right=ft.BorderSide(1.5, "#FFD1DC")),
            padding=15
        )
        
        self.main_content_container = ft.Container(
            content=self.build_body(),
            expand=True,
            padding=20
        )
        
        self.main_container = ft.Container(
            expand=True,
            bgcolor=styles.BG_CREAM,
            content=ft.Column(
                controls=[
                    self.build_header(),
                    ft.Row(
                        controls=[
                            self.sidebar_container,
                            self.main_content_container
                        ],
                        expand=True,
                        spacing=0
                    )
                ],
                spacing=0,
                expand=True
            )
        )
        
        self.page.add(self.main_container)
        self.page.update()
        
        # Start a background polling thread for real-time schedule updates if not already started
        if not hasattr(self, "refresh_thread_started") or not self.refresh_thread_started:
            self.refresh_thread_started = True
            threading.Thread(target=self.run_schedule_refresh_loop, daemon=True).start()

    def logout(self, e):
        
        self.user = None
        self.refresh_thread_started = False
        self.selected_bond_id = None
        self.selected_partner_name = ""
        self.bonds = []
        self.events = []
        self.show_snack("Logged out successfully! See you soon. ♥")
        self.show_login_screen()

    def build_header(self):
        connect_btn = ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(ft.Icons.MARKUNREAD_MAILBOX_OUTLINED, size=18, color=ft.Colors.WHITE),
                ft.Text("CONNECT", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
            ], spacing=5),
            on_click=self.show_connect_dialog,
            bgcolor=styles.PRIMARY,
            height=40,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
        
        return ft.Container(
            padding=ft.Padding(30, 15, 30, 15),
            bgcolor=ft.Colors.WHITE,
            border=ft.Border(bottom=ft.BorderSide(1.5, "#FFD1DC")),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row([
                        ft.Icon(ft.Icons.FAVORITE, color=styles.PRIMARY, size=24),
                        ft.Text("Loom & Link", size=26, weight=ft.FontWeight.BOLD, color=styles.PRIMARY)
                    ], spacing=10),
                    ft.Row([
                        ft.Text(f"Logged in as: {self.user['name']}", color=styles.TEXT_DARK, weight=ft.FontWeight.W_500),
                        ft.IconButton(
                            icon=ft.Icons.LOGOUT,
                            icon_color=styles.PRIMARY,
                            tooltip="Log Out",
                            on_click=self.logout
                        ),
                        ft.VerticalDivider(width=10),
                        connect_btn
                    ], spacing=15)
                ]
            )
        )

    def build_sidebar(self):
        # LEFT UP: Profile Section
        profile_card = styles.get_postcard_container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.PERSON, color=styles.PRIMARY, size=16),
                    ft.Text("MY PROFILE", size=13, weight=ft.FontWeight.BOLD, color=styles.TEXT_DARK)
                ], spacing=5),
                ft.Text(f"Name: {self.user['name']}", size=12, color=styles.TEXT_DARK, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(f"Region: {self.user.get('region', 'UTC')}", size=12, color=styles.TEXT_DARK, overflow=ft.TextOverflow.ELLIPSIS),
                ft.ElevatedButton(
                    "Edit Profile",
                    on_click=self.show_edit_profile_dialog,
                    bgcolor=styles.PRIMARY,
                    color=ft.Colors.WHITE,
                    height=30,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15), text_style=ft.TextStyle(size=11))
                )
            ], spacing=8, tight=True),
            padding=15
        )

        # LEFT DOWN: Scrollable Bonds Section
        bonds_list = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=8
        )
        
        if not self.bonds:
            bonds_list.controls.append(
                ft.Container(
                    content=ft.Text("No bonds created yet. Connect with someone!", size=11, color="#8B5F6C", text_align=ft.TextAlign.CENTER),
                    padding=20,
                    alignment=ft.alignment.Alignment(0, 0)
                )
            )
        else:
            for b in self.bonds:
                is_selected = (b['id'] == self.selected_bond_id)
                bonds_list.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.FAVORITE if is_selected else ft.Icons.FAVORITE_BORDER, color=styles.PRIMARY, size=16),
                            ft.Text(b['partner_name'], size=13, weight=ft.FontWeight.BOLD, color=styles.TEXT_DARK, overflow=ft.TextOverflow.ELLIPSIS)
                        ], spacing=10),
                        bgcolor=styles.ACCENT if is_selected else "#FFFFFB",
                        border=ft.Border.all(1.5, styles.PRIMARY if is_selected else "#EAE0E2"),
                        border_radius=8,
                        padding=12,
                        on_click=lambda e, bond_id=b['id'], partner=b['partner_name']: self.select_bond(bond_id, partner)
                    )
                )

        bonds_section = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.LINK, color=styles.PRIMARY, size=16),
                ft.Text("BONDS", size=13, weight=ft.FontWeight.BOLD, color=styles.TEXT_DARK)
            ], spacing=5),
            ft.Container(
                content=bonds_list,
                expand=True
            )
        ], spacing=10, expand=True)

        return ft.Column([
            profile_card,
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            bonds_section
        ], expand=True, spacing=0)

    def select_bond(self, bond_id, partner_name):
        self.selected_bond_id = bond_id
        self.selected_partner_name = partner_name
        
        # Load events for bond
        all_events = db.fetch_bond_events(bond_id)
        print(f"DEBUG select_bond: fetched {len(all_events)} events for bond {bond_id}", flush=True)
        
        # Filter events for CURRENT WEEK IN USER'S LOCAL TIMEZONE
        tz_name = self.user.get('region', 'UTC')
        week_days = get_week_days(tz_name)
        week_start_utc = week_days[0].astimezone(pytz.utc)
        week_end_utc = (week_days[0] + datetime.timedelta(days=7)).astimezone(pytz.utc)
        print(f"DEBUG select_bond: region={tz_name}, week_start_utc={week_start_utc}, week_end_utc={week_end_utc}", flush=True)
        
        self.events = []
        for ev in all_events:
            try:
                ev_start = datetime.datetime.fromisoformat(ev['start_time'].replace('Z', '+00:00'))
                in_range = week_start_utc <= ev_start < week_end_utc
                print(f"DEBUG select_bond:   event '{ev['title']}' start={ev['start_time']} parsed={ev_start} in_range={in_range}", flush=True)
                if in_range:
                    self.events.append(ev)
            except Exception as ex:
                print(f"DEBUG select_bond:   event parse error: {ex}", flush=True)
                # Include as fallback if string is simple
                self.events.append(ev)
        
        print(f"DEBUG select_bond: {len(self.events)} events passed filter", flush=True)
                
        # Re-render main layout
        self.sidebar_container.content = self.build_sidebar()
        self.main_content_container.content = self.build_body()
        self.page.update()

    def build_body(self):
        if not self.selected_bond_id:
            # CENTER: Kitsune Idle Card
            chibi = KitsuneChibi(size=200, is_success_mode=False)
            return ft.Container(
                content=ft.Column([
                    chibi,
                    ft.Text("Loom & Link", size=30, weight=ft.FontWeight.BOLD, color=styles.PRIMARY),
                    ft.Container(
                        content=ft.Text(
                            "Welcome back, sweetheart! Select a bond from the list on the left to see your shared schedule, or press CONNECT in the top right to start a new pairing together. ♥",
                            color=styles.TEXT_DARK,
                            size=13,
                            text_align=ft.TextAlign.CENTER
                        ),
                        padding=15,
                        width=450,
                    )
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.Alignment(0, 0),
                expand=True
            )
            
        # Select bond schedule grid
        return ft.Container(
            expand=True,
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.FAVORITE, color=styles.PRIMARY, size=20),
                    ft.Text(f"Sharing hearts with {self.selected_partner_name}", size=18, weight=ft.FontWeight.BOLD, color=styles.TEXT_DARK),
                    ft.IconButton(
                        icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                        icon_color=styles.PRIMARY,
                        icon_size=22,
                        tooltip="Add Long Event",
                        on_click=self.show_add_long_event_dialog
                    )
                ], spacing=8),
                ft.Container(
                    expand=True,
                    padding=5,
                    content=self.build_schedule_grid()
                )
            ], spacing=15, expand=True)
        )

    def build_schedule_grid(self):
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        dates = get_week_days(self.user.get('region', 'UTC'))
        slots = get_time_slots()
        
        header_row = ft.Row(
            spacing=8,
            controls=[ft.Container(width=55)] + [
                ft.Container(
                    expand=True,
                    bgcolor="#FFFFFB",
                    border=ft.Border.all(1.0, "#FFD1DC"),
                    border_radius=8,
                    padding=6,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=2,
                        controls=[
                            ft.Text(day, weight=ft.FontWeight.BOLD, color=styles.PRIMARY, size=13),
                            ft.Text(date.strftime("%d %b"), size=11, color="#8B5F6C")
                        ]
                    )
                ) for day, date in zip(days, dates)
            ]
        )
        
        week_start_local = dates[0]
        week_end_local = dates[6] + datetime.timedelta(days=1)
        
        # Prepare event map: {(day_idx, slot): event}
        event_map = {}
        for event in self.events:
            try:
                local_start = get_local_time(event['start_time'], self.user.get('region', 'UTC'))
                local_end = get_local_time(event['end_time'], self.user.get('region', 'UTC'))
                
                # Step through in 30-minute intervals
                curr = local_start
                while curr < local_end:
                    if week_start_local <= curr < week_end_local:
                        day_idx = curr.weekday()
                        hour = curr.hour
                        minute = "00" if curr.minute < 30 else "30"
                        slot_key = f"{hour:02d}:{minute}"
                        event_map[(day_idx, slot_key)] = event
                    curr += datetime.timedelta(minutes=30)
            except Exception as e:
                # Fallback to single slot
                local_start = get_local_time(event['start_time'], self.user.get('region', 'UTC'))
                if week_start_local <= local_start < week_end_local:
                    day_idx = local_start.weekday()
                    hour = local_start.hour
                    minute = "00" if local_start.minute < 30 else "30"
                    slot_key = f"{hour:02d}:{minute}"
                    event_map[(day_idx, slot_key)] = event

        grid_rows = []
        for slot in slots:
            row_controls = [ft.Container(width=55, content=ft.Text(slot, size=11, weight=ft.FontWeight.W_500, color="#8B5F6C"))]
            for d in range(7):
                cell_content = None
                bgcolor = ft.Colors.with_opacity(0.1, "#FFFFFB")
                border_color = ft.Colors.with_opacity(0.1, "#FF9EB5")
                
                if (d, slot) in event_map:
                    ev = event_map[(d, slot)]
                    color_key = list(styles.PASTEL_PALETTE.keys())[ev.get('color_index', 0)]
                    bgcolor = styles.PASTEL_PALETTE[color_key]
                    border_color = styles.PRIMARY
                    cell_content = ft.Text(
                        ev['title'], 
                        size=10, 
                        weight=ft.FontWeight.BOLD, 
                        color=styles.TEXT_DARK, 
                        no_wrap=True,
                        overflow=ft.TextOverflow.ELLIPSIS
                    )

                row_controls.append(
                    ft.Container(
                        expand=True,
                        height=35,
                        bgcolor=bgcolor,
                        content=cell_content,
                        alignment=ft.alignment.Alignment(0, 0),
                        border=ft.Border.all(1.0, border_color),
                        on_click=lambda e, day=d, time=slot: self.on_slot_click(day, time),
                        border_radius=6,
                        animate_scale=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT)
                    )
                )
            grid_rows.append(ft.Row(spacing=8, controls=row_controls))

        return ft.Column(
            controls=[
                header_row,
                ft.Column(
                    controls=grid_rows,
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                    spacing=8
                )
            ],
            expand=True,
            spacing=10
        )

    def on_slot_click(self, day, time):
        title_field = ft.TextField(label="Activity Name", **styles.LOVE_INPUT_STYLE)
        desc_field = ft.TextField(label="Description", multiline=True, **styles.LOVE_INPUT_STYLE)
        color_dropdown = ft.Dropdown(
            label="Pick a Color",
            options=[ft.dropdown.Option(k) for k in styles.PASTEL_PALETTE.keys()],
            value="strawberry",
            **styles.LOVE_INPUT_STYLE
        )
        
        def on_add_click(e):
            try:
                print(f"DEBUG: on_add_click triggered for day={day}, time={time}", flush=True)
                self.save_event(
                    dialog,
                    day,
                    time,
                    title_field.value,
                    desc_field.value,
                    color_dropdown.value
                )
            except Exception as ex:
                print(f"Exception in on_add_click: {ex}", flush=True)
                self.show_snack(f"Failed to save event: {ex}", is_error=True)

        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.EDIT_CALENDAR_OUTLINED, color=styles.PRIMARY),
                ft.Text(f"Add Activity ({time})", color=styles.TEXT_DARK, weight=ft.FontWeight.BOLD)
            ], spacing=5),
            content=ft.Container(
                content=ft.Column([
                    title_field,
                    desc_field,
                    color_dropdown
                ], tight=True, spacing=15),
                width=320
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.close_dialog(dialog), style=ft.ButtonStyle(color=styles.TEXT_DARK)),
                ft.ElevatedButton("Add to Schedule", on_click=on_add_click, bgcolor=styles.PRIMARY, color=ft.Colors.WHITE)
            ],
            bgcolor="#FFFDFE",
            shape=ft.RoundedRectangleBorder(radius=16)
        )
        self.show_dialog(dialog)

    def save_event(self, dialog, day, time_slot, title, desc, color_key):
        print(f"DEBUG: save_event called: day={day}, time_slot={time_slot}, title={title}, desc={desc}, color_key={color_key}", flush=True)
        if not title:
            self.show_snack("Activity name is required!", is_error=True)
            return
            
        try:
            # 1. Get dates of the current week
            week_days = get_week_days(self.user.get('region', 'UTC'))
            day_date = week_days[day]
            
            # 2. Parse time slot
            h, m = map(int, time_slot.split(":"))
            local_dt = datetime.datetime.combine(day_date.date(), datetime.time(h, m))
            
            # 3. Convert to UTC strings
            start_utc = to_utc_str(local_dt, self.user.get('region', 'UTC'))
            end_utc = to_utc_str(local_dt + datetime.timedelta(minutes=30), self.user.get('region', 'UTC'))
            
            color_index = list(styles.PASTEL_PALETTE.keys()).index(color_key)
            
            db.add_event(
                self.selected_bond_id,
                title,
                desc,
                start_utc,
                end_utc,
                color_index
            )
            
            self.close_dialog(dialog)
            self.show_snack("Event added! ♥")
            self.select_bond(self.selected_bond_id, self.selected_partner_name)
        except Exception as ex:
            self.show_snack(f"Failed to add event: {ex}", is_error=True)

    def show_add_long_event_dialog(self, e):
        title_field = ft.TextField(label="Activity Name", **styles.LOVE_INPUT_STYLE)
        desc_field = ft.TextField(label="Description", multiline=True, **styles.LOVE_INPUT_STYLE)
        
        days_map = {
            "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
            "Friday": 4, "Saturday": 5, "Sunday": 6
        }
        day_dropdown = ft.Dropdown(
            label="Day of the Week",
            options=[ft.dropdown.Option(d) for d in days_map.keys()],
            value="Monday",
            **styles.LOVE_INPUT_STYLE
        )
        
        slots = get_time_slots()
        start_dropdown = ft.Dropdown(
            label="Start Time (Your Region)",
            options=[ft.dropdown.Option(s) for s in slots],
            value="12:00",
            **styles.LOVE_INPUT_STYLE
        )
        
        end_slots = []
        for h in range(24):
            end_slots.append(f"{h:02d}:30")
            end_slots.append(f"{h+1:02d}:00")
            
        end_dropdown = ft.Dropdown(
            label="End Time (Your Region)",
            options=[ft.dropdown.Option(s) for s in end_slots],
            value="13:00",
            **styles.LOVE_INPUT_STYLE
        )
        
        color_dropdown = ft.Dropdown(
            label="Pick a Color",
            options=[ft.dropdown.Option(k) for k in styles.PASTEL_PALETTE.keys()],
            value="strawberry",
            **styles.LOVE_INPUT_STYLE
        )
        
        def on_add_long_click(e):
            try:
                day_val = day_dropdown.value
                day_idx = days_map.get(day_val, 0)
                print(f"DEBUG: on_add_long_click triggered: day={day_val} (idx={day_idx}), start={start_dropdown.value}, end={end_dropdown.value}", flush=True)
                self.save_long_event(
                    dialog,
                    day_idx,
                    start_dropdown.value,
                    end_dropdown.value,
                    title_field.value,
                    desc_field.value,
                    color_dropdown.value
                )
            except Exception as ex:
                print(f"Exception in on_add_long_click: {ex}", flush=True)
                self.show_snack(f"Failed to save event: {ex}", is_error=True)

        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.EDIT_CALENDAR_OUTLINED, color=styles.PRIMARY),
                ft.Text("Add Long Activity", color=styles.TEXT_DARK, weight=ft.FontWeight.BOLD)
            ], spacing=5),
            content=ft.Container(
                content=ft.Column([
                    title_field,
                    desc_field,
                    day_dropdown,
                    ft.Row([start_dropdown, end_dropdown], spacing=10),
                    color_dropdown
                ], tight=True, spacing=15),
                width=420
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.close_dialog(dialog), style=ft.ButtonStyle(color=styles.TEXT_DARK)),
                ft.ElevatedButton("Add to Schedule", 
                    on_click=on_add_long_click,
                    bgcolor=styles.PRIMARY, color=ft.Colors.WHITE
                )
            ],
            bgcolor="#FFFDFE",
            shape=ft.RoundedRectangleBorder(radius=16)
        )
        self.show_dialog(dialog)

    def save_long_event(self, dialog, day, start_time, end_time, title, desc, color_key):
        print(f"DEBUG: save_long_event called: day={day}, start_time={start_time}, end_time={end_time}, title={title}, desc={desc}, color_key={color_key}", flush=True)
        if not title:
            self.show_snack("Activity name is required!", is_error=True)
            return
            
        try:
            sh, sm = map(int, start_time.split(":"))
            eh, em = map(int, end_time.split(":"))
            
            if eh < sh or (eh == sh and em <= sm):
                self.show_snack("End time must be after start time!", is_error=True)
                return
                
            week_days = get_week_days(self.user.get('region', 'UTC'))
            day_date = week_days[day]
            
            local_start = datetime.datetime.combine(day_date.date(), datetime.time(sh, sm))
            if eh == 24:
                local_end = datetime.datetime.combine(day_date.date(), datetime.time(23, 59)) + datetime.timedelta(minutes=1)
            else:
                local_end = datetime.datetime.combine(day_date.date(), datetime.time(eh, em))
            
            start_utc = to_utc_str(local_start, self.user.get('region', 'UTC'))
            end_utc = to_utc_str(local_end, self.user.get('region', 'UTC'))
            
            color_index = list(styles.PASTEL_PALETTE.keys()).index(color_key)
            
            db.add_event(
                self.selected_bond_id,
                title,
                desc,
                start_utc,
                end_utc,
                color_index
            )
            
            self.close_dialog(dialog)
            self.show_snack("Long event added! ♥")
            self.select_bond(self.selected_bond_id, self.selected_partner_name)
        except Exception as ex:
            self.show_snack(f"Failed to add event: {ex}", is_error=True)

    def run_schedule_refresh_loop(self):
        while self.user is not None and getattr(self, "refresh_thread_started", False):
            time.sleep(8)
            if self.user is None or not getattr(self, "refresh_thread_started", False):
                break
            if self.selected_bond_id:
                try:
                    all_events = db.fetch_bond_events(self.selected_bond_id)
                    tz_name = self.user.get('region', 'UTC')
                    week_days = get_week_days(tz_name)
                    week_start_utc = week_days[0].astimezone(pytz.utc)
                    week_end_utc = (week_days[0] + datetime.timedelta(days=7)).astimezone(pytz.utc)
                    
                    new_events = []
                    for ev in all_events:
                        try:
                            ev_start = datetime.datetime.fromisoformat(ev['start_time'].replace('Z', '+00:00'))
                            if week_start_utc <= ev_start < week_end_utc:
                                new_events.append(ev)
                        except Exception:
                            new_events.append(ev)
                            
                    # Check if the list has changed
                    if len(new_events) != len(self.events) or json.dumps(new_events, sort_keys=True) != json.dumps(self.events, sort_keys=True):
                        self.events = new_events
                        self.main_content_container.content = self.build_body()
                        self.page.update()
                except Exception as ex:
                    print(f"Error in background schedule refresh: {ex}")
        self.refresh_thread_started = False

    # --- PROFILE EDITING ---
    def show_edit_profile_dialog(self, e):
        name_field = ft.TextField(label="Name (Username)", value=self.user['name'], **styles.LOVE_INPUT_STYLE)
        password_field = ft.TextField(label="Password", value=self.user.get('password', self.user.get('secret_code', '')), password=True, can_reveal_password=True, **styles.LOVE_INPUT_STYLE)
        
        region_dropdown = ft.Dropdown(
            label="Region (Timezone)",
            options=[ft.dropdown.Option(r) for r in ["Europe/Rome", "America/New_York", "UTC", "Asia/Tokyo", "Europe/London", "Australia/Sydney"]],
            value=self.user.get('region', 'Europe/Rome'),
            **styles.LOVE_INPUT_STYLE
        )
        
        edit_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.SETTINGS, color=styles.PRIMARY),
                ft.Text("Edit Profile Settings", color=styles.TEXT_DARK, weight=ft.FontWeight.BOLD)
            ], spacing=5),
            content=ft.Container(
                content=ft.Column([
                    name_field,
                    password_field,
                    region_dropdown
                ], tight=True, spacing=15),
                width=320
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.close_dialog(edit_dialog), style=ft.ButtonStyle(color=styles.TEXT_DARK)),
                ft.ElevatedButton("Save Changes", on_click=lambda e: self.save_profile_changes(edit_dialog, name_field, password_field, region_dropdown), bgcolor=styles.PRIMARY, color=ft.Colors.WHITE)
            ],
            bgcolor="#FFFDFE",
            shape=ft.RoundedRectangleBorder(radius=16)
        )
        self.show_dialog(edit_dialog)

    def save_profile_changes(self, edit_dialog, name_field, password_field, region_dropdown):
        new_name = name_field.value.strip()
        new_password = password_field.value.strip()
        new_region = region_dropdown.value
        
        if not new_name or not new_password:
            self.show_snack("Name and Password cannot be empty!", is_error=True)
            return
            
        if new_region != self.user.get('region', 'UTC'):
            # Show region warning dialog
            self.show_region_warning_dialog(new_name, new_password, new_region, edit_dialog)
        else:
            db.update_profile(self.user['id'], new_name, new_password, new_region)
            self.user['name'] = new_name
            self.user['password'] = new_password
            # Session update not needed in web mode
            self.close_dialog(edit_dialog)
            self.show_snack("Profile updated successfully!")
            self.show_main_screen()

    def show_region_warning_dialog(self, new_name, new_password, new_region, edit_dialog):
        warning_dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=styles.PRIMARY),
                ft.Text("Change Region?", color=styles.TEXT_DARK, weight=ft.FontWeight.BOLD)
            ], spacing=5),
            content=ft.Text(
                "Are you sure you want to change your region? The tables with all your bonds might suffer changes.",
                color=styles.TEXT_DARK
            ),
            actions=[
                ft.TextButton("No, Cancel", on_click=lambda _: self.close_dialog(warning_dialog), style=ft.ButtonStyle(color=styles.TEXT_DARK)),
                ft.ElevatedButton("Yes, Change Region", 
                    on_click=lambda e: self.confirm_profile_update(new_name, new_password, new_region, warning_dialog, edit_dialog),
                    bgcolor=styles.PRIMARY, color=ft.Colors.WHITE
                )
            ],
            bgcolor="#FFFDFE",
            shape=ft.RoundedRectangleBorder(radius=16)
        )
        self.show_dialog(warning_dialog)

    def confirm_profile_update(self, new_name, new_password, new_region, warning_dialog, edit_dialog):
        db.update_profile(self.user['id'], new_name, new_password, new_region)
        self.user['name'] = new_name
        self.user['password'] = new_password
        self.user['region'] = new_region
        # Session update not needed in web mode
        
        self.close_dialog(warning_dialog)
        self.close_dialog(edit_dialog)
        self.show_snack("Profile and region updated successfully!")
        self.show_main_screen()

    # --- CONNECT FLOW & PAIRING ---
    def show_connect_dialog(self, e):
        self.pairing_dialog_open = True
        dialog_content = ft.Column(tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
        
        connect_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.FAVORITE, color=styles.PRIMARY),
                ft.Text("Connect Hearts", color=styles.TEXT_DARK, weight=ft.FontWeight.BOLD),
                ft.Icon(ft.Icons.FAVORITE, color=styles.PRIMARY)
            ], alignment=ft.MainAxisAlignment.CENTER),
            content=ft.Container(content=dialog_content, width=350, padding=10),
            actions=[
                ft.TextButton("Close", on_click=lambda _: self.close_connect_dialog(connect_dialog), style=ft.ButtonStyle(color=styles.TEXT_DARK))
            ],
            bgcolor="#FFFDFE",
            shape=ft.RoundedRectangleBorder(radius=16)
        )
        
        dialog_content.controls = [
            ft.Text(
                "To create a bond, you and your partner must both open this Connect menu at the same time. You will have 5 minutes to share your code, input it below, and establish your connection.",
                color=styles.TEXT_DARK,
                text_align=ft.TextAlign.CENTER,
                size=13
            ),
            ft.ElevatedButton(
                "Start Pairing",
                on_click=lambda e: self.start_pairing_countdown(connect_dialog, dialog_content),
                bgcolor=styles.PRIMARY,
                color=ft.Colors.WHITE,
                width=250,
                height=45
            )
        ]
        self.show_dialog(connect_dialog)

    def close_connect_dialog(self, dialog):
        self.pairing_dialog_open = False
        self.close_dialog(dialog)

    def start_pairing_countdown(self, dialog, content_col):
        pairing_code = db.generate_pairing_code(self.user['id'])
        if not pairing_code:
            content_col.controls = [ft.Text("Error generating code. Try again.", color=ft.Colors.RED)]
            self.page.update()
            return
            
        progress_ring = ft.ProgressRing(width=48, height=48, stroke_width=3, color=styles.PRIMARY, value=1.0)
        timer_text = ft.Text("Time Remaining: 5:00", size=13, weight=ft.FontWeight.BOLD, color=styles.TEXT_DARK)
        
        code_display = ft.Container(
            content=ft.Text(pairing_code, size=20, weight=ft.FontWeight.BOLD, color=styles.PRIMARY, selectable=True),
            padding=ft.padding.Padding(left=20, top=10, right=20, bottom=10),
            bgcolor=styles.ACCENT,
            border_radius=10,
            border=ft.Border.all(1.5, "#FF9EB5"),
            on_click=lambda _: self.copy_to_clipboard(pairing_code),
            tooltip="Click to copy code"
        )
        
        partner_code_input = ft.TextField(
            label="Partner's Code",
            text_align=ft.TextAlign.CENTER,
            autofocus=True,
            **styles.LOVE_INPUT_STYLE
        )
        
        submit_button = ft.ElevatedButton(
            "Connect",
            on_click=lambda e: self.submit_partner_code(partner_code_input.value, submit_button, partner_code_input),
            bgcolor=styles.PRIMARY,
            color=ft.Colors.WHITE,
            width=200,
            height=40
        )
        
        content_col.controls = [
            ft.Row([progress_ring, timer_text], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
            ft.Text("Your Pairing Code:", color=styles.TEXT_DARK, size=11, weight=ft.FontWeight.BOLD),
            code_display,
            ft.Text("Click the code to copy, or select and copy it manually.", size=10, color="#8B5F6C"),
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            ft.Text("Input your friend's or partner's code to connect.", size=11, color=styles.TEXT_DARK, weight=ft.FontWeight.BOLD),
            partner_code_input,
            submit_button
        ]
        self.page.update()
        
        # Countdown thread
        threading.Thread(target=self.run_pairing_loop, args=(dialog, progress_ring, timer_text), daemon=True).start()

    def submit_partner_code(self, code, button, text_field):
        if not code:
            self.show_snack("Please enter a code!", is_error=True)
            return
            
        success = db.submit_pairing_code(self.user['id'], code)
        if success:
            button.disabled = True
            button.text = "Submitted"
            text_field.disabled = True
            self.show_snack("Code submitted! Waiting for partner...")
            self.page.update()
        else:
            self.show_snack("Invalid or expired code. Please try again.", is_error=True)

    def run_pairing_loop(self, dialog, progress_ring, timer_text):
        total_seconds = 300
        start_bonds_count = len(db.fetch_user_bonds(self.user['id']))
        
        for i in range(total_seconds, -1, -1):
            if not self.pairing_dialog_open:
                break
                
            minutes = i // 60
            seconds = i % 60
            timer_text.value = f"Time Remaining: {minutes}:{seconds:02d}"
            progress_ring.value = i / total_seconds
            
            # Check for mutual pair every 3 seconds
            if i % 3 == 0:
                current_bonds = db.fetch_user_bonds(self.user['id'])
                if len(current_bonds) > start_bonds_count:
                    self.pairing_dialog_open = False
                    self.close_dialog(dialog)
                    
                    new_bond = current_bonds[-1]
                    self.show_pairing_success_dialog(new_bond['partner_name'], new_bond['id'])
                    break
                    
            self.page.update()
            time.sleep(1)
            
        if self.pairing_dialog_open and i == 0:
            timer_text.value = "Code expired!"
            progress_ring.value = 0
            self.page.update()

    def show_pairing_success_dialog(self, partner_name, bond_id):
        success_chibi = KitsuneChibi(size=140, is_success_mode=True)
        success_dialog = ft.AlertDialog(
            modal=True,
            content=ft.Container(
                content=ft.Column([
                    success_chibi,
                    ft.Text("SUCCESS!", size=24, color=styles.PRIMARY, weight=ft.FontWeight.BOLD),
                    ft.Text(f"You have connected with {partner_name}!\nYour shared schedule is ready.", text_align=ft.TextAlign.CENTER, color=styles.TEXT_DARK),
                ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=260,
                padding=10,
                alignment=ft.alignment.Alignment(0, 0)
            ),
            bgcolor="#FFFDFE",
            shape=ft.RoundedRectangleBorder(radius=16)
        )
        self.show_dialog(success_dialog)
        
        def select_and_refresh():
            time.sleep(3.5)
            self.close_dialog(success_dialog)
            self.select_bond(bond_id, partner_name)
            
        threading.Thread(target=select_and_refresh, daemon=True).start()

def main(page: ft.Page):
    app = LoomLinkApp(page)

if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER, port=8560)
