# YimMenuV2 简体中文版自动构建

本仓库只包含「构建注入即中文的 YimMenuV2.dll」所需的**汉化脚本与定制词典**（`localization/` 下 8 个文件 + 本工作流）。
源码在构建时自动从上游 [YimMenu/YimMenuV2](https://github.com/YimMenu/YimMenuV2)（`enhanced` 分支）拉取，官方译文亦在构建时按固定 commit 下载，**本仓库不保存源码，也不保存编译产物**。

## 下载已编译好的 DLL

最新版在 **[Releases](../../releases/latest)** 页的附件 `YimMenuV2.dll` 直接下载即可（无需自己编译）。
历次构建对应的 artifact（msvc + clang 两套）可在对应 Actions 运行页面底部 **Artifacts** 找到。

## 使用

- 把 `YimMenuV2.dll` 注入游戏，菜单即为简体中文，无需任何外部语言包。
- 推送到 `main` 会自动触发构建；也可以在 Actions → Build YimMenuV2 (zh-CN) → Run workflow 手动触发（默认 Release）。
- 构建约 5～15 分钟，完成后本次运行页面底部 **Artifacts** 提供：
  - `YimMenuV2-zh-CN-msvc.zip`（推荐，同 Release 附件）
  - `YimMenuV2-zh-CN-clang.zip`
- msvc 产物会自动发布为新 Release（tag `zh-cn-<运行号>`）。

## 上游更新后

上游 `enhanced` 分支更新后，直接重跑工作流即可自动把汉化应用到新源码；个别未匹配的句子保持英文，不影响编译。

## 汉化说明

- **官方译文**：构建时从 [YimMenu/Translations](https://github.com/YimMenu/Translations) 下载
  （commit `c053bb8` 固定，可复现），用 en_US.json + zh_CN.json 组合出「英文原文→中文」映射（2068 条）
- **定制译文**：`localization/translations_part_1.json` ~ `translations_part_6.json`
  （共 1725 条，覆盖官方未收录及需要修正的界面文案；与官方合并去重后为 **3769 条**词典）
- **打补丁**：`localization/apply.py`
  - 词表合并 + 逐字符状态机扫描源码字符串字面量（正则无法正确处理 `("id"_J, "标签")` 这类相邻字面量）
  - UI 目录白名单 + 词典精确命中，整体排除 `core/scripting/**`（避免误翻译 Lua API 常量名）
  - MSVC 追加 `/utf-8` 编译选项（否则无 BOM 的 UTF-8 中文字面量会被按系统代码页解释、变成 `?`）
- **字体**：`localization/patch_font.py`
  - 扫描汉化后源码的全部字符串字面量，**动态收集**实际用到的字形（含 ImGui 内置 2500 字表缺的「辑剪贴」等），生成精确的 `kZhGlyphRanges[]`
  - 跳过 PUA 区（FontAwesome 图标由嵌入 IconFont 提供）
- **刻意不翻译**：Command 内部名（joaat 哈希/配置键）、`CMOD_*`/`HORN_*` 游戏资产标签、ImGui `##` 隐藏 ID、
  Windows 字体目录名 `Fonts` 等路径串（`apply.py` 内有路径上下文守卫）
