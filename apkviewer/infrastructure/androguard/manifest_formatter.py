"""
Formats an APK's AndroidManifest.xml into pretty-printed text.
"""

from xml.dom import minidom

from androguard.core.apk import APK

from apkviewer.infrastructure.xml.lxml_serializer import LxmlSerializer
from apkviewer.infrastructure.xml.xml_serializer import XmlSerializer


class ManifestFormatter:
    def __init__(self, serializer: XmlSerializer | None = None) -> None:
        self._serializer: XmlSerializer = serializer or LxmlSerializer()

    def format(self, apk: APK) -> str:
        try:
            xml_root = apk.get_android_manifest_xml()
            if xml_root is None:
                return "Manifest XML is missing or corrupted."

            raw_xml = self._serializer.serialize(xml_root)
            pretty = minidom.parseString(raw_xml).toprettyxml(indent="    ")
            # "\n" and not os.linesep: this text goes into a Tk Text widget, where a "\r" would be a stray character.
            return "\n".join(line for line in pretty.splitlines() if line.strip())
        except Exception as exc:  # pylint: disable=broad-except
            return f"Error processing Manifest:\n{exc}"
