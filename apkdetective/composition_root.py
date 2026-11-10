"""
Composition root: the ONLY module that knows every layer.

It picks a concrete implementation for each port and injects them into
the application use cases and the front end. Replacing a layer (another
APK parser, another GUI toolkit, another storage) means changing this
file and nothing else.
"""

import os

import ttkbootstrap as ttkb

from apkdetective.application.analysis.analyze_apk import AnalyzeApk
from apkdetective.application.export.app_info_serializer import AppInfoSerializer
from apkdetective.application.files.entry_previewer import EntryPreviewer
from apkdetective.application.export.export_app_info import ExportAppInfo
from apkdetective.application.export.export_icon import ExportIcon
from apkdetective.application.export.extract_apk_entries import ExtractApkEntries
from apkdetective.application.appearance.resolve_color_scheme import ResolveColorScheme
from apkdetective.infrastructure.androguard.androguard_apk_inspector import AndroguardApkInspector
from apkdetective.infrastructure.androguard.dex.dex_analysis_starter import DexAnalysisStarter
from apkdetective.infrastructure.filesystem.local_file_writer import LocalFileWriter
from apkdetective.infrastructure.filesystem.temp_directory_workspace import TempDirectoryWorkspace
from apkdetective.infrastructure.platforms.platform_services_resolver import PlatformServicesResolver
from apkdetective.infrastructure.zip.zip_apk_extractor import ZipApkExtractor
from apkdetective.infrastructure.zip.zip_archive_reader import ZipArchiveReader
from apkdetective.ports.apk.apk_extractor_port import ApkExtractorPort
from apkdetective.ports.filesystem.file_writer_port import FileWriterPort
from apkdetective.ports.formatting.date_formatter_port import DateFormatterPort
from apkdetective.ports.formatting.size_formatter_port import SizeFormatterPort
from apkdetective.ports.system.platform_services_port import PlatformServicesPort
from apkdetective.presentation.app import ApkAnalyzerApp
from apkdetective.presentation.formatting.english_long_date_formatter import EnglishLongDateFormatter
from apkdetective.presentation.formatting.human_readable_size_formatter import HumanReadableSizeFormatter


def build_app(root: ttkb.App) -> ApkAnalyzerApp:
    platform_services: PlatformServicesPort = PlatformServicesResolver().resolve()
    apk_extractor: ApkExtractorPort = ZipApkExtractor()
    file_writer: FileWriterPort = LocalFileWriter()
    size_formatter: SizeFormatterPort = HumanReadableSizeFormatter()
    date_formatter: DateFormatterPort = EnglishLongDateFormatter()
    dex_analysis_starter: DexAnalysisStarter = DexAnalysisStarter(parallel=os.environ.get("APKDETECTIVE_PARALLEL") != "1")

    return ApkAnalyzerApp(
        root,
        analyze_apk=AnalyzeApk(AndroguardApkInspector(dex_analysis_starter=dex_analysis_starter), ZipArchiveReader()),
        extract_entries=ExtractApkEntries(apk_extractor),
        entry_previewer=EntryPreviewer(
            extractor=apk_extractor,
            workspace=TempDirectoryWorkspace(),
            file_opener=platform_services.create_os_file_opener(),
            clipboard_copier=platform_services.create_clipboard_file_copier(),
        ),
        export_app_info=ExportAppInfo(
            file_writer, AppInfoSerializer(size_formatter, date_formatter)
        ),
        export_icon=ExportIcon(file_writer),
        url_opener=platform_services.create_url_opener(),
        native_window_icon=platform_services.create_native_window_icon(),
        resolve_color_scheme=ResolveColorScheme(
            platform_services.create_system_color_scheme_detector()
        ),
        size_formatter=size_formatter,
        date_formatter=date_formatter,
    )
