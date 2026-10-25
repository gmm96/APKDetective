"""
ttkbootstrap draws no focus mark on a button styled as a toolbutton (the filter pills): the layout of that
style has no focus element, unlike the one of a normal button. Without it, a pill that has the keyboard
focus can't be told from the rest.
"""

import ttkbootstrap as ttkb


class ToolbuttonFocusRing:
    @staticmethod
    def apply(style_name: str) -> None:
        """
        Adds the focus ring to a toolbutton style (such as "primary.Outline.Toolbutton"). A ttk layout
        belongs to a theme, so this has to be done again whenever the theme changes.
        """
        ttkb.Style().layout(
            style_name,
            [("Toolbutton.border", {"sticky": "nswe", "children": [
                ("Toolbutton.focus", {"sticky": "nswe", "children": [
                    ("Toolbutton.padding", {"sticky": "nswe", "children": [
                        ("Toolbutton.label", {"sticky": "nswe"}),
                    ]}),
                ]}),
            ]})],
        )
