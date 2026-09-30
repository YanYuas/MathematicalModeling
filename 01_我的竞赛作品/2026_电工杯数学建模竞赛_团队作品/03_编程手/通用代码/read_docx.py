import sys
print("Python started", flush=True)

import zipfile, re, os, shutil, traceback

try:
    os.chdir(r'c:\Users\29845\Desktop\电工杯')
    print("chdir ok", flush=True)

    src = 'B题：嵌入式社区养老服务站的建设与优化问题.docx'
    dst = '_tmp_b.docx'
    print(f"copying {src} -> {dst}", flush=True)
    shutil.copy2(src, dst)
    print("copy ok", flush=True)

    print("opening zip...", flush=True)
    with zipfile.ZipFile(dst, 'r') as z:
        print("zip open ok", flush=True)
        c = z.read('word/document.xml').decode('utf-8')
        print(f"read {len(c)} bytes", flush=True)
        t = re.sub(r'<[^>]+>', ' ', c)
        t = re.sub(r'\s+', ' ', t).strip()
        print(t[:15000])

    os.remove(dst)
    print("done", flush=True)
except Exception:
    traceback.print_exc()
    sys.exit(1)
