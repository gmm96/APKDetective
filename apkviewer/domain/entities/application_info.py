"""
Identity, SDK range and physical file metrics of an analyzed APK.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass()
class ApplicationInfo:
    app_name: str
    package_name: str
    version_name: str | None
    version_code: str | None
    min_sdk: str | None
    target_sdk: str | None
    max_sdk: str | None
    file_name: str | None
    file_path: str | None
    file_size: int | None
    last_modified: datetime | None
    debuggable: bool | None = None
    allow_backup: bool | None = None
    test_only: bool | None = None
    extract_native_libs: bool | None = None
    hardware_accelerated: bool | None = None
    cleartext_traffic_permitted: bool | None = None
    trust_user_certificates: bool | None = None
    certificate_pinning_enforced: bool | None = None
