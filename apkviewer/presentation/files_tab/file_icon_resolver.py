"""
Decides which icon file represents a node of the APK's file tree. It is pure
logic (no Tk, no files are read), so it is easy to test and the tree widget
does not need to know how an icon is chosen.

The order of the rules is:
  1. folders: a few have their own icon, the rest share the generic one;
  2. files recognised by their full name (AndroidManifest.xml);
  3. files recognised by their extension, from the table of known Android files;
  4. any other extension, by the main type of its MIME type (image, audio, video);
  5. the generic file icon.

The table in (3) must hold everything the MIME database does not know. The
database of the interpreter lacks, for instance, .webp, .ogg, .m4a and the
fonts, which are common in APKs, and it varies between platforms.
"""

import mimetypes

from apkviewer.domain.entities.file_node import FileNode


class FileIconResolver:
    GENERIC_FILE: str = "file.png"
    DIRECTORY: str = "directory.png"

    # Folders with an icon of their own, by their path inside the APK.
    _DIRECTORY_ICONS: dict[str, str] = {
        "assets": "assets.png",
    }

    # Files recognised by their full name (lower case) before looking at the extension.
    _FILE_NAME_ICONS: dict[str, str] = {
        "androidmanifest.xml": "manifest.png",
    }

    # Known extensions (lower case, without the dot) grouped by icon. A given extension
    # can only appear once: it is checked when the resolver is created.
    _EXTENSION_GROUPS: dict[str, frozenset[str]] = {
        "xml.png": frozenset({"xml"}),
        "dex.png": frozenset({"dex"}),
        "so.png": frozenset({"so"}),
        "json.png": frozenset({"json"}),
        "html.png": frozenset({"html", "htm"}),
        "config.png": frozenset({
            "arsc", "properties", "cfg", "conf", "ini", "yml", "yaml", "toml", "version",
        }),
        "rsa.png": frozenset({  # signature files, certificates and keys
            "rsa", "dsa", "ec", "sf", "mf",
            "pem", "pk8", "cer", "crt", "der", "p12", "pfx", "jks", "bks", "keystore",
        }),
        "font.png": frozenset({"ttf", "otf", "ttc", "woff", "woff2"}),
        "zip.png": frozenset({"zip", "jar", "aar", "apk", "tar", "gz", "tgz", "bz2", "xz", "7z"}),
        # Media that the MIME database of the interpreter does not know:
        "drawable.png": frozenset({"webp"}),
        "audio.png": frozenset({"ogg", "oga", "m4a", "flac", "mid", "midi", "amr", "wma"}),
        "video.png": frozenset({"mkv", "m4v"}),
    }

    # Main MIME type -> icon, for the extensions that are not in the table above.
    _MIME_ICONS: dict[str, str] = {
        "image": "drawable.png",
        "audio": "audio.png",
        "video": "video.png",
    }

    def __init__(self) -> None:
        self._extension_icons: dict[str, str] = self._invert(self._EXTENSION_GROUPS)
        # An instance with the interpreter's built-in table: the answers do not depend on
        # what the operating system has registered.
        self._mime_types: mimetypes.MimeTypes = mimetypes.MimeTypes()
        self._mime_cache: dict[str, str] = {}  # extension -> icon, one MIME lookup per extension

    def resolve(self, node: FileNode) -> str:
        """The name of the icon file (e.g. 'dex.png') that represents `node`."""
        if not node.is_file:
            return self._DIRECTORY_ICONS.get(node.path, self.DIRECTORY)
        named = self._FILE_NAME_ICONS.get(node.name.lower())
        if named is not None:
            return named
        extension = node.extension  # upper case, without the dot
        known = self._extension_icons.get(extension)
        if known is not None:
            return known
        return self._icon_from_mime(extension)

    def _icon_from_mime(self, extension: str) -> str:
        if not extension:
            return self.GENERIC_FILE
        icon = self._mime_cache.get(extension)
        if icon is None:
            mime_type, _ = self._mime_types.guess_type(f"file.{extension.lower()}")
            main_type = mime_type.split("/", 1)[0] if mime_type else ""
            icon = self._MIME_ICONS.get(main_type, self.GENERIC_FILE)
            self._mime_cache[extension] = icon
        return icon

    @staticmethod
    def _invert(groups: dict[str, frozenset[str]]) -> dict[str, str]:
        """{icon: extensions} -> {EXTENSION: icon}, with the keys as FileNode.extension gives them."""
        inverted: dict[str, str] = {}
        for icon, extensions in groups.items():
            for extension in extensions:
                key = extension.upper()
                if key in inverted:
                    raise ValueError(
                        f"The extension '.{extension}' is assigned to both {inverted[key]} and {icon}"
                    )
                inverted[key] = icon
        return inverted
