# -*- coding: utf-8 -*-
"""
给 Menu.cpp 打补丁，让 ImGui 字体图集包含简体中文字形。

YimMenuV2 原本只合并了西里尔文（arial.ttf）和日文（meiryo.ttc），
没有中文字形范围，所以中文标题会渲染成空白方框（豆腐块）。

本补丁按优先级尝试 msyh.ttc -> msyhbd.ttc -> simhei.ttf -> simsun.ttc
-> arialuni.ttf，取第一个存在的中文字体，用
GetGlyphRangesChineseSimplifiedCommon() 合并进图集。

补丁是"追加式"的：只插入一段额外的合并步骤，不改动原有行为；
字体缺失时跳过而不是报错。可重复执行（幂等）。
"""
import os, sys

ANCHOR = 'io.Fonts->AddFontFromFileTTF((std::filesystem::path(std::getenv("SYSTEMROOT")) / "Fonts" / "meiryo.ttc").string().c_str(), size, &FontCfg, io.Fonts->GetGlyphRangesJapanese());'

SNIPPET = r'''
		// --- BEGIN zh-CN localization: merge Simplified Chinese glyph ranges ---
		// Chinese UI text would render as empty boxes without this.
		{
			static constexpr const char* kChineseFonts[] = {
			    "msyh.ttc",     // Microsoft YaHei (Windows 10/11)
			    "msyhbd.ttc",   // Microsoft YaHei Bold
			    "simhei.ttf",   // SimHei
			    "simsun.ttc",   // SimSun / NSimSun
			    "arialuni.ttf", // Arial Unicode MS (fallback)
			};

			for (const char* name : kChineseFonts)
			{
				auto path = std::filesystem::path(std::getenv("SYSTEMROOT")) / "Fonts" / name;
				std::error_code ec;
				if (!std::filesystem::exists(path, ec))
					continue;
				io.Fonts->AddFontFromFileTTF(
				    path.string().c_str(),
				    size,
				    &FontCfg,
				    io.Fonts->GetGlyphRangesChineseSimplifiedCommon());
				break; // 取第一个存在的字体
			}
		}
		// --- END zh-CN localization ---
'''


def main():
    if len(sys.argv) != 2:
        sys.exit('usage: python localization/patch_font.py <src/game/frontend/Menu.cpp>')
    path = sys.argv[1]
    text = open(path, encoding='utf-8').read()

    if 'BEGIN zh-CN localization' in text:
        print('  font patch  : already applied, skipped')
        return 0
    if ANCHOR not in text:
        print('WARNING: anchor line not found, font patch skipped.', file=sys.stderr)
        print('         Chinese text may render as empty boxes.', file=sys.stderr)
        return 0

    # 保留锚点原有的缩进
    open(path, 'w', encoding='utf-8', newline='').write(
        text.replace(ANCHOR, SNIPPET + "\t\t" + ANCHOR, 1))
    print('  font patch  : applied')
    return 0


if __name__ == '__main__':
    sys.exit(main())
