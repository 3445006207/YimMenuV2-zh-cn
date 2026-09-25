#include "Neon.hpp"
#include "game/pointers/Pointers.hpp"
#include "game/frontend/Menu.hpp"
#include "core/frontend/manager/UIManager.hpp"
#include "game/frontend/submenus/Settings/GUISettings.hpp"

namespace YimMenu
{
	namespace
	{
		// ImGui 没有原生辉光，用多层描边由粗到细、逐层提高 alpha 来模拟霓虹发光
		void GlowRect(ImDrawList* drawList, ImVec2 min, ImVec2 max, ImU32 color, float rounding, float intensity)
		{
			// 由外到内四层，越靠内越亮
			ImU32 c1 = (color & 0x00FFFFFF) | (static_cast<ImU32>(38 * intensity) << 24);
			ImU32 c2 = (color & 0x00FFFFFF) | (static_cast<ImU32>(80 * intensity) << 24);
			ImU32 c3 = (color & 0x00FFFFFF) | (static_cast<ImU32>(140 * intensity) << 24);
			ImU32 c4 = (color & 0x00FFFFFF) | (static_cast<ImU32>(225 * intensity) << 24);

			drawList->AddRect(min, max, c1, rounding, ImDrawFlags_None, 4.0f);
			drawList->AddRect(min, max, c2, rounding, ImDrawFlags_None, 2.5f);
			drawList->AddRect(min, max, c3, rounding, ImDrawFlags_None, 1.5f);
			drawList->AddRect(min, max, c4, rounding, ImDrawFlags_None, 1.0f);
		}

		// 带多层辉光的填充矩形（卡片底 + 边框发光）
		void GlowCard(ImDrawList* drawList, ImVec2 min, ImVec2 max, ImU32 fill, ImU32 glow, float rounding, float intensity)
		{
			drawList->AddRectFilled(min, max, fill, rounding);
			GlowRect(drawList, min, max, glow, rounding, intensity);
		}
	}

	void RenderNeonTheme()
	{
		YimMenu::SyncColorCommandsToStyle();

		float windowWidth = *YimMenu::Pointers.ScreenResX / 2.5f;
		if (windowWidth < 900.0f)
			windowWidth = 900.0f; // 保证左右分栏有足够空间

		float windowHeight = *YimMenu::Pointers.ScreenResY / 2.2f;
		float centerX = (*YimMenu::Pointers.ScreenResX - windowWidth) / 2.0f;
		float centerY = (*YimMenu::Pointers.ScreenResY - windowHeight) / 2.0f;

		ImGui::SetNextWindowSize(ImVec2(windowWidth, windowHeight), ImGuiCond_FirstUseEver);
		ImGui::SetNextWindowPos(ImVec2(centerX, centerY), ImGuiCond_FirstUseEver);

		ImGuiWindowFlags flags = ImGuiWindowFlags_NoTitleBar | ImGuiWindowFlags_NoScrollbar
		                       | ImGuiWindowFlags_NoScrollWithMouse | ImGuiWindowFlags_NoCollapse;

		if (ImGui::Begin("##NeonRootWindow", nullptr, flags))
		{
			ImDrawList* drawList = ImGui::GetWindowDrawList();
			ImVec2 winPos = ImGui::GetWindowPos();
			ImVec2 winSize = ImGui::GetWindowSize();

			const ImU32 accentCyan = IM_COL32(0x00, 0xE5, 0xFF, 255);
			const ImU32 accentMagenta = IM_COL32(0xFF, 0x2D, 0x95, 255);
			const ImU32 textColor = ImGui::GetColorU32(ImGuiCol_Text);
			const ImU32 textDim = ImGui::GetColorU32(ImGuiCol_TextDisabled);

			// 整窗底色（比默认更深）
			drawList->AddRectFilled(winPos, winPos + winSize, IM_COL32(0x08, 0x09, 0x0D, 245), 0.0f);

			const auto& submenus = YimMenu::UIManager::GetSubmenus();
			auto activeSubmenu = YimMenu::UIManager::GetActiveSubmenu();

			// 两张卡片的矩形
			ImVec2 navMin(winPos.x + 10.0f, winPos.y + 10.0f);
			ImVec2 navMax(navMin.x + YimMenu::Neon::kNavCardWidth, winPos.y + winSize.y - 10.0f);

			ImVec2 contentMin(navMax.x + YimMenu::Neon::kCardGap, winPos.y + 10.0f);
			ImVec2 contentMax(winPos.x + winSize.x - 10.0f, winPos.y + winSize.y - 10.0f);

			// ---- 左侧导航卡片 ----
			GlowCard(drawList, navMin, navMax, IM_COL32(0x0E, 0x10, 0x16, 255), accentCyan, YimMenu::Neon::kCardRounding, 0.55f);

			// 标题区（品牌名 + 一条霓虹分隔线）
			ImVec2 titlePos(navMin.x + 14.0f, navMin.y + 12.0f);
			drawList->AddText(titlePos, accentCyan, "YimMenu");
			drawList->AddText(ImVec2(titlePos.x, titlePos.y + 20.0f), accentMagenta, "V2  赛博");

			float dividerY = navMin.y + 54.0f;
			GlowRect(drawList, ImVec2(navMin.x + 12.0f, dividerY), ImVec2(navMax.x - 12.0f, dividerY + 1.0f), accentCyan, 0.0f, 0.8f);

			// 导航条目（自绘：图标 + 文字 + 激活指示条 + 辉光）
			float entryY = dividerY + 12.0f;
			for (size_t i = 0; i < submenus.size(); ++i)
			{
				auto& submenu = submenus[i];
				bool isActive = (submenu == activeSubmenu);

				ImVec2 eMin(navMin.x + 10.0f, entryY);
				ImVec2 eMax(navMax.x - 10.0f, entryY + YimMenu::Neon::kEntryHeight);

				ImGui::SetCursorScreenPos(eMin);
				ImGui::PushID(static_cast<int>(i));
				ImGui::InvisibleButton("##NeonNavEntry", ImVec2(eMax.x - eMin.x, eMax.y - eMin.y));
				bool hovered = ImGui::IsItemHovered();
				bool clicked = ImGui::IsItemClicked();
				ImGui::PopID();

				if (clicked)
				{
					YimMenu::UIManager::SetActiveSubmenu(submenu);
					YimMenu::UIManager::SetShowContentWindow(true);
				}

				// 条目底与描边
				if (isActive)
				{
					drawList->AddRectFilled(eMin, eMax, IM_COL32(0x00, 0xE5, 0xFF, 26), YimMenu::Neon::kEntryRounding);
					GlowRect(drawList, eMin, eMax, accentCyan, YimMenu::Neon::kEntryRounding, 0.85f);
					// 左指示条
					drawList->AddRectFilled(ImVec2(eMin.x, eMin.y + 3.0f),
					                        ImVec2(eMin.x + YimMenu::Neon::kAccentBarWidth, eMax.y - 3.0f),
					                        accentCyan, 2.0f);
				}
				else if (hovered)
				{
					drawList->AddRectFilled(eMin, eMax, IM_COL32(0xFF, 0x2D, 0x95, 18), YimMenu::Neon::kEntryRounding);
					GlowRect(drawList, eMin, eMax, accentMagenta, YimMenu::Neon::kEntryRounding, 0.45f);
				}

				// 图标
				ImU32 iconColor = isActive ? accentCyan : (hovered ? accentMagenta : textDim);
				ImFont* iconFont = YimMenu::Menu::Font::g_AwesomeFont;
				if (iconFont && !submenu->m_Icon.empty())
				{
					ImGui::PushFont(iconFont);
					ImVec2 iconSize = ImGui::CalcTextSize(submenu->m_Icon.c_str());
					drawList->AddText(iconFont, 0.0f,
					                  ImVec2(eMin.x + 12.0f, eMin.y + (eMax.y - eMin.y - iconSize.y) * 0.5f),
					                  iconColor, submenu->m_Icon.c_str());
					ImGui::PopFont();
				}

				// 文字（激活时用亮色）
				ImU32 labelColor = (isActive || hovered) ? textColor : textDim;
				ImVec2 labelSize = ImGui::CalcTextSize(submenu->m_Name.c_str());
				drawList->AddText(ImVec2(eMin.x + 42.0f, eMin.y + (eMax.y - eMin.y - labelSize.y) * 0.5f),
				                  labelColor, submenu->m_Name.c_str());

				entryY += YimMenu::Neon::kEntryHeight + 4.0f;
			}

			// ---- 右侧内容卡片 ----
			GlowCard(drawList, contentMin, contentMax, IM_COL32(0x0E, 0x10, 0x16, 255), accentMagenta, YimMenu::Neon::kCardRounding, 0.45f);

			if (activeSubmenu && YimMenu::UIManager::ShowingContentWindow())
			{
				// 顶部分类选择栏
				ImGui::SetCursorScreenPos(ImVec2(contentMin.x + 10.0f, contentMin.y + 10.0f));
				if (ImGui::BeginChild("##NeonCategories", ImVec2(contentMax.x - contentMin.x - 20.0f, YimMenu::Neon::kHeaderHeight - 16.0f), false, ImGuiWindowFlags_NoScrollbar | ImGuiWindowFlags_NoScrollWithMouse))
				{
					activeSubmenu->DrawCategorySelectors();
				}
				ImGui::EndChild();

				// 分隔线
				float sepY = contentMin.y + YimMenu::Neon::kHeaderHeight;
				GlowRect(drawList, ImVec2(contentMin.x + 12.0f, sepY), ImVec2(contentMax.x - 12.0f, sepY + 1.0f), accentMagenta, 0.0f, 0.7f);

				// 内容区
				ImGui::SetCursorScreenPos(ImVec2(contentMin.x + 10.0f, sepY + 8.0f));
				if (ImGui::BeginChild("##NeonOptions", ImVec2(contentMax.x - contentMin.x - 20.0f, contentMax.y - sepY - 18.0f), false))
				{
					ImFont* optionsFont = YimMenu::UIManager::GetOptionsFont();
					if (optionsFont)
						ImGui::PushFont(optionsFont);

					activeSubmenu->Draw();

					if (optionsFont)
						ImGui::PopFont();
				}
				ImGui::EndChild();
			}
		}
		ImGui::End();
	}
}
