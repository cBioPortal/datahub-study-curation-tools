#!/usr/bin/env python3
"""Download the exact preprocessing tools in preprocessing-tools.lock.json."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path, help='New directory; existing directories are refused')
    args = parser.parse_args()
    lock = Path(__file__).with_name('preprocessing-tools.lock.json')
    entries = json.loads(lock.read_text())
    args.destination.mkdir(parents=True, exist_ok=False)
    for entry in entries:
        url = f"https://raw.githubusercontent.com/{entry['repo']}/{entry['commit']}/{entry['path']}"
        with urllib.request.urlopen(url, timeout=60) as response:
            content = response.read()
        if hashlib.sha256(content).hexdigest() != entry['sha256']:
            raise ValueError(f"Checksum mismatch: {entry['file']}")
        path = args.destination / entry['file']
        with path.open('xb') as output:
            output.write(content)
        print(path, flush=True)
    (args.destination / 'sources.lock.json').write_bytes(lock.read_bytes())


if __name__ == '__main__':
    main()
