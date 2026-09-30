import zipfile, re, os

os.chdir(r'c:\Users\29845\Desktop\电工杯')

with zipfile.ZipFile('B题：嵌入式社区养老服务站的建设与优化问题.docx', 'r') as z:
    c = z.read('word/document.xml').decode('utf-8')
    t = re.sub(r'<[^>]+>', ' ', c)
    t = re.sub(r'\s+', ' ', t).strip()
    # Find question 3
    idx3 = t.find('问题三')
    if idx3 < 0:
        idx3 = t.find('问题 三')
    if idx3 < 0:
        # Try to find section about question 3
        for kw in ['三、', '3.', '第三']:
            idx3 = t.find(kw)
            if idx3 > 1000:
                break

    if idx3 > 0:
        print("=== 问题三内容 (从文本中找到) ===")
        print(t[max(0,idx3-200):idx3+3000])
    else:
        print("=== 全文搜索关键词 ===")
        for kw in ['问题', '三', '建设', '运营', '阶段', '动态']:
            positions = [m.start() for m in re.finditer(kw, t)]
            print(f"'{kw}': {len(positions)} 处, 位置: {positions[:10]}...")

        # Output entire text
        print("\n=== 完整文本 ===")
        print(t[:8000])
