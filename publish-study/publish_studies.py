#!/usr/bin/env python3
"""Publish local cBioPortal study directories as <study_id>.tar.gz at an S3 bucket root."""
import argparse
import gzip
import hashlib
from pathlib import Path
import re
import tarfile
import tempfile


LFS_POINTER = b"version https://git-lfs.github.com/spec/v1"


def study_id(directory):
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError(f"Expected a study directory: {directory}")
    meta = directory / "meta_study.txt"
    if meta.is_symlink() or not meta.is_file():
        raise ValueError(f"Missing regular file: {meta}")
    ids = []
    for line in meta.read_text(encoding="utf-8-sig").splitlines():
        key, sep, value = line.partition(":")
        if sep and key.strip() == "cancer_study_identifier":
            ids.append(value.strip())
    if len(ids) != 1 or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", ids[0]):
        raise ValueError(f"Expected one valid cancer_study_identifier in {meta}")
    return ids[0]


def pack(directory, identifier, destination):
    # Stable member metadata and gzip header let repeated uploads reuse the object.
    with destination.open("wb") as raw, gzip.GzipFile(
        filename="", mode="wb", fileobj=raw, compresslevel=1, mtime=0
    ) as compressed, tarfile.open(fileobj=compressed, mode="w|") as archive:
        for path in sorted(directory.rglob("*")):
            relative = path.relative_to(directory)
            if ".git" in relative.parts:
                continue
            if path.is_symlink() or not (path.is_dir() or path.is_file()):
                raise ValueError(f"Unsupported file in study: {relative}")
            if path.is_dir():
                continue
            member = tarfile.TarInfo(f"{identifier}/{relative.as_posix()}")
            member.size = path.stat().st_size
            with path.open("rb") as stream:
                if stream.read(len(LFS_POINTER)) == LFS_POINTER:
                    raise ValueError(f"Fetch Git LFS content before publishing: {relative}")
                stream.seek(0)
                archive.addfile(member, stream)
    digest = hashlib.sha256()
    with destination.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def upload(client, bucket, archive, metadata):
    from botocore.exceptions import ClientError

    key = archive.name
    try:
        current = client.head_object(Bucket=bucket, Key=key)
    except ClientError as exc:
        if exc.response["ResponseMetadata"]["HTTPStatusCode"] != 404:
            raise
    else:
        if (current["ContentLength"] == archive.stat().st_size and
                all(current["Metadata"].get(k) == v for k, v in metadata.items())):
            return "Unchanged"
    client.upload_file(str(archive), bucket, key, ExtraArgs={
        "ContentType": "application/gzip", "Metadata": metadata,
    })
    return "Published"


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog=(
        "Example: python publish_studies.py --bucket my-curation-bucket study-a study-b. "
        "Use prepared, materialized study directories. Uploads require boto3 and AWS credentials "
        "with bucket list, object read and object write access. A changed archive replaces its S3 key."
    ))
    parser.add_argument("studies", type=Path, nargs="+")
    parser.add_argument("--bucket", required=True, help="Destination S3 bucket name")
    parser.add_argument("--profile", help="AWS profile (defaults to the standard AWS credential chain)")
    parser.add_argument("--source-revision", help="Record the source Git commit in object metadata")
    parser.add_argument("--dry-run", action="store_true", help="Build and check archives locally without contacting AWS")
    args = parser.parse_args()
    if "/" in args.bucket or not args.bucket.strip():
        parser.error("--bucket takes a bucket name")
    selected = {}
    for directory in args.studies:
        identifier = study_id(directory)
        if identifier in selected:
            parser.error(f"Study selected twice: {identifier}")
        selected[identifier] = directory
    client = None
    if not args.dry_run:
        import boto3
        client = boto3.Session(profile_name=args.profile).client("s3")
    for identifier, directory in selected.items():
        with tempfile.TemporaryDirectory(prefix="publish-study-") as tmp:
            archive = Path(tmp) / f"{identifier}.tar.gz"
            digest = pack(directory, identifier, archive)
            metadata = {"archive-sha256": digest}
            if args.source_revision:
                metadata["source-commit"] = args.source_revision
            status = "Prepared" if args.dry_run else upload(client, args.bucket, archive, metadata)
            print(f"{status} s3://{args.bucket}/{archive.name} ({archive.stat().st_size} bytes, SHA-256 {digest})", flush=True)


if __name__ == "__main__":
    main()
