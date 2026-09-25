# -*- coding: utf-8 -*-
"""
让 ImGui 字体图集覆盖 UI 中用到的全部字符（动态字形收集版）。

背景：
    YimMenuV2 原本只合并了西里尔文（arial.ttf）和日文（meiryo.ttc），
    没有中文字形，中文会渲染成空白方框。
    旧方案用 GetGlyphRangesChineseSimplifiedCommon()，但 imgui 内置
    该表只有 2500 个常用字，"辑""剪""贴"等字不在表内，渲染成 '?'。

本方案：
    扫描【汉化后】源码树的所有字符串字面量，收集实际用到的全部
    非 ASCII 字符，生成精确的字形 ranges 表注入 Menu.cpp。
    源码里所有将要显示的字符 100% 进入图集，图集还比 2500 字表更小。

    兜底区间（源码中未出现但运行时可能用到）：
      Latin-1 补充、通用标点、CJK 标点、全角 ASCII。

补丁是"追加式"的：只插入一段额外的合并步骤，不改动原有行为；
字体缺失时跳过而不是报错。可重复执行（幂等，自动清理旧版补丁块）。

用法:
    python localization/patch_font.py <汉化后的src根目录>
    （目录下应有 game/frontend/Menu.cpp）
"""
import os, re, sys

SRC_EXTS = ('.cpp', '.hpp', '.h', '.cc')


def iter_string_literals(text):
    """扫描 C/C++ 字符串字面量，产出 (start, end, inner)。

    与 apply.py 同一套逻辑：不能用 '"..."' 正则在含 `("hash"_J, "Label")`
    的代码上错配引号对 —— 那会让部分中文串的字形漏收集，运行时显示成方块。
    """
    i, n = 0, len(text)
    while i < n:
        if text[i] != '"':
            i += 1
            continue
        j = i + 1
        while j < n:
            c = text[j]
            if c == '\\':
                j += 2
                continue
            if c == '"' or c == '\n':
                break
            j += 1
        if j < n and text[j] == '"':
            yield i, j + 1, text[i + 1:j]
            i = j + 1
        else:
            i += 1

# 兜底区间：源码里没出现、但运行时可能用到的符号
BASE_RANGES = [
    (0x00A0, 0x00FF),   # Latin-1 Supplement（é ° ² × ÷ 等）
    (0x2010, 0x2027),   # 通用标点（— – ' ' " " … ′ ″）
    (0x3000, 0x301F),   # CJK 标点（，。、〈〉《》）
    (0xFF01, 0xFF5E),   # 全角 ASCII（！＂＃ … ＡＺ ａｚ ０９）
]

BEGIN_MARK = '// --- BEGIN zh-CN glyph ranges (auto-generated) ---'
END_MARK = '// --- END zh-CN glyph ranges ---'
# 旧版补丁的标记（本次执行时先剥离）
OLD_BEGIN = '// --- BEGIN zh-CN localization: merge Simplified Chinese glyph ranges ---'
OLD_END = '// --- END zh-CN localization ---'

# 锚点正则：定位菜单里合并日文字形的那次 AddFontFromFileTTF 调用。
# 用正则而非精确串，源码/汉化脚本的细微变动不会导致补丁静默跳过。
ANCHOR_RX = re.compile(r'io\.Fonts->AddFontFromFileTTF\(\([^\n]*meiryo[^\n]*GetGlyphRangesJapanese\(\)\);')


def collect_literal_points(inner, points):
    """解码一个字符串字面量的内容，把其中的码点收进 points。

    处理：直接 UTF-8 字符（apply.py 写入的中文）、\\xXX 字节转义
    （连续序列按 UTF-8 解码，如 FontAwesome 图标）、\\uXXXX。
    PUA 区（U+E000-U+F8FF）跳过 —— 图标字形由嵌入的 IconFont 提供，
    系统中文字体里没有，收进中文字体的 ranges 只会浪费图集。
    """
    buf = bytearray()

    def flush():
        if buf:
            try:
                for ch in buf.decode('utf-8'):
                    points.add(ord(ch))
            except UnicodeDecodeError:
                pass
            buf.clear()

    i, n = 0, len(inner)
    while i < n:
        c = inner[i]
        if c == '\\' and i + 1 < n:
            d = inner[i + 1]
            if d == 'x' and i + 3 < n:
                try:
                    buf.append(int(inner[i + 2:i + 4], 16))
                    i += 4
                    continue
                except ValueError:
                    pass
            if d == 'u' and i + 5 < n:
                flush()
                try:
                    cp = int(inner[i + 2:i + 6], 16)
                    if not (0xE000 <= cp <= 0xF8FF):
                        points.add(cp)
                except ValueError:
                    pass
                i += 6
                continue
            flush()
            i += 2
            continue
        flush()
        cp = ord(c)
        if cp >= 0xA0 and not (0xE000 <= cp <= 0xF8FF):
            points.add(cp)
        i += 1
    flush()


def collect_points_from_tree(src_root):
    points = set()
    files = 0
    for dp, dn, fn in os.walk(src_root):
        if 'fonts' in dp.split(os.sep):
            continue  # 生成的字体字节数组整体跳过
        for f in fn:
            if not f.endswith(SRC_EXTS):
                continue
            p = os.path.join(dp, f)
            try:
                text = open(p, 'rb').read().decode('utf-8')
            except (UnicodeDecodeError, OSError):
                continue
            files += 1
            for _s, _e, inner in iter_string_literals(text):
                collect_literal_points(inner, points)
    return points, files


def build_ranges(points):
    spans = list(BASE_RANGES)
    for p in points:
        spans.append((p, p))
    spans.sort()
    merged = []
    for a, b in spans:
        if merged and a <= merged[-1][1] + 1:
            if b > merged[-1][1]:
                merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    return merged


def ranges_snippet(merged):
    lines = []
    lines.append(BEGIN_MARK)
    lines.append('\t\t// Dynamic glyph ranges: collected from every localized string literal')
    lines.append('\t\t// in the source tree (+ punctuation fallbacks), so all UI text is')
    lines.append('\t\t// guaranteed to be in the atlas. imgui\'s built-in table only has 2500')
    lines.append('\t\t// common characters and misses e.g. "辑剪贴".')
    lines.append('\t\tstatic const ImWchar kZhGlyphRanges[] = {')
    row = '\t\t    '
    for a, b in merged:
        item = '0x%04X, 0x%04X, ' % (a, b)
        if len(row) + len(item) > 100:
            lines.append(row.rstrip())
            row = '\t\t    '
        row += item
    row += '0,'
    lines.append(row)
    lines.append('\t\t};')
    lines.append('\t\t{')
    lines.append('\t\t\tstatic constexpr const char* kChineseFonts[] = {')
    lines.append('\t\t\t    "msyh.ttc",     // Microsoft YaHei (Windows 10/11)')
    lines.append('\t\t\t    "msyhbd.ttc",   // Microsoft YaHei Bold')
    lines.append('\t\t\t    "simhei.ttf",   // SimHei')
    lines.append('\t\t\t    "simsun.ttc",   // SimSun / NSimSun')
    lines.append('\t\t\t    "arialuni.ttf", // Arial Unicode MS (fallback)')
    lines.append('\t\t\t};')
    lines.append('\t\t\tfor (const char* name : kChineseFonts)')
    lines.append('\t\t\t{')
    lines.append('\t\t\t\tauto path = std::filesystem::path(std::getenv("SYSTEMROOT")) / "Fonts" / name;')
    lines.append('\t\t\t\tstd::error_code ec;')
    lines.append('\t\t\t\tif (!std::filesystem::exists(path, ec))')
    lines.append('\t\t\t\t\tcontinue;')
    lines.append('\t\t\t\tio.Fonts->AddFontFromFileTTF(path.string().c_str(), size, &FontCfg, kZhGlyphRanges);')
    lines.append('\t\t\t\tbreak; // 取第一个存在的字体')
    lines.append('\t\t\t}')
    lines.append('\t\t}')
    lines.append(END_MARK)
    return '\n'.join(lines)


def strip_old_patches(text):
    """删除旧版/新版的补丁块，返回干净文本。"""
    for b, e in ((OLD_BEGIN, OLD_END), (BEGIN_MARK, END_MARK)):
        while True:
            i = text.find(b)
            if i < 0:
                break
            j = text.find(e, i)
            if j < 0:
                text = text[:i]
                break
            text = text[:i] + text[j + len(e):]
    return text


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    src_root = sys.argv[1].rstrip('/\\')
    menu_cpp = os.path.join(src_root, 'game', 'frontend', 'Menu.cpp')
    if not os.path.exists(menu_cpp):
        sys.exit('FATAL: %s not found' % menu_cpp)

    points, nfiles = collect_points_from_tree(src_root)
    cjk = sum(1 for p in points if 0x4E00 <= p <= 0x9FFF)
    print('  scanned files  : %d' % nfiles)
    print('  unique glyphs  : %d (CJK %d)' % (len(points), cjk))

    merged = build_ranges(points)
    snippet = ranges_snippet(merged)

    text = open(menu_cpp, encoding='utf-8').read()
    if BEGIN_MARK in text and 'kZhGlyphRanges' in text:
        print('  font patch     : already applied, skipped')
        return 0

    text = strip_old_patches(text)
    m = ANCHOR_RX.search(text)
    if not m:
        print('WARNING: anchor line not found, font patch skipped.', file=sys.stderr)
        return 2

    text = text[:m.start()] + snippet + '\n\t\t' + text[m.start():]
    open(menu_cpp, 'w', encoding='utf-8', newline='').write(text)
    print('  font patch     : applied (%d range pairs)' % len(merged))
    return 0


if __name__ == '__main__':
    sys.exit(main())
