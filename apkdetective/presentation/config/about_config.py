"""
Project metadata.
"""

class AboutConfig:
    NAME: str = "APKDetective"
    DESCRIPTION: str = (
        "Desktop tool to inspect Android APK files: application identity and SDK range, "
        "signing certificates, permissions, components, exported intents, the decoded manifest "
        "and the contents of the package.\n\n"
        "Released under the GNU General Public License v3."
    )
    REPOSITORY_URL: str = "https://github.com/gmm96/APKDetective"
    ISSUES_URL: str = f"{REPOSITORY_URL}/issues"
