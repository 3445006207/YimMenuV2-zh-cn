# YimMenuV2 简体中文版自动构建

本仓库只包含「构建注入即中文的 YimMenuV2.dll」所需的汉化脚本与定制词典（共 5 个文件）。
源码在构建时自动从上游 [YimMenu/YimMenuV2](https://github.com/YimMenu/YimMenuV2)（`enhanced` 分支）拉取，官方译文亦在构建时按固定 commit 下载，本仓库不保存源码。

## 使用

- 推送到 `main` 会自动触发构建；也可以在 Actions → Build YimMenuV2 (zh-CN) → Run workflow 手动触发（默认 Release）。
- 构建约 5～15 分钟，完成后在本次运行页面底部 **Artifacts** 下载：
  - `YimMenuV2-zh-CN-msvc.zip`（推荐）
  - `YimMenuV2-zh-CN-clang.zip`
- 解压得到 `YimMenuV2.dll`，注入后菜单即为简体中文，无需任何外部语言包。

## 上游更新后

上游 `enhanced` 分支更新后，直接重跑工作流即可自动把汉化应用到新源码；个别未匹配的句子保持英文，不影响编译。

## 汉化说明

- 官方译文：构建时从 [YimMenu/Translations](https://github.com/YimMenu/Translations) 下载
  （commit `c053bb8` 固定，可复现），用 en_US.json + zh_CN.json 组合出「英文原文→中文」映射
- 定制译文：`localization/translations_part_1.json` + `translations_part_2.json`
  （共 1367 条，覆盖官方未收录及需要修正的界面文案；两份合并 + 官方 = 已验证的 3399 条词典）
- 打补丁：`localization/apply.py`；字体：`localization/patch_font.py`（合并简体中文字形，否则中文显示方框）
- 刻意不翻译：Command 内部名（joaat 哈希/配置键）、`CMOD_*`/`HORN_*` 游戏资产标签、ImGui `##` 隐藏 ID
