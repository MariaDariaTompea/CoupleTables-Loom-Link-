import flet as ft

# --- PASTEL PALETTE FOR SCHEDULING (From Original App) ---
PASTEL_PALETTE = {
    "strawberry": "#FFB7B2", # Date Night
    "sky_blue": "#B2E2F2",   # Online Gaming
    "mint_green": "#B2F2BB", # Studying Together
    "lavender": "#D1B2F2",   # Sleep/Wind Down
    "lemon": "#FFF1B2",      # Morning Call
    "peach": "#FFDAC1",
    "lilac": "#E2F0CB",
    "salmon": "#FF9AA2",
    "aqua": "#C7CEEA",
    "vanilla": "#FFFFD8"
}

# --- PRIMARY AESTHETIC COLORS (Love & Cuteness) ---
PRIMARY = "#FF5E7E"        # Rose Pink
SECONDARY = "#FF9EB5"      # Soft Pink
ACCENT = "#FFE3E8"         # Light Blush
TEXT_DARK = "#4A2E35"      # Deep Espresso
BG_CREAM = "#FFF5F6"       # Soft Cream Pink
BG_CARD = "#FFFFFF"

# --- GLASSMORPHISM STYLES ---
GLASS_STYLE = {
    "bgcolor": ft.Colors.with_opacity(0.4, ft.Colors.WHITE),
    "border_radius": 15,
    "border": ft.Border.all(1.5, ft.Colors.with_opacity(0.3, "#FF9EB5")),
    "blur": ft.Blur(8, 8, ft.BlurStyle.OUTER),
    "padding": 20,
}

# --- CUTE UI STYLES ---
POSTCARD_STYLE = {
    "bgcolor": "#FFFFFB", # Soft writing paper color
    "border_radius": 12,
    "border": ft.Border.all(2.0, "#EAE0E2"),
    "shadow": ft.BoxShadow(
        blur_radius=15,
        color=ft.Colors.with_opacity(0.08, "#8B5F6C"),
        offset=ft.Offset(2, 4)
    ),
    "padding": 25,
}

LOVE_INPUT_STYLE = {
    "border_color": "#FFD1DC",
    "focused_border_color": "#FF5E7E",
    "focused_border_width": 2,
    "border_radius": 10,
    "label_style": ft.TextStyle(color="#8B5F6C", size=13),
    "text_style": ft.TextStyle(color=TEXT_DARK),
}

LOVE_BUTTON_STYLE = {
    "bgcolor": PRIMARY,
    "color": ft.Colors.WHITE,
    "height": 45,
    "border_radius": 22,
}

EVENT_CARD_STYLE = {
    "border_radius": 8,
    "padding": 5,
    "margin": 2,
}

def get_glass_container(content, **kwargs):
    style = GLASS_STYLE.copy()
    style.update(kwargs)
    return ft.Container(content=content, **style)

def get_postcard_container(content, **kwargs):
    style = POSTCARD_STYLE.copy()
    style.update(kwargs)
    return ft.Container(content=content, **style)
