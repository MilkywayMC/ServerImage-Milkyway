#!/usr/bin/env python3
"""docker-compose.yaml のイメージの決まりを確かめる (CI と手元。標準ライブラリだけ)。

  1. build: を使わない (本番でイメージを作らない。GitHub Actions が作ったものを使う)
  2. すべてのイメージにタグがあり、latest ではない
  3. 自前も含めて @sha256: で中身まで固定する (タグは動かせる。毎朝の pull で、確かめていないものが本番に入らないように)

  4. security/images.txt の「本番 /home/toroserver」の節が、compose のイメージ (digest を除いたもの) と過不足なく一致する
     (脆弱性検査の一覧が compose とずれると、動いているイメージが検査されない)

digest は ServerImage-TORO では scripts/pin-images.sh で付ける。

正本はこのファイル (ServerImage-TORO)。ServerImage-Milkyway の .github/scripts/check-images.py は同一内容の写し (直すときはここだけ直して写す)。
4 は security/images.txt があるリポジトリだけで行う。

使い方: python3 scripts/check-images.py [compose ファイル...]  (既定は docker-compose.yaml)
"""
import os
import re
import sys

DIGEST = re.compile(r"@sha256:[0-9a-f]{64}$")


def problems(path):
    for no, raw in enumerate(open(path, encoding="utf-8"), 1):
        line = raw.split(" #", 1)[0].rstrip()
        if re.match(r"^\s+build:", line):
            yield no, "build: は使わない (イメージは GitHub Actions で作る)"
            continue
        m = re.match(r"^\s+image:\s*(\S+)$", line)
        if not m:
            continue
        ref = m.group(1)
        name = DIGEST.sub("", ref)
        tag = name.rsplit(":", 1)[1] if ":" in name.rsplit("/", 1)[-1] else ""
        if not tag:
            yield no, f"{ref}: タグが無い"
        elif tag == "latest" or tag.endswith("-latest"):
            yield no, f"{ref}: latest は使わない"
        elif not DIGEST.search(ref):
            yield no, f"{ref}: @sha256: で固定する (digest を付ける)"


IMAGES_TXT = "security/images.txt"


def compose_images(path):
    found = set()
    for raw in open(path, encoding="utf-8"):
        m = re.match(r"^\s+image:\s*(\S+)", raw.split(" #", 1)[0].rstrip())
        if m:
            found.add(DIGEST.sub("", m.group(1)))
    return found


def listed_images(path):
    """images.txt の「本番 /home/toroserver」の節 (見出しの comment から、次の comment まで)"""
    found, inside = set(), False
    for raw in open(path, encoding="utf-8"):
        line = raw.strip()
        if line.startswith("#"):
            if inside and found:
                break
            inside = "/home/toroserver" in line
        elif inside and line:
            found.add(line)
    return found


def list_problems(compose):
    want, have = compose_images(compose), listed_images(IMAGES_TXT)
    for ref in sorted(want - have):
        yield f"{IMAGES_TXT}: {ref} が一覧に無い (compose にある)"
    for ref in sorted(have - want):
        yield f"{IMAGES_TXT}: {ref} は compose に無い (古い。消すか別の節へ)"


def main():
    paths = sys.argv[1:] or ["docker-compose.yaml"]
    bad = 0
    if paths == ["docker-compose.yaml"] and os.path.exists(IMAGES_TXT):
        for msg in list_problems(paths[0]):
            print(msg)
            bad += 1
    for path in paths:
        for no, msg in problems(path):
            print(f"{path}:{no}: {msg}")
            bad += 1
    if bad:
        sys.exit(1)
    print("OK: イメージの決まりを守っています")


main()
