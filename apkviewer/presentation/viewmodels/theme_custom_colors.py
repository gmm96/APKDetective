from dataclasses import dataclass


@dataclass(frozen=True)
class ThemeCustomColors:
    xml_tag: str
    xml_attr: str
    xml_value: str
    xml_comment: str
