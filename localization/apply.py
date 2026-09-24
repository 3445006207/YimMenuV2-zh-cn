# -*- coding: utf-8 -*-
"""
把中文译文写回 YimMenuV2 源码树。

用法:
    python localization/apply.py <源码src目录> <输出src目录>

词典构成:
    官方译文 + 本仓库定制译文。
    官方译文来自 YimMenu/Translations（commit 已固定，保证可复现），
    构建时联网下载 en_US.json 与 zh_CN.json，组合出「英文原文 -> 中文」映射
    （en_US 的值即英文原文，zh_CN 的值即中文译文，二者按翻译键对齐），
    首次下载后缓存为 _official_cache.json。
    定制译文 = translations_part_*.json，按文件名排序依次覆盖官方译文。

安全约束（脚本强制保证）:
  1. Command 构造函数的第一个字符串是内部名，会被编译成 joaat 哈希，
     同时作为配置文件里的键 —— 永远不翻译。
  2. 只替换字符串字面量的内容，引号本身与周边代码一字不动。
  3. 只有当字面量原文在译表中精确命中时才替换，
     因此代码标识符、文件路径、格式串不会被误伤。
  4. 游戏资产标签键（CMOD_HRN_TRK、HORN_CLAS1 等）保持原样 ——
     它们会被交给 HUD::GET_FILENAME_FOR_AUDIO_CONVERSATION() 由游戏自身本地化。
  5. ImGui 标签中 '##' 之后的隐藏 ID 原样保留（Join##username -> 加入##username）。
  6. fonts/ 目录（生成的字体字节数组）整体跳过。
"""
import os, re, json, glob, shutil, collections, sys, urllib.request

SRC_EXTS = ('.cpp', '.hpp', '.h', '.cc')
HERE = os.path.dirname(os.path.abspath(__file__))

# 官方译文源：按 commit 固定保证可复现。主源 jsDelivr，备用 raw.githubusercontent。
TRANS_SHA = 'c053bb86a729d175a5f73ac5de083388abaac780'
OFFICIAL_BASES = [
    'https://cdn.jsdelivr.net/gh/YimMenu/Translations@' + TRANS_SHA + '/',
    'https://raw.githubusercontent.com/YimMenu/Translations/' + TRANS_SHA + '/',
]

# ---------------------------------------------------------------- 规则 -------
# 一个完整的 C 字符串字面量（连同引号）。
LIT = r'("(?:[^"\\\n]|\\.)*")'

WIDGETS = [
    'ImGui::Button', 'ImGui::SmallButton', 'ImGui::Selectable',
    'ImGui::Checkbox', 'ImGui::RadioButton', 'ImGui::BeginTabItem',
    'ImGui::TreeNode', 'ImGui::TreeNodeEx', 'ImGui::CollapsingHeader',
    'ImGui::MenuItem', 'ImGui::BeginMenu',
]

PATTERNS = [
    # Command 注册：{内部名(不动), 标签, 说明}
    ('command',
     r'(static\s+\w+\s+_\w+\s*\{\s*)' + LIT + r'(\s*,\s*)' + LIT + r'(\s*,\s*)' + LIT,
     'skip_first'),
    # 顶层子菜单 / 标签页标题
    ('submenu', r'(Submenu::Submenu\s*\(\s*)' + LIT, 'all'),
    # 分类 / 分组显示名
    ('group', r'(std::make_shared<\s*(?:Category|Group)\s*>\s*\(\s*)' + LIT, 'all'),
    # 输入提示（标签与提示都可见）
    ('hint', r'(InputTextWithHint\s*\(\s*)' + LIT + r'(\s*,\s*)' + LIT, 'all'),
    # 下拉/列表选项表：{<int|enum>, "标签"}
    ('optionlist', r'(\{\s*[^,\{\}\[\]]{1,140},\s*)' + LIT + r'(\s*\})', 'second'),
    # 普通 ImGui::Text
    ('text', r'(ImGui::Text(?:Unformatted)?\s*\(\s*)' + LIT, 'all'),
]
for _w in WIDGETS:
    PATTERNS.append(('widget', r'(' + _w.replace('.', r'\.') + r'\s*\(\s*)' + LIT, 'all'))

COMPILED = [(name, re.compile(rx), mode) for name, rx, mode in PATTERNS]

# 游戏资产标签键：交给游戏引擎本地化，翻译后反而取不到文本。
GAME_ASSET_KEY = re.compile(r'^[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+$')
# ImGui 标签里 '##' 之后是隐藏 ID。
HIDDEN_ID = re.compile(r'^(.*?)(##.+)$', re.S)


def lookup(inner, tmap):
    """返回该字面量内容的中文替换；返回 None 表示保持原样。"""
    if not inner:
        return None
    if inner.startswith('##') or GAME_ASSET_KEY.match(inner):
        return None
    hidden = HIDDEN_ID.match(inner)
    visible = hidden.group(1) if hidden else inner
    tail = hidden.group(2) if hidden else ''
    if hidden and not visible.strip():
        return None
    zh = tmap.get(visible)
    if not zh or zh == visible:
        zh = tmap.get(inner)
        if not zh or zh == inner:
            return None
        return zh
    return zh + tail


def esc(s):
    return (s.replace('\\', '\\\\').replace('"', '\\"')
             .replace('\t', '\\t').replace('\r', '\\r'))


def swap(literal, tmap, stats, ctx):
    """替换带引号字面量的内容，引号本身保留不动。"""
    inner = literal[1:-1]
    new = lookup(inner, tmap)
    if new and new != inner:
        stats[ctx] += 1
        return '"' + esc(new) + '"'
    return literal


def patch_text(text, tmap, stats):
    for name, rx, mode in COMPILED:
        if mode == 'skip_first':
            def sub(m):
                stats['_commands'] += 1
                return (m.group(1) + m.group(2)          # 内部名，原样输出
                        + m.group(3) + swap(m.group(4), tmap, stats, 'label')
                        + m.group(5) + swap(m.group(6), tmap, stats, 'description'))
        elif mode == 'second':
            def sub(m):
                return m.group(1) + swap(m.group(2), tmap, stats, name) + m.group(3)
        else:
            def sub(m):
                out = m.group(1) + swap(m.group(2), tmap, stats, name)
                if m.re.groups > 2 and m.group(3) is not None and m.group(4) is not None:
                    out += m.group(3) + swap(m.group(4), tmap, stats, name)
                return out
        text = rx.sub(sub, text)
    return text


def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'yimmenu-zh-build'})
    return json.loads(urllib.request.urlopen(req, timeout=60).read().decode('utf-8'))


def load_tmap():
    """官方译文(en_US+zh_CN 组合) + 本地定制译文(translations_part_*.json)。"""
    cache = os.path.join(HERE, '_official_cache.json')
    if os.path.exists(cache):
        official = json.load(open(cache, encoding='utf-8'))
    else:
        en = zh = None
        last = None
        for base in OFFICIAL_BASES:
            try:
                en = fetch_json(base + 'en_US.json')
                zh = fetch_json(base + 'zh_CN.json')
                break
            except Exception as e:
                en = zh = None
                last = e
        if not en or not zh:
            sys.exit('FATAL: 无法下载官方译文(%s) —— '
                     '可手动把 en_US.json 与 zh_CN.json 组合后存为 %s' % (last, cache))
        official = {}
        for k, zhv in zh.items():
            ev = en.get(k)
            if isinstance(ev, str) and ev:
                official[ev] = zhv
        json.dump(official, open(cache, 'w', encoding='utf-8'), ensure_ascii=False)
    tmap = dict(official)
    for f in sorted(glob.glob(os.path.join(HERE, 'translations_part_*.json'))):
        tmap.update(json.load(open(f, encoding='utf-8')))
    return tmap


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src_root, out_root = sys.argv[1], sys.argv[2]

    tmap = load_tmap()
    # 长键优先，避免短键先命中造成半截替换
    tmap = dict(sorted(tmap.items(), key=lambda kv: -len(kv[0])))
    stats = collections.Counter()

    if os.path.exists(out_root):
        shutil.rmtree(out_root)
    shutil.copytree(src_root, out_root)

    scanned = patched = 0
    for dp, dn, fn in os.walk(out_root):
        if 'fonts' in dp.split(os.sep):
            continue
        for f in fn:
            if not f.endswith(SRC_EXTS):
                continue
            p = os.path.join(dp, f)
            scanned += 1
            raw = open(p, 'rb').read()
            try:
                text = raw.decode('utf-8')
            except UnicodeDecodeError:
                continue
            new = patch_text(text, tmap, stats)
            if new != text:
                open(p, 'w', encoding='utf-8', newline='').write(new)
                patched += 1

    print('  scanned files : %d' % scanned)
    print('  patched files : %d' % patched)
    print('  command ctors : %d' % stats['_commands'])
    for k, v in sorted((k, v) for k, v in stats.items() if not k.startswith('_')):
        if v:
            print('    %-12s -> %5d' % (k, v))


if __name__ == '__main__':
    main()
