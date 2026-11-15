#!/usr/bin/env python3
"""Write the cloud-request log line of the plain baseline arm for one case.

  make_baseline_log.py KIT CASE OUT.jsonl

The baseline sends the allergy lists (inside the prompt) and the menu image to the cloud, so its privacy check fails by design.
The image is recorded as its first 400 base64 characters, byte size and SHA-256 (the real request carried the whole image).
"""
import base64
import json
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'testkit'))
import common as C  # noqa: E402


def main(argv):
    if len(argv) != 4:
        print(__doc__)
        return 2
    kit = C.load_kit(argv[1])
    cid = argv[2]
    prompt = C.read(os.path.join(kit.d('prompts'), cid + '.txt'))
    img = kit.p(os.path.join('menus', cid + '.png'))
    raw = open(img, 'rb').read()
    b64 = base64.b64encode(raw).decode('ascii')
    line = {'to': 'cloud', 'body': {'prompt': prompt, 'image_base64_first_400_chars': b64[:400], 'image_bytes': len(raw), 'image_sha256': C.sha_file(img)}}
    C.write(argv[3], json.dumps(line, ensure_ascii=False) + '\n')
    print('wrote', argv[3])
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
