"""
What each flag of the Info tab controls, shown as its tooltip. They do not depend on the value of the flag.
"""


class FlagDescriptions:
    DEBUGGABLE: str = (
        "Controls whether the application can be debugged. True exposes the app to debugging tools and standard "
        "access; false secures it for production releases."
    )
    ALLOW_BACKUP: str = (
        "Controls whether app data can be backed up and restored via the system or adb. True allows data "
        "extraction; false protects local app data from standard backups."
    )
    TEST_ONLY: str = (
        "Indicates if the APK is built strictly for testing. True restricts installation to adb with the '-t' flag "
        "and prevents standard distribution; false allows normal installation."
    )
    HARDWARE_ACCELERATED: str = (
        "Determines if hardware-accelerated 2D rendering is enabled for the UI. True improves graphical "
        "performance; false relies on software rendering."
    )
    EXTRACT_NATIVE_LIBS: str = (
        "Determines if native libraries (.so files) are extracted to the filesystem upon installation (true) or "
        "read directly from the compressed APK to save storage space (false)."
    )
    CLEARTEXT_TRAFFIC_PERMITTED: str = (
        "Controls whether the app can communicate using unencrypted network protocols (like HTTP). True allows "
        "plaintext traffic; false enforces encrypted connections (HTTPS)."
    )
    TRUSTS_USER_CERTIFICATES: str = (
        "Indicates if the app trusts custom user-installed CA certificates. True allows easier traffic "
        "interception via proxies; false restricts trust to system-level certificates."
    )
    CERTIFICATE_PINNING_ENFORCED: str = (
        "Indicates if the application uses a Network Security Configuration to pin specific certificates or "
        "public keys, making Man-in-the-Middle (MITM) attacks harder to execute."
    )
