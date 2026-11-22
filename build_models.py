#!/usr/bin/env python3
"""specs/*.md（モデル定義）と models/*.vox から models-extra.js を生成する。

モデル定義の仕様は MODEL-SPEC.md を参照。
実行: uv run --with pyyaml python3 build_models.py
出力: models-extra.js（window.EXTRA_MODELS を定義する。Voxel Valkyrie 等の
エンジン側はこのファイルを読み込むだけでモデルとアニメーションが使える）
"""
import base64
import json
import struct
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).parent


def parse_vox(path):
    raw = path.read_bytes()
    assert raw[:4] == b"VOX ", path
    pos = 8
    dims, voxels, palette = None, None, {}
    assert raw[pos:pos + 4] == b"MAIN"
    content_n, children_n = struct.unpack_from("<II", raw, pos + 4)
    pos += 12 + content_n
    end = pos + children_n
    while pos < end:
        cid = raw[pos:pos + 4]
        c_n, ch_n = struct.unpack_from("<II", raw, pos + 4)
        body = pos + 12
        if cid == b"SIZE":
            dims = struct.unpack_from("<III", raw, body)
        elif cid == b"XYZI":
            (n,) = struct.unpack_from("<I", raw, body)
            voxels = []
            for i in range(n):
                x, y, z, c = struct.unpack_from("<BBBB", raw, body + 4 + i * 4)
                voxels.append((x, y, z, c))
        elif cid == b"RGBA":
            for i in range(256):
                r, g, b, a = struct.unpack_from("<BBBB", raw, body + i * 4)
                if a or r or g or b:
                    palette[i + 1] = (r << 16) | (g << 8) | b
        pos = body + c_n + ch_n
    assert dims and voxels is not None, path
    return dims, voxels, palette


def surface_count(dims, voxels):
    filled = {(x, y, z) for x, y, z, _ in voxels}
    n = 0
    for (x, y, z) in filled:
        if all((x + dx, y + dy, z + dz) in filled
               for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))):
            continue
        n += 1
    return n


def read_spec(path):
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---"), path
    fm = text.split("---", 2)[1]
    return yaml.safe_load(fm)


def main():
    specs = []
    for p in sorted((HERE / "specs").glob("*.md")):
        specs.append(read_spec(p))
    specs.sort(key=lambda s: s.get("order", 9999))
    models = []
    max_surface = 0
    for sp in specs:
        key = sp["key"]
        form_specs = sp["forms"]
        if not all((HERE / "models" / f["file"]).exists() for f in form_specs):
            print(f"SKIP {key}: .vox files missing")
            continue
        forms = []
        palette_all = {}
        form_names, robot_forms, form_anim = [], [], []
        for i, f in enumerate(form_specs):
            dims, voxels, palette = parse_vox(HERE / "models" / f["file"])
            palette_all.update(palette)
            quads = bytearray()
            for x, y, z, c in voxels:
                quads += struct.pack("<BBBB", x, y, z, c)
            sc = surface_count(dims, voxels)
            max_surface = max(max_surface, sc)
            forms.append({
                "dims": list(dims),
                "data": base64.b64encode(bytes(quads)).decode(),
                "voxels": len(voxels),
                "surface": sc,
            })
            form_names.append(f["label"])
            if f.get("robot"):
                robot_forms.append(i)
            form_anim.append(f.get("anim"))
        entry = {
            "key": key,
            "name": sp["name"],
            "formNames": form_names,
            "robotForms": robot_forms,
            "palette": {str(k): v for k, v in sorted(palette_all.items())},
            "forms": forms,
        }
        if any(form_anim):
            entry["formAnim"] = form_anim
        if "pivot" in sp:
            entry["pivot"] = sp["pivot"]
        models.append(entry)
        print(f"{key}: forms={len(forms)}")
    js = "// 追加モデルデータ（specs/*.md と models/*.vox から自動変換。build_models.py で再生成）\n"
    js += "window.EXTRA_MODELS = " + json.dumps(models, ensure_ascii=False) + ";\n"
    out = HERE / "models-extra.js"
    out.write_text(js, encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size} bytes), models={len(models)}, max surface = {max_surface}")


if __name__ == "__main__":
    sys.exit(main())
