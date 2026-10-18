import ttkbootstrap as ttkb

from apkviewer.presentation.common.auto_hide_scrollbar import AutoHideScrollbar
from apkviewer.presentation.config.layout import FIELD_PADX, FIELD_PADY


class AutoScrolledText(ttkb.ScrolledText):
    """
    A ScrolledText widget whose scrollbars are only shown while the content overflows.

    ttkbootstrap reserves a fixed lane for each bar (a minsize on the row or column that holds
    it), so showing or hiding a bar never changes the size of the text. That is what stops the
    visibility from feeding back into the layout (a bar appears -> less room -> another bar
    appears...): those lanes must stay. The grid options of the bars are not repeated here
    either; hiding a bar remembers them and showing it again restores them.
    """

    def __init__(self, *args, **kwargs) -> None:
        # Ensure horizontal scrollbar is requested by default
        kwargs.setdefault("hbar", True)
        super().__init__(*args, **kwargs)

        self.text.configure(padx=FIELD_PADX, pady=FIELD_PADY)

        # ttkbootstrap grids the bars as soon as it creates them: start with both hidden and
        # let the first scroll report of the text decide which ones the content really needs.
        self.hide_scrollbars()
        if self.hbar is not None:
            self.text.configure(xscrollcommand=AutoHideScrollbar(self.hbar).scroll_command)
        if self.vbar is not None:
            self.text.configure(yscrollcommand=AutoHideScrollbar(self.vbar).scroll_command)
