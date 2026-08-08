#!/usr/bin/env python3
"""Compute SHA-256 checksums of a mission bag directory (Bible §17.4).

Usage: python3 bag_checksum.py <bag_dir> [checksums.txt]
"""

import hashlib
import os
import sys


def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(1)
    bag = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(bag,
                                                             'checksums.txt')
    if not os.path.isdir(bag):
        print(f'not a directory: {bag}')
        raise SystemExit(1)

    with open(out, 'w') as f:
        for root, _, files in os.walk(bag):
            for name in sorted(files):
                p = os.path.join(root, name)
                rel = os.path.relpath(p, bag)
                digest = sha256_file(p)
                f.write(f'{digest}  {rel}\n')
                print(f'{digest}  {rel}')
    print(f'written: {out}')


if __name__ == '__main__':
    main()
