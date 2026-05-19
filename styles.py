import flet as ft

# --- COLORS (From Documentation) ---
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

PRIMARY = "#FF6B6B"
SECONDARY = "#4ECDC4"
ACCENT = "#FFE66D"

# --- GLASSMORPHISM STYLES ---
GLASS_STYLE = {
    "bgcolor": ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
    "border_radius": 15,
    "border": ft.Border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.WHITE)),
    "blur": ft.Blur(10, 10, ft.BlurStyle.OUTER),
    "padding": 20,
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
