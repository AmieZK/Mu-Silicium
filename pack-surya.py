#!/usr/bin/env python3
"""Pack HakiOS UEFI for surya + an XNUP payload into a fastboot-bootable image.

kernel = gzip(BootShim + SILICIUM_UEFI.fd + payload) + surya.dtb
ramdisk = the small stock ramdisk (the loader does not need it)
"""
import argparse
import gzip
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FD_SIZE = 0x300000
PAYLOAD_BASE = 0xF0000000
PAYLOAD_MAX = 0x04000000 - 0x1000

ap = argparse.ArgumentParser()
ap.add_argument("-p", "--payload", required=True)
ap.add_argument("-o", "--output", default=os.path.join(HERE, "haki-surya.img"))
ap.add_argument("--mode", default="RELEASE")
args = ap.parse_args()

fd = os.path.join(HERE, "Build", "suryaPkg", f"{args.mode}_CLANGPDB", "FV", "SILICIUM_UEFI.fd")
shim = os.path.join(HERE, "BootShim", "BootShim.bin")
dtb = os.path.join(HERE, "Resources", "DTBs", "surya.dtb")
ramdisk = os.path.join(HERE, "Resources", "ramdisk")
mkbootimg = os.path.join(HERE, "Resources", "Scripts", "mkbootimg.py")
for path in (fd, shim, dtb, ramdisk, mkbootimg, args.payload):
    if not os.path.isfile(path):
        sys.exit(f"pack-surya: missing {path}")

blob = open(shim, "rb").read() + open(fd, "rb").read()
if len(open(fd, "rb").read()) != FD_SIZE:
    sys.exit(f"pack-surya: FD size is not {FD_SIZE:#x}")
payload = open(args.payload, "rb").read()
if payload[:4] != b"XNUP" or len(payload) > PAYLOAD_MAX:
    sys.exit("pack-surya: bad or oversized payload")
blob += payload
blob += b"\0" * (-len(blob) % 16)

kernel = args.output + ".kernel~"
open(kernel, "wb").write(gzip.compress(blob, 6) + open(dtb, "rb").read())
try:
    subprocess.check_call(
        [sys.executable, mkbootimg, "--kernel", kernel, "--ramdisk", ramdisk,
         "--header_version", "1", "-o", args.output]
    )
finally:
    os.unlink(kernel)
print(f"{args.output}: {os.path.getsize(args.output)} bytes")
