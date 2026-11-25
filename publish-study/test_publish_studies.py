import io
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import boto3
from moto import mock_aws
from publish_studies import main


class PublisherTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.study = self.root / "local-directory"
        self.study.mkdir()
        (self.study / "meta_study.txt").write_text("cancer_study_identifier: example\n")

    def publish(self, *args):
        with patch.object(sys, "argv", ["publish_studies.py", "--bucket", "test-studies", str(self.study), *args]):
            main()

    @mock_aws
    def test_retries_and_updates_use_one_key(self):
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="test-studies")
        client.put_bucket_versioning(Bucket="test-studies", VersioningConfiguration={"Status": "Enabled"})
        self.publish()
        self.publish()
        versions = client.list_object_versions(Bucket="test-studies")["Versions"]
        self.assertEqual(len(versions), 1)
        (self.study / "data.txt").write_text("updated")
        self.publish("--source-revision", "abc123")
        obj = client.get_object(Bucket="test-studies", Key="example.tar.gz")
        self.assertEqual(obj["Metadata"]["source-commit"], "abc123")
        with tarfile.open(fileobj=io.BytesIO(obj["Body"].read())) as archive:
            self.assertEqual(archive.extractfile("example/data.txt").read(), b"updated")

    def test_pointer_and_symlink_refused_even_in_dry_run(self):
        data = self.study / "data.txt"
        data.write_bytes(b"version https://git-lfs.github.com/spec/v1\n")
        with self.assertRaisesRegex(ValueError, "Git LFS"):
            self.publish("--dry-run")
        data.unlink()
        data.symlink_to(self.study / "meta_study.txt")
        with self.assertRaisesRegex(ValueError, "Unsupported file"):
            self.publish("--dry-run")

    def test_duplicate_ids_fail_before_any_upload(self):
        with patch("boto3.Session") as session, self.assertRaises(SystemExit):
            self.publish(str(self.study))
        session.assert_not_called()
