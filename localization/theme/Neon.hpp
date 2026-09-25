#pragma once

// ---------------------------------------------------------------------------
// Neon 主题（赛博霓虹 / 左右分栏卡片）
//
// 设计意图：
//   - 深黑底 + 霓虹青主色 + 品红副色，营造赛博都市霓虹观感
//   - 左右两张悬浮卡片（左侧图标导航 / 右侧内容），中间留缝形成层次
//   - ImGui 无原生辉光，采用「同矩形多层描边、由粗到细、alpha 递增」模拟
// ---------------------------------------------------------------------------

namespace YimMenu::Neon
{
	// 布局常量
	inline constexpr float kNavCardWidth = 190.0f; // 左侧导航卡片宽度
	inline constexpr float kCardGap = 8.0f;        // 两张卡片之间的缝隙
	inline constexpr float kEntryHeight = 34.0f;   // 导航条目高度
	inline constexpr float kEntryRounding = 4.0f;  // 导航条目圆角
	inline constexpr float kCardRounding = 6.0f;   // 卡片圆角
	inline constexpr float kHeaderHeight = 58.0f;  // 内容卡片顶部分类选择栏高度
	inline constexpr float kAccentBarWidth = 3.0f; // 激活条左指示条宽度

	// 霓虹色板
	inline constexpr unsigned int kNeonCyan = 0x00E5FF;   // 主霓虹（青）
	inline constexpr unsigned int kNeonMagenta = 0xFF2D95; // 副霓虹（品红）
	inline constexpr unsigned int kNeonViolet = 0x8A5CFF;  // 辅色（紫）
}
