#!/usr/bin/env python3
"""Catch current-product name regressions in source translations and built apps.

License notices and the explicit upstream attribution retain their real names.
Run without arguments for source checks, or with --app for each shipping bundle.
"""
import argparse
import json
import plistlib
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ATTRIBUTION = "Built on Swiftfin. An independent app by Ralleur."
LEGACY = re.compile(r"(?i:swiftfin|\bvela\b)|\bKurtz\b|\bKURTZ\b")


def read_strings(path):
    return json.loads(subprocess.check_output(["plutil", "-convert", "json", "-o", "-", str(path)]))


def check_strings(paths):
    count = 0
    errors = []
    for path in paths:
        for key, value in read_strings(path).items():
            count += 1
            if key != ATTRIBUTION and LEGACY.search(value):
                errors.append(f"{path}: {key}: {value}")
    if errors:
        raise SystemExit("Current-product branding regressions:\n" + "\n".join(errors))
    return count


def verify_app(app):
    mac = (app / "Contents/Info.plist").exists()
    info = plistlib.loads((app / ("Contents/Info.plist" if mac else "Info.plist")).read_bytes())
    resources = app / "Contents/Resources" if mac else app
    assert app.name == "kurtz.app"
    assert all(info[key] == "kurtz" for key in ("CFBundleName", "CFBundleDisplayName", "CFBundleExecutable"))
    assert info["CFBundleIdentifier"] == ("com.ralleur.vela.mac" if mac else "com.ralleur.vela")
    schemes = {value for entry in info["CFBundleURLTypes"] for value in entry["CFBundleURLSchemes"]}
    assert {"kurtz", "vela"} <= schemes
    for font in ("Sora-Regular.ttf", "Sora-SemiBold.ttf", "Sora-Bold.ttf"):
        assert font in info["UIAppFonts"] and (resources / font).is_file(), font
    assert "CFBundledisplayTitle" not in info
    if info.get("UIDeviceFamily") == [3]:
        assert info["UILaunchStoryboardName"] == "KurtzLaunchScreen"
        assert (resources / "KurtzLaunchScreen.storyboardc").is_dir()
        assert info["TVTopShelfImage"]
    count = check_strings(path for path in resources.glob("*.lproj/*.strings")
                          if path.name in {"Localizable.strings", "Kurtz.strings", "InfoPlist.strings"})
    print(f"PASS {app}: kurtz {info['CFBundleShortVersionString']} ({info['CFBundleVersion']}), "
          f"{count} localized values, Sora, app identity and launch resources")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, action="append")
    args = parser.parse_args()
    if args.app:
        for app in args.app:
            verify_app(app)
    else:
        paths = list((ROOT / "Translations").glob("*.lproj/*.strings"))
        paths += list((ROOT / "Shared/Resources").glob("*.lproj/Kurtz.strings"))
        print(f"PASS source branding: {check_strings(paths)} localized values")


if __name__ == "__main__":
    main()
