"""Generate colour logo options with the image model (Actions → Logo options).

    python tools/logo_ai.py OUT_DIR ["extra wishes"]

Uses the same Azure settings as the backgrounds (AZURE_OPENAI_ENDPOINT, AZURE_IMAGE_DEPLOYMENT,
AZURE_OPENAI_KEY). Each style is asked for with a transparent background, so the chosen logo
can sit on top of the slides; if the model doesn't offer that, it is asked for a plain white
background instead, which is removed afterwards.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request

BASE = (
    "Design a logo emblem for a Christian ministry called Rise & Shine Ministries: an open Holy Bible "
    "with fire rising out of its pages. The Bible must be instantly recognisable: open pages with fine "
    "lines of text, a dark leather cover with gold page edges, and a red ribbon bookmark. The fire rises "
    "from the centre of the open pages in warm orange, gold and red, with a bright yellow core, like a "
    "sunrise of flame. Centred, balanced composition that still reads clearly when shown very small, "
    "like an app icon. No words, letters or numbers. No people. "
)
STYLES = {
    "modern": "Style: a clean modern flat emblem with smooth gradients and crisp edges.",
    "glow": "Style: a polished emblem with soft 3D shading and a gentle warm glow around the flames.",
    "classic": "Style: a classic church emblem, rich and warm, like an engraved badge, with fine detail.",
    "minimal": "Style: minimal and bold, few shapes, strong colour contrast, made to work tiny.",
}


def request(prompt: str, transparent: bool) -> bytes:
    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].strip().rstrip("/")
    body = {"prompt": prompt, "model": os.environ["AZURE_IMAGE_DEPLOYMENT"].strip(), "size": "1024x1024",
            "quality": "high", "n": 1, "output_format": "png"}
    if transparent:
        body["background"] = "transparent"
    req = urllib.request.Request(
        f"{endpoint}/openai/v1/images/generations?api-version=preview", data=json.dumps(body).encode(),
        headers={"api-key": os.environ["AZURE_OPENAI_KEY"].strip(), "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=300) as response:
        data = json.load(response)
    if usage := data.get("usage"):
        print(f"  tokens: {json.dumps(usage)}")
    return base64.b64decode(data["data"][0]["b64_json"])


def main(out: Path, wishes: str) -> int:
    out.mkdir(parents=True, exist_ok=True)
    made = 0
    for name, style in STYLES.items():
        prompt = BASE + style + (f" Also: {wishes}" if wishes else "")
        for transparent in (True, False):
            text = prompt + (" Transparent background." if transparent else " Plain pure white background.")
            try:
                image = request(text, transparent)
            except urllib.error.HTTPError as err:
                detail = err.read().decode(errors="replace")[:300]
                print(f"{name}: HTTP {err.code} ({'transparent' if transparent else 'white'}): {detail}")
                continue
            path = out / f"logo-{name}{'' if transparent else '-white-bg'}.png"
            path.write_bytes(image)
            print(f"{name}: {path.name}")
            made += 1
            break
    return 0 if made else 1


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]), " ".join(sys.argv[2:])))
