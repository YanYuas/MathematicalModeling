# -*- coding: utf-8 -*-
"""Palette / label audit of the 12 delivered PNGs (exact-pixel colour census)."""
import glob, os, struct
from collections import Counter
from PIL import Image

OKABE = {"#0072B2":"blue","#E69F00":"orange","#009E73":"bluish green","#D55E00":"vermillion",
         "#56B4E9":"sky blue","#F0E442":"yellow","#CC79A7":"reddish purple","#999999":"grey"}
DEFAULT_MATPLOTLIB = {"#FF0000":"pure red","#00FF00":"pure green","#0000FF":"pure blue",
                      "#FFA500":"orange(x11)","#FFFF00":"yellow(x11)"}

def dpi_of(p):
    d = open(p,"rb").read(4000); i = 8
    while i+8 <= len(d):
        ln = struct.unpack(">I", d[i:i+4])[0]; t = d[i+4:i+8]
        if t == b"pHYs":
            px,py,u = struct.unpack(">IIB", d[i+8:i+17]); return round(px*0.0254,1) if u==1 else None
        i += 12+ln
    return None

for folder in ["图_v2.1_基础修订","图_v3.0_创新设计"]:
    base = "E:/CUMCM2026/交付准备区/Q2_待交付_最终版/"+folder
    print("="*90); print(folder)
    for p in sorted(glob.glob(base+"/*.png")):
        im = Image.open(p).convert("RGB")
        w,h = im.size
        small = im.resize((min(w,900), min(h,900)))
        cnt = Counter(small.getdata())
        tot = sum(cnt.values())
        hexes = {"#%02X%02X%02X"%c: n for c,n in cnt.items()}
        hit_ok = {k:v for k,v in hexes.items() if k in OKABE and v/tot > 0.0002}
        hit_def = {k:v for k,v in hexes.items() if k in DEFAULT_MATPLOTLIB and v/tot > 0.0002}
        # near-default detection (pure saturated primaries within +-6)
        near = 0
        for (r,g,b),n in cnt.items():
            if (r>249 and g<6 and b<6) or (g>249 and r<6 and b<6) or (b>249 and r<6 and g<6): near += n
        print("  %-30s %5dx%-5d dpi=%-6s %6.0fKB  okabe=%s  default=%s  pure_primary=%.2f%%"
              % (os.path.basename(p), w, h, str(dpi_of(p)), os.path.getsize(p)/1024,
                 sorted(hit_ok.keys()) or "-", sorted(hit_def.keys()) or "-", 100.0*near/tot))
