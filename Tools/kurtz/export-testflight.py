#!/usr/bin/env python3
"""Export an existing signed archive for internal TestFlight; upload only with --upload."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import subprocess
import tempfile
import zipfile


def prepare_framework_architectures(archive, output, certificate):
    """Thin a copied archive to the main executable's architectures, then re-sign."""
    archive_info = plistlib.loads((archive / "Info.plist").read_bytes())
    relative_app = Path("Products") / archive_info["ApplicationProperties"]["ApplicationPath"]
    app = archive / relative_app
    info = plistlib.loads((app / "Info.plist").read_bytes())
    def architectures(binary):
        return set(subprocess.check_output(["lipo", "-archs", str(binary)], text=True).split())
    app_archs = architectures(app / info["CFBundleExecutable"])
    if app_archs != {"arm64"}:
        raise SystemExit(f"Expected an arm64 device archive; found {sorted(app_archs)}")
    changes = []
    for framework in sorted((app / "Frameworks").glob("*.framework")):
        framework_info = plistlib.loads((framework / "Info.plist").read_bytes())
        binary = framework / framework_info["CFBundleExecutable"]
        archs = architectures(binary)
        if not app_archs <= archs:
            raise SystemExit(f"{framework.name} is missing the app's device architecture")
        extra = archs - app_archs
        if extra:
            changes.append((framework.relative_to(archive), binary.relative_to(archive), sorted(extra)))
    if not changes:
        return archive, []
    if not certificate:
        raise SystemExit("Embedded frameworks need thinning; provide the existing local --certificate-sha1")
    prepared = output / "prepared.xcarchive"
    if prepared.exists():
        raise SystemExit("Use a fresh output directory; prepared.xcarchive already exists")
    subprocess.run(["ditto", str(archive), str(prepared)], check=True)
    records = []
    for relative_framework, relative_binary, extras in changes:
        binary = prepared / relative_binary
        before = hashlib.sha256(binary.read_bytes()).hexdigest()
        temporary = binary.with_name(binary.name + ".thinned")
        command = ["lipo", str(binary)]
        for arch in extras:
            command += ["-remove", arch]
        subprocess.run(command + ["-output", str(temporary)], check=True)
        temporary.replace(binary)
        if architectures(binary) != app_archs:
            raise SystemExit("Framework thinning did not preserve the required architectures")
        subprocess.run(["codesign", "--force", "--sign", certificate,
                        "--preserve-metadata=identifier,entitlements,requirements,flags,runtime",
                        str(prepared / relative_framework)], check=True)
        records.append({"framework": relative_framework.name, "removed_architectures": extras,
                        "original_sha256": before, "prepared_sha256": hashlib.sha256(binary.read_bytes()).hexdigest()})
    subprocess.run(["codesign", "--force", "--sign", certificate,
                    "--preserve-metadata=identifier,entitlements,requirements,flags,runtime",
                    str(prepared / relative_app)], check=True)
    subprocess.run(["codesign", "--verify", "--deep", "--strict", str(prepared / relative_app)], check=True)
    return prepared, records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("platform", choices=["ios", "tvos"])
    parser.add_argument("archive", type=Path)
    parser.add_argument("--team", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--key", type=Path, help="Existing App Store Connect API private key")
    parser.add_argument("--key-id")
    parser.add_argument("--issuer-file", type=Path, help="File containing the API issuer ID")
    parser.add_argument("--profile", type=Path, help="Installed distribution provisioning profile")
    parser.add_argument("--certificate-sha1", help="Existing local distribution signing identity")
    parser.add_argument("--upload", action="store_true", help="Upload for internal testing only")
    args = parser.parse_args()
    archive = args.archive.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    archive, architecture_adjustments = prepare_framework_architectures(archive, output, args.certificate_sha1)
    with (archive / "Info.plist").open("rb") as stream:
        archive_info = plistlib.load(stream)
    app = archive / "Products" / archive_info["ApplicationProperties"]["ApplicationPath"]
    subprocess.run(["python3", str(Path(__file__).with_name("verify-apple-build.py")), args.platform, str(app)], check=True)
    subprocess.run(["codesign", "--verify", "--deep", "--strict", str(app)], check=True)
    with (app / "Info.plist").open("rb") as stream:
        info = plistlib.load(stream)
    if b"KurtzCheckFixture" in (app / info["CFBundleExecutable"]).read_bytes():
        parser.error("Refusing a build containing the debug playback harness")
    supplied = [args.key, args.key_id, args.issuer_file]
    if any(supplied) and not all(supplied):
        parser.error("Provide --key, --key-id and --issuer-file together")
    if bool(args.profile) != bool(args.certificate_sha1):
        parser.error("Provide --profile and --certificate-sha1 together")
    options = {
        "method": "app-store-connect",
        "destination": "upload" if args.upload else "export",
        "teamID": args.team,
        "signingStyle": "automatic",
        "testFlightInternalTestingOnly": True,
        "manageAppVersionAndBuildNumber": False,
        "uploadSymbols": True,
        "generateAppStoreInformation": True,
    }
    if args.profile:
        decoded = subprocess.run(["security", "cms", "-D", "-i", str(args.profile.resolve(strict=True))],
                                 capture_output=True, check=True)
        profile = plistlib.loads(decoded.stdout)
        expected_id = args.team + "." + info["CFBundleIdentifier"]
        if profile["Entitlements"].get("application-identifier") != expected_id:
            parser.error("Provisioning profile belongs to another app or team")
        options.update({"signingStyle": "manual", "signingCertificate": args.certificate_sha1,
                        "provisioningProfiles": {info["CFBundleIdentifier"]: profile["UUID"]}})
    options_path = output / "ExportOptions.plist"
    with options_path.open("wb") as stream:
        plistlib.dump(options, stream)
    command = ["xcodebuild", "-exportArchive", "-archivePath", str(archive),
               "-exportPath", str(output), "-exportOptionsPlist", str(options_path),
               "-allowProvisioningUpdates"]
    if args.key:
        command += ["-authenticationKeyPath", str(args.key.resolve(strict=True)),
                    "-authenticationKeyID", args.key_id,
                    "-authenticationKeyIssuerID", args.issuer_file.read_text().strip()]
    log = output / ("upload.log" if args.upload else "export.log")
    # Never print the private key or authentication arguments. Keep diagnostic
    # output local: Xcode may include account identifiers and signing metadata.
    print(f"{'Uploading' if args.upload else 'Exporting'} {args.platform} "
          f"{info['CFBundleShortVersionString']} ({info['CFBundleVersion']}); internal TestFlight only.", flush=True)
    with log.open("w") as stream:
        os.chmod(log, 0o600)
        result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT)
    record = {
        "platform": args.platform,
        "bundle_id": info["CFBundleIdentifier"],
        "version": info["CFBundleShortVersionString"],
        "build": info["CFBundleVersion"],
        "internal_only": True,
        "architecture_adjustments": architecture_adjustments,
        "action": "upload" if args.upload else "export",
        "xcode_exit_code": result.returncode,
        "apple_processing_verified": False,
        "note": "A successful upload still requires App Store Connect processing and tester availability checks.",
    }
    (output / "result.json").write_text(json.dumps(record, indent=2) + "\n")
    if result.returncode:
        raise SystemExit(f"Xcode failed. Inspect the local diagnostic log: {log}")
    if not args.upload:
        packages = list(output.glob("*.ipa"))
        if len(packages) != 1:
            raise SystemExit("Expected exactly one exported IPA")
        package = packages[0]
        with zipfile.ZipFile(package) as bundle:
            prefix = "Payload/kurtz.app/"
            exported = plistlib.loads(bundle.read(prefix + "Info.plist"))
            for field in ("CFBundleIdentifier", "CFBundleVersion", "CFBundleShortVersionString", "UIDeviceFamily"):
                if exported[field] != info[field]:
                    raise SystemExit(f"Export changed {field}")
            with tempfile.NamedTemporaryFile() as profile:
                profile.write(bundle.read(prefix + "embedded.mobileprovision"))
                profile.flush()
                decoded = subprocess.run(["security", "cms", "-D", "-i", profile.name], capture_output=True, check=True)
                provisioning = plistlib.loads(decoded.stdout)
            entitlements = provisioning["Entitlements"]
            if (provisioning.get("ProvisionedDevices") or provisioning.get("ProvisionsAllDevices")
                    or entitlements.get("get-task-allow") or not entitlements.get("beta-reports-active")):
                raise SystemExit("Export did not use a TestFlight distribution profile")
            if provisioning.get("TeamIdentifier") != [args.team]:
                raise SystemExit("Unexpected distribution team")
        record["ipa"] = package.name
        record["ipa_sha256"] = hashlib.sha256(package.read_bytes()).hexdigest()
        record["distribution_profile_verified"] = True
        (output / "result.json").write_text(json.dumps(record, indent=2) + "\n")
    print(f"Xcode completed. Record: {output / 'result.json'}")


if __name__ == "__main__":
    main()
