"""
Decides which icon file represents a node of the APK's file tree. It is pure
logic (no Tk, no files are read), so it is easy to test and the tree widget
does not need to know how an icon is chosen.

The order of the rules is:
  1. folders: a few have their own icon, the rest share the generic one;
  2. files recognised by their full name (AndroidManifest.xml, LICENSE...);
  3. files recognised by the folder they live in (META-INF/services/);
  4. files recognised by their extension, from the table of known files;
  5. any other extension, by the main type of its MIME type (image, audio, video, text);
  6. the generic file icon.

The table in (4) must hold everything the MIME database does not know. The
database of the interpreter lacks, for instance, .webp, .ogg, .m4a and the
fonts, which are common in APKs, and it varies between platforms.

An icon file that does not exist is not an error: FileIconProvider shows the
generic one instead, so a new group can be added before its icon is drawn.
"""

import mimetypes

from apkdetective.domain.entities.archive.file_node import FileNode


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
        "stamp-cert-sha256": "rsa.png",         # the hash of the signing certificate that Google Play adds
        "index.android.bundle": "code.png",     # the JavaScript (or Hermes) bundle of a React Native app
        **dict.fromkeys(
            (
                "license",
                "licence",
                "notice",
                "readme",
                "copying",
                "authors",
                "changelog",
                "dependencies",
                "copyright"
            ),
            "text.png",
        ),
    }

    # Files that are recognised by the folder they live in, wherever that folder sits in the APK.
    # Their names often carry dots that are not an extension (a Java class name, for instance).
    _FILE_FOLDER_ICONS: dict[str, str] = {
        "META-INF/services": "config.png",      # Java ServiceLoader registrations
    }

    # Known extensions (lower case, without the dot) grouped by icon. A given extension
    # can only appear once: it is checked when the resolver is created.
    _EXTENSION_GROUPS: dict[str, frozenset[str]] = {
        "xml.png": frozenset({"xml", "xsd", "xsl", "xslt"}),
        "dex.png": frozenset({
            "dex", "odex", "vdex",
            "prof", "profm",                    # ART baseline profiles, which list dex methods
        }),
        "so.png": frozenset({"so", "dll"}),     # native libraries, and the .NET assemblies of Unity / Xamarin
        "json.png": frozenset({"json", "geojson", "jsonl"}),
        "html.png": frozenset({"html", "htm", "xhtml"}),
        "config.png": frozenset({
            "arsc", "properties", "cfg", "conf", "cnf", "ini", "yml", "yaml", "toml", "version", "pro",
            "kotlin_module", "kotlin_builtins",
        }),
        "rsa.png": frozenset({                  # signature files, certificates and keys
            "rsa", "dsa", "ec", "sf", "mf",
            "pem", "pk8", "cer", "crt", "der", "p12", "pfx", "jks", "bks", "ks", "keystore",
            "p7b", "p7s", "crl", "csr", "key", "asc", "sig",
        }),
        "font.png": frozenset({"ttf", "otf", "ttc", "woff", "woff2", "eot", "fnt"}),
        "zip.png": frozenset({
            "zip", "jar", "aar", "apk", "tar", "gz", "tgz", "bz2", "xz", "7z", "rar",
            "lz4", "zst", "br", "lzma", "z",
            "aab", "apks", "apkm", "xapk",      # app bundles
            "obb", "pak", "pck", "lottie",      # expansion files and packed game / animation assets
        }),
        # Media that the MIME database of the interpreter does not know:
        "drawable.png": frozenset({"webp", "apng", "jfif", "jxl", "wbmp", "tga", "ktx", "ktx2", "astc", "dds", "pvr"}),
        "audio.png": frozenset({
            "ogg", "oga", "m4a", "flac", "mid", "midi", "amr", "awb", "wma", "mka", "weba", "ac3", "3ga",
            "xmf", "mxmf", "imy", "rtttl", "rtx", "ota",   # the ringtone and MIDI formats of Android
        }),
        "video.png": frozenset({"mkv", "m4v", "flv", "wmv", "ogv", "asf", "3pg"}),
        # Groups whose icon has to be drawn (until then they show the generic one):
        "text.png": frozenset({"txt", "md", "csv", "tsv", "log", "srt", "vtt"}),
        "code.png": frozenset({
            "js", "mjs", "css", "java", "kt", "kts", "smali", "aidl", "glsl", "frag", "vert", "shader", "sh", "py", "lua",
        }),
        "data.png": frozenset({                 # protobuf, machine learning models and opaque binary data
            "pb", "pbf", "proto", "textproto", "binarypb", "bin", "dat",
            "tflite", "onnx", "pt", "ptl", "pte", "traineddata",
        }),
        "database.png": frozenset({"db", "sqlite", "sqlite3", "db3", "realm"}),
        "document.png": frozenset({"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "odt", "ods", "odp", "rtf", "epub",}),
    }

    # Main MIME type -> icon, for the extensions that are not in the table above.
    _MIME_ICONS: dict[str, str] = {
        "image": "drawable.png",
        "audio": "audio.png",
        "video": "video.png",
        "text": "text.png",
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
        by_name = self._FILE_NAME_ICONS.get(node.name.lower())
        if by_name is not None:
            return by_name
        by_folder = self._icon_from_folder(node.path)
        if by_folder is not None:
            return by_folder
        extension = node.extension  # upper case, without the dot
        known = self._extension_icons.get(extension)
        if known is not None:
            return known
        return self._icon_from_mime(extension)

    def _icon_from_folder(self, path: str) -> str | None:
        parent = path.rpartition("/")[0]
        for folder, icon in self._FILE_FOLDER_ICONS.items():
            if parent == folder or parent.endswith(f"/{folder}"):
                return icon
        return None

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
