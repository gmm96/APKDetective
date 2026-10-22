"""
Gives the tree widget the image to show for each node of the file tree. The
choice of icon belongs to FileIconResolver; this class only loads the image
files, once each and only when a node needs them, and keeps them alive (Tk
shows an image only while a Python reference to it exists).
"""

from PIL import ImageTk

from apkviewer.domain.entities.archive.file_node import FileNode
from apkviewer.presentation.tabs.files_tab.file_icon_resolver import FileIconResolver
from apkviewer.presentation.common.icons.icon_loader import IconLoader


class FileIconProvider:
    ICON_DIR: str = "assets/icons/color"
    _PADDING_LEFT: int = 4
    _PADDING_RIGHT: int = 8

    def __init__(
        self,
        icon_loader: IconLoader | None = None,
        resolver: FileIconResolver | None = None,
    ) -> None:
        self._icon_loader: IconLoader = icon_loader or IconLoader()
        self._resolver: FileIconResolver = resolver or FileIconResolver()
        self._images: dict[str, ImageTk.PhotoImage] = {}

    def icon_for(self, node: FileNode) -> ImageTk.PhotoImage:
        return self._image(self._resolver.resolve(node))

    def _image(self, icon_name: str) -> ImageTk.PhotoImage:
        image = self._images.get(icon_name)
        if image is None:
            image = self._load(icon_name)
            self._images[icon_name] = image
        return image

    def _load(self, icon_name: str) -> ImageTk.PhotoImage:
        try:
            return self._icon_loader.load_icon(
                f"{self.ICON_DIR}/{icon_name}",
                padding_left=self._PADDING_LEFT,
                padding_right=self._PADDING_RIGHT,
            )
        except FileNotFoundError:
            # A missing icon file must not break the whole tab: show the generic one instead.
            if icon_name == FileIconResolver.GENERIC_FILE:
                raise
            return self._image(FileIconResolver.GENERIC_FILE)
