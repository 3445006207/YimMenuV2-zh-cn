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
    # 桌面通知：Notifications::Show("标题", "内容", 类型) —— 两条都是 UI 文本
    ('notify', r'(Notifications::Show\s*\(\s*)' + LIT + r'(\s*,\s*)' + LIT, 'all'),
    # 下拉/列表选项表：{<int|enum>, "标签"}
    ('optionlist', r'(\{\s*[^,\{\}\[\]]{1,140},\s*)' + LIT + r'(\s*\})', 'second'),
    # 普通 ImGui::Text
    ('text', r'(ImGui::Text(?:Unformatted)?\s*\(\s*)' + LIT, 'all'),
]
for _w in WIDGETS:
    PATTERNS.append(('widget', r'(' + _w.replace('.', r'\.') + r'\s*\(\s*)' + LIT, 'all'))

COMPILED = [(name, re.compile(rx), mode) for name, rx, mode in PATTERNS]

# ------------------------------------------------- 兜底直译（UI 目录白名单）---
# 背景：YimMenuV2 的界面由一套多态 Item 类 + 大量数据表构建
#   （make_shared<CommandItem>("id"_J, "标签")、CollapsingHeaderItem("标题")、
#    {"Sedan", "Coupe", ...} 之类的字符串数组…），
# 调用点写法五花八门，逐个枚举 pattern 既易漏又难维护。
# 因此对 UI 目录采用「词典精确命中即替换」策略：
#   安全性由三点保证 ——
#     1. 只有显式收录进词典的字符串才会被替换（词典即白名单）；
#     2. 形状过滤排除内部名/资产键/字节特征码/格式串/路径/隐藏 ID；
#     3. core/scripting 等非 UI 目录整体不参与（避免误伤 Lua API 名）。
# 该步骤在 PATTERNS 之后执行：已被 pattern 翻译过的字面量此时是中文，
# 不会二次命中；且幂等。
UI_DIRS = ('game/frontend/', 'game/features/', 'game/backend/', 'game/gta/data/')

LOWER_IDENT = re.compile(r'[a-z][a-z0-9_]*$')
BYTE_PAT = re.compile(r'[0-9A-F?]{1,2}(?: [0-9A-F?]{1,2})*$')
FILENAME = re.compile(r'\.[A-Za-z0-9]{1,6}$')          # arial.ttf / meiryo.ttc …
# 路径构造上下文：这些位置的字面量是文件/目录名，绝不能翻译
# （血的教训：早期词表把 "Fonts" 译成"字体"，会让 %SYSTEMROOT%/Fonts 失效，
#   字体加载失败 → 所有中文变方块）
PATH_CTX = re.compile(r'std::filesystem::path|getenv\s*\(|/ "|" /')


def is_ui_literal(inner):
    """形状过滤：只把"像 UI 文本"的字面量交给词典判断。"""
    if not inner.strip() or len(inner) > 110:
        return False
    if GAME_ASSET_KEY.match(inner):
        return False
    if LOWER_IDENT.match(inner):        # 全小写内部名/标识符/音效名
        return False
    if BYTE_PAT.match(inner):           # "2D 01 09 00 00" 字节特征码
        return False
    if FILENAME.search(inner):          # 文件名（arial.ttf、config.json…）
        return False
    if re.search(r'[%\\/]|\{[^}]*\}', inner):   # 格式串、路径
        return False
    if not re.search(r'[A-Za-z]', inner):
        return False
    return True


def iter_string_literals(text):
    """扫描 C/C++ 字符串字面量，产出 (start, end, inner)（end 为闭引号后一位）。

    ⚠ 不能用 '"..."' 这类正则：在 `("hash"_J, "Label")` 这种相邻字面量上，
    正则会把第一个串的**闭引号**当成下一个串的开引号，错配引号对，
    导致真正的标签字面量被整段跳过（这正是 "Amount"/"Session Type"/"Kill All"
    等标签长期翻不出来的原因）。这里用状态机逐字符扫描，转义与相邻串都正确。
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
            i += 1          # 未闭合（例如跨行截断），跳过这个引号


def translate_ui_literals(text, tmap, stats, overrides=None):
    parts, last = [], 0
    for start, end, inner in iter_string_literals(text):
        if start < last:
            continue
        lit = text[start:end]
        if text[end:end + 2] == '_J':          # joaat 内部名，不能翻译
            continue
        if overrides and inner in overrides:   # 同字不同义的文件级精确覆盖
            zh = overrides[inner]
        else:
            window = text[max(0, start - 90):end + 90]
            if PATH_CTX.search(window):        # 路径构造表达式里的字符串
                continue
            if not is_ui_literal(inner):
                continue
            zh = tmap.get(inner)
            if zh:
                hidden = HIDDEN_ID.match(inner)
                if hidden:
                    zh = zh + hidden.group(2)  # 保留 ImGui 隐藏 ID
            else:
                continue
        if not zh or zh == inner:
            continue
        parts.append(text[last:start])
        parts.append('"' + esc(zh) + '"')
        last = end
        stats['ui'] += 1
    parts.append(text[last:])
    return ''.join(parts)


# 同字不同义的精确覆盖（按文件路径后缀匹配，优先级最高）。
# 例：Weather.cpp 的 "Clear" 是天气（晴朗），调试页按钮的 "Clear" 是"清除"，
# 全局词表只能二选一，这里按文件单独修正。
FILE_OVERRIDES = {
    'features/world/Weather.cpp': {'Clear': '晴朗'},
}

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
        data = json.load(open(f, encoding='utf-8'))
        # 只接受 str -> str：词典文件里若混入注释对象/嵌套结构，直接忽略，避免脏数据进词表
        tmap.update({k: v for k, v in data.items() if isinstance(k, str) and isinstance(v, str)})
    return tmap


def patch_cmake_utf8(src_root):
    """给上游 CMakeLists.txt 追加 MSVC /utf-8。

    根因：源码含 UTF-8 中文字面量且无 BOM，MSVC 默认按系统代码页
    (windows-latest 上为 CP1252) 解释，转换失败的字符在编译期就被
    替换成 '?'，DLL 里的字符串直接损坏。/utf-8 强制源码与执行字符集
    均为 UTF-8。clang-cl 默认按 UTF-8 处理，且其 CXX_COMPILER_ID 是
    "Clang"，下面的 generator expression 不会影响 clang 构建。
    """
    root = os.path.dirname(os.path.abspath(src_root.rstrip('/\\')))
    cm = os.path.join(root, 'CMakeLists.txt')
    if not os.path.exists(cm):
        print('  cmake utf-8   : CMakeLists.txt not found next to src, skipped')
        return
    text = open(cm, encoding='utf-8').read()
    if 'zh-CN localization: MSVC utf-8' in text:
        print('  cmake utf-8   : already applied, skipped')
        return
    text += ('\n# --- BEGIN zh-CN localization: MSVC utf-8 ---\n'
             '# Sources contain UTF-8 Chinese literals; without /utf-8 MSVC interprets\n'
             '# them via the system codepage and some characters become "?" in the binary.\n'
             'target_compile_options(${PROJECT_NAME} PRIVATE $<$<CXX_COMPILER_ID:MSVC>:/utf-8>)\n'
             '# --- END zh-CN localization: MSVC utf-8 ---\n')
    open(cm, 'w', encoding='utf-8', newline='').write(text)
    print('  cmake utf-8   : applied (%s)' % cm)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src_root, out_root = sys.argv[1], sys.argv[2]

    # MSVC 编码链修复：源码含无 BOM 的 UTF-8 中文，MSVC 默认按系统代码页
    # (CP1252) 解释会把部分字符编译成 '?'。必须在 copytree 之前打，
    # 因为它改的是 src_root 上一级的 CMakeLists.txt（upstream/CMakeLists.txt）。
    patch_cmake_utf8(src_root)

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
            rel = os.path.relpath(p, out_root).replace('\\', '/')
            if rel.startswith(UI_DIRS):
                ovr = next((t for suffix, t in FILE_OVERRIDES.items() if rel.endswith(suffix)), None)
                new = translate_ui_literals(new, tmap, stats, ovr)
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
