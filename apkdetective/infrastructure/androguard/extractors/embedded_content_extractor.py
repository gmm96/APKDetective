"""
Scans the strings of the DEX files to extract hardcoded HTTP/HTTPS URLs.
"""

import re
from collections.abc import Iterable

from apkdetective.domain.entities.analysis.sections.embedded_content import EmbeddedContent


class EmbeddedContentExtractor:
    _URL_REGEX: re.Pattern = re.compile(r"https?://[\w\-\.\:]+(?:/[\w\-\.\:\/\?\=\&\%\#\+]*)?")

    def find_urls(self, strings: Iterable[str]) -> tuple[str, ...]:
        """The URLs written in the strings of one DEX file, sorted and without repeats."""
        urls: set[str] = set()
        for text in strings:
            if "http://" in text or "https://" in text:
                urls.update(self._URL_REGEX.findall(text))
        return tuple(sorted(urls))

    @staticmethod
    def combine(urls_per_file: Iterable[Iterable[str]]) -> EmbeddedContent:
        """The embedded content of the whole APK, from the URLs found in each of its DEX files."""
        return EmbeddedContent(urls=tuple(sorted({url for urls in urls_per_file for url in urls})))
