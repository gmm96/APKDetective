"""
An <intent-filter> of a component: the conditions under which it answers an intent.
"""

from dataclasses import dataclass

from apkdetective.domain.entities.manifest.intents.intent_data import IntentData


@dataclass(frozen=True)
class IntentFilter:
    actions: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()
    data: tuple[IntentData, ...] = ()
    auto_verify: bool = False  # android:autoVerify (API 23+): an App Link candidate
