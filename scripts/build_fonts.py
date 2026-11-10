#!/usr/bin/env python3
"""One-off: cut the three Archivo instances the cards use, subset them, and
record their advance widths.

Run locally when the type changes; the outputs in fonts/ are committed, so the
daily Action needs nothing but the standard library.

    pip install fonttools
    python scripts/build_fonts.py path/to/Archivo[wdth,wght].ttf
"""
import json
import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent
CHARS = "".join(chr(c) for c in range(32, 127))

# name -> (width axis, weight axis). One family at two widths: the expanded
# cut is only ever the name, the normal width carries everything else.
INSTANCES = {
    "display": (125, 800),
    "semi": (100, 600),
    "regular": (100, 400),
}


def main(src: str) -> None:
    metrics = {}
    for name, (wdth, wght) in INSTANCES.items():
        font = instancer.instantiateVariableFont(
            TTFont(src), {"wdth": wdth, "wght": wght})
        opts = subset.Options()
        opts.flavor = "woff"
        opts.layout_features = ["kern", "liga"]
        sub = subset.Subsetter(opts)
        sub.populate(text=CHARS)
        sub.subset(font)
        out = ROOT / "fonts" / f"archivo-{name}.woff"
        font.flavor = "woff"
        font.save(out)

        cmap = font.getBestCmap()
        hmtx = font["hmtx"]
        metrics[name] = {
            "upm": font["head"].unitsPerEm,
            "adv": {ch: hmtx[cmap[ord(ch)]][0] for ch in CHARS if ord(ch) in cmap},
        }
        print(f"{out.name}: {out.stat().st_size / 1024:.1f} KB")
    (ROOT / "fonts" / "metrics.json").write_text(json.dumps(metrics))


if __name__ == "__main__":
    main(sys.argv[1])
