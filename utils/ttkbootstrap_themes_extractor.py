import ttkbootstrap as tb

# Initialize the Style object
style = tb.Style()

# Retrieve the list of all available theme names
available_themes = style.theme_names()

for theme in available_themes:
    # Apply the theme
    style.theme_use(theme)

    print(f"\n--- Theme: {theme.upper()} ---")

    # Get all colors as a dictionary using vars() on the colors object
    theme_colors = vars(style.colors)

    # Print each color and its hex value
    for color_name, hex_value in theme_colors.items():
        print(f"{color_name.ljust(12)}: {hex_value}")
