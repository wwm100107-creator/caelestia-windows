# Caelestia Shell for Windows 11

Replication of the **Caelestia Material 3 Fluid Shell** ([caelestia-dots/shell](https://github.com/caelestia-dots/shell)) directly on Windows 11 with Zebar v3, GlazeWM, Flow Launcher, and Python backend scripts.

---

## 🌟 Tính năng nổi bật

1. **Top Morphing Dashboard (Bảng điều khiển động mép trên)**:
   - **Tương tác chạm biên thông minh:** Đẩy chuột lên mép trên màn hình để thả bảng xuống mượt mà.
   - **Tự động đóng siêu nhạy:** Rời chuột ra ngoài bảng 0.1 giây bảng tự động co lại.
   - **Concave Fluid Ears:** Thiết kế bo cong tiếp giáp màn hình chuẩn Material You fluid.
   - **Thời gian thực:** Đồng hồ thời gian thực nhảy từng giây (HH:MM:SS) luôn hiển thị ở header, thẻ DateTime và bộ đếm thời gian phát nhạc.

2. **4 Tabs Giao diện Chức năng Toàn diện**:
   - **Dashboard (Bento Grid):**
     - Thời tiết thời gian thực (Open-Meteo, chuyển đổi °C/°F, mở MSN Weather).
     - Thông tin hệ thống & người dùng kèm 4 nút tác vụ nhanh: Chụp màn hình (Snipping Tool), Dọn RAM tức thì, Mở PowerShell, Khóa máy.
     - Đồng hồ dọc & Pomodoro Timer 25 phút.
     - Lịch tháng tương tác: cuộn chuột chuyển tháng, thêm/xóa ghi chú ngày lưu bền vững.
     - 3 thanh trượt dọc tương tác: Chỉnh âm lượng Windows, chỉnh độ sáng màn hình WMI, hiển thị/dọn RAM.
     - Trình phát media thu nhỏ kèm Bongo Cat chuyển động theo nhịp nhạc.
   - **Media (Trình điều khiển đa phương tiện):**
     - Vòng sóng nhạc 36 thanh (Radial Visualizer) chuyển động theo trạng thái phát.
     - Nút mở Windows Volume Mixer và YouTube / Spotify nhanh.
   - **Performance (Hiệu năng phần cứng):**
     - 3 vòng đo kép (GPU temp & usage, CPU temp & usage, RAM & ổ cứng C:\ thực tế).
     - Nhấp trực tiếp để dọn RAM hoặc mở Task Manager / Cài đặt đồ họa.
   - **Workspaces (Quản lý không gian & Khởi chạy):**
     - Quản lý và chuyển đổi workspace GlazeWM (1 - 5).
     - 3 chế độ: Kho hình nền (Wallpaper Carousel), Bảng khởi chạy ứng dụng nhanh (Quick Apps), Quản lý & đóng nhanh các cửa sổ đang mở (Active Windows).
     - Ô nhập lệnh và máy tính cầm tay trực tiếp.

3. **Material You Dynamic Theming (Python M3 OKLCH Engine)**:
   - Tự động quét màu chủ đạo từ hình nền Desktop (hoặc thư mục Wallpapers).
   - Sinh bảng màu Material You 38 tokens (OKLCH color space).
   - Đồng bộ màu tức thì tới toàn bộ giao diện qua CSS variables.

---

## 🚀 Cách sử dụng

* **Bật Caelestia Shell:**
  - Nhấp đúp chuột vào: `Bat-Caelestia.bat` (hoặc chạy `powershell -ExecutionPolicy Bypass -File .\start-caelestia.ps1`).
* **Tắt trở về Windows gốc:**
  - Nhấp đúp chuột vào: `Tat-Caelestia.bat` (hoặc chạy `powershell -ExecutionPolicy Bypass -File .\stop-caelestia.ps1`).
  - Toàn bộ thanh taskbar Windows và màn hình ban đầu sẽ được khôi phục nguyên trạng.

---

## 📁 Cấu trúc thư mục

```
caelestia-windows/
├── Bat-Caelestia.bat         # File nhấp đúp để khởi chạy
├── Tat-Caelestia.bat         # File nhấp đúp để tắt sạch sẽ
├── start-caelestia.ps1       # Script khởi động toàn bộ stack
├── stop-caelestia.ps1        # Script tắt và phục hồi Windows gốc
├── glazewm-config.yaml       # Cấu hình GlazeWM tiling
├── bin/                      # Binaries (GlazeWM standalone CLI)
├── scripts/                  # Các tiến trình nền
│   ├── mouse_edge.py         # Quét chuột mép trên + Xóa viền vàng DWM
│   ├── sync_palette.py       # Engine sinh màu Material You từ hình nền
│   ├── sys_actions.py        # Win32 APIs: Dọn RAM, độ sáng WMI, ổ đĩa, quản lý cửa sổ
│   └── taskbar_ctl.py        # Điều khiển ẩn/hiện Taskbar Windows
└── zebar-pack/               # Bộ giao diện Zebar Webview
    ├── zpack.json            # Cấu hình widget và quyền shell commands
    ├── dashboard.html        # Giao diện bảng điều khiển thả xuống 4 tab
    ├── caelestia.css         # CSS Material 3 fluid tokens
    ├── palette.json          # Bảng màu Material You đang áp dụng
    └── assets/               # Biểu tượng, GIF, avatar, thumbnail video
```
