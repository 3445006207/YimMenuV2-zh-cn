void DefaultStyle()
	{
		ImGuiStyle& style = ImGui::GetStyle();
		// Text
		style.Colors[ImGuiCol_Text] = ImVec4(0.85f, 0.97f, 1.00f, 1.00f);
		style.Colors[ImGuiCol_TextDisabled] = ImVec4(0.38f, 0.47f, 0.55f, 1.00f);

		// Backgrounds（深黑，带一点冷蓝）
		style.Colors[ImGuiCol_WindowBg] = ImVec4(0.031f, 0.035f, 0.051f, 0.96f);
		style.Colors[ImGuiCol_ChildBg] = ImVec4(0.055f, 0.063f, 0.086f, 1.00f);
		style.Colors[ImGuiCol_PopupBg] = ImVec4(0.043f, 0.051f, 0.071f, 0.98f);

		// Borders（霓虹青，淡）
		style.Colors[ImGuiCol_Border] = ImVec4(0.00f, 0.90f, 1.00f, 0.22f);
		style.Colors[ImGuiCol_BorderShadow] = ImVec4(0.00f, 0.00f, 0.00f, 0.00f);

		// Frames
		style.Colors[ImGuiCol_FrameBg] = ImVec4(0.078f, 0.090f, 0.122f, 1.00f);
		style.Colors[ImGuiCol_FrameBgHovered] = ImVec4(1.00f, 0.18f, 0.58f, 0.35f);
		style.Colors[ImGuiCol_FrameBgActive] = ImVec4(1.00f, 0.18f, 0.58f, 0.55f);

		// Title bars
		style.Colors[ImGuiCol_TitleBg] = ImVec4(0.024f, 0.027f, 0.039f, 1.00f);
		style.Colors[ImGuiCol_TitleBgActive] = ImVec4(0.043f, 0.051f, 0.071f, 1.00f);
		style.Colors[ImGuiCol_TitleBgCollapsed] = ImVec4(0.016f, 0.020f, 0.027f, 1.00f);

		// Menus/tabs
		style.Colors[ImGuiCol_MenuBarBg] = ImVec4(0.055f, 0.063f, 0.086f, 1.00f);
		style.Colors[ImGuiCol_Tab] = ImVec4(0.00f, 0.90f, 1.00f, 0.20f);
		style.Colors[ImGuiCol_TabHovered] = ImVec4(1.00f, 0.18f, 0.58f, 0.45f);
		style.Colors[ImGuiCol_TabActive] = ImVec4(0.00f, 0.90f, 1.00f, 0.75f);
		style.Colors[ImGuiCol_TabUnfocused] = ImVec4(0.00f, 0.90f, 1.00f, 0.12f);
		style.Colors[ImGuiCol_TabUnfocusedActive] = ImVec4(0.00f, 0.90f, 1.00f, 0.40f);

		// Scrollbar
		style.Colors[ImGuiCol_ScrollbarBg] = ImVec4(0.020f, 0.024f, 0.035f, 0.80f);
		style.Colors[ImGuiCol_ScrollbarGrab] = ImVec4(0.00f, 0.65f, 0.75f, 0.55f);
		style.Colors[ImGuiCol_ScrollbarGrabHovered] = ImVec4(0.00f, 0.90f, 1.00f, 0.80f);
		style.Colors[ImGuiCol_ScrollbarGrabActive] = ImVec4(1.00f, 0.18f, 0.58f, 0.95f);

		// Checkmarks, sliders
		style.Colors[ImGuiCol_CheckMark] = ImVec4(0.00f, 0.90f, 1.00f, 1.00f);
		style.Colors[ImGuiCol_SliderGrab] = ImVec4(0.00f, 0.78f, 0.90f, 1.00f);
		style.Colors[ImGuiCol_SliderGrabActive] = ImVec4(1.00f, 0.18f, 0.58f, 1.00f);

		// Buttons（青主 / 品红激活）
		style.Colors[ImGuiCol_Button] = ImVec4(0.00f, 0.55f, 0.65f, 0.55f);
		style.Colors[ImGuiCol_ButtonHovered] = ImVec4(0.00f, 0.82f, 0.95f, 0.75f);
		style.Colors[ImGuiCol_ButtonActive] = ImVec4(1.00f, 0.18f, 0.58f, 0.90f);

		// Headers（菜单项/可折叠项）
		style.Colors[ImGuiCol_Header] = ImVec4(0.00f, 0.78f, 0.90f, 0.32f);
		style.Colors[ImGuiCol_HeaderHovered] = ImVec4(1.00f, 0.18f, 0.58f, 0.45f);
		style.Colors[ImGuiCol_HeaderActive] = ImVec4(0.00f, 0.90f, 1.00f, 0.70f);

		// Separators
		style.Colors[ImGuiCol_Separator] = ImVec4(0.00f, 0.90f, 1.00f, 0.30f);
		style.Colors[ImGuiCol_SeparatorHovered] = ImVec4(1.00f, 0.18f, 0.58f, 0.70f);
		style.Colors[ImGuiCol_SeparatorActive] = ImVec4(1.00f, 0.18f, 0.58f, 1.00f);

		// Resize grips
		style.Colors[ImGuiCol_ResizeGrip] = ImVec4(0.00f, 0.90f, 1.00f, 0.25f);
		style.Colors[ImGuiCol_ResizeGripHovered] = ImVec4(1.00f, 0.18f, 0.58f, 0.65f);
		style.Colors[ImGuiCol_ResizeGripActive] = ImVec4(1.00f, 0.18f, 0.58f, 0.95f);

		// Plots
		style.Colors[ImGuiCol_PlotLines] = ImVec4(0.00f, 0.90f, 1.00f, 1.00f);
		style.Colors[ImGuiCol_PlotLinesHovered] = ImVec4(1.00f, 0.18f, 0.58f, 1.00f);
		style.Colors[ImGuiCol_PlotHistogram] = ImVec4(0.00f, 0.78f, 0.90f, 1.00f);
		style.Colors[ImGuiCol_PlotHistogramHovered] = ImVec4(1.00f, 0.18f, 0.58f, 1.00f);

		// Drag & drop
		style.Colors[ImGuiCol_DragDropTarget] = ImVec4(1.00f, 0.18f, 0.58f, 0.90f);

		// Navigation highlighting
		style.Colors[ImGuiCol_NavHighlight] = ImVec4(0.00f, 0.90f, 1.00f, 1.00f);
		style.Colors[ImGuiCol_NavWindowingHighlight] = ImVec4(1.00f, 1.00f, 1.00f, 0.70f);
		style.Colors[ImGuiCol_NavWindowingDimBg] = ImVec4(0.20f, 0.20f, 0.20f, 0.20f);

		// Modal/background dimming
		style.Colors[ImGuiCol_ModalWindowDimBg] = ImVec4(0.02f, 0.02f, 0.03f, 0.55f);

		// Rounding（比默认更硬朗，贴赛博感）
		style.GrabRounding = style.FrameRounding = style.ChildRounding = style.WindowRounding = 5.0f;
		style.WindowPadding = ImVec2(10.0f, 10.0f);
		style.FramePadding = ImVec2(8.0f, 4.0f);
		style.ItemSpacing = ImVec2(8.0f, 6.0f);
		style.WindowBorderSize = 1.0f;
		style.FrameBorderSize = 0.0f;
	}

	