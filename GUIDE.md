# 📖 Hướng Dẫn Sử Dụng Kling Video Generator

## 🎯 Giới Thiệu

**Kling Video Generator** là công cụ tự động hóa việc tạo video trên Kling AI với giao diện đồ họa thân thiện, hỗ trợ:
- ✅ Tạo video hàng loạt từ ảnh + prompt
- ✅ Xử lý nhiều thư mục cùng lúc
- ✅ Quản lý phiên đăng nhập
- ✅ Theo dõi tiến độ real-time
- ✅ Xác minh prompt trước khi download

---

## 📁 Chuẩn Bị Dữ Liệu

### Cấu trúc thư mục:

```
root_folder/
  ├── folder1/
  │   ├── 1.jpg          ← Ảnh đầu tiên
  │   ├── 2.jpg          ← Ảnh thứ hai
  │   ├── 3.jpg
  │   └── prompts.txt    ← File chứa prompts
  ├── folder2/
  │   ├── 1.jpg
  │   ├── 2.jpg
  │   └── prompts.txt
  └── folder3/
      ├── 1.jpg
      ├── 2.jpg
      └── prompts.txt
```

### File `prompts.txt`:

```
1: a cute cat playing with a ball
2: a dog running in the park
3: beautiful sunset over the ocean
```

**Lưu ý:**
- Mỗi dòng = 1 prompt
- Số thứ tự phải khớp với tên ảnh (1.jpg → prompt 1)
- Định dạng: `số: nội dung prompt`

---

## 🚀 Hướng Dẫn Sử Dụng

### **Bước 1: Khởi động ứng dụng**

**Cách 1: Từ Finder (Khuyến nghị)**
1. Mở Finder
2. Đến thư mục: `Kling_advance/`
3. Double-click: `KlingVideoGenerator.app`

**Cách 2: Từ Terminal**
```bash
cd Kling_advance
./start.sh
```

**⚠️ Lần đầu chạy:**
- macOS có thể chặn app
- Right-click app → Chọn **"Open"**
- Hoặc: Terminal → `xattr -cr KlingVideoGenerator.app`
- Hoặc: System Preferences → Security & Privacy → **"Open Anyway"**

---

### **Bước 2: Chọn thư mục gốc**

1. Click nút **"..."** bên cạnh "Thư mục:"
2. Chọn thư mục root chứa các folder con
3. ✅ Danh sách folders sẽ hiển thị tự động

---

### **Bước 3: Chọn folders cần xử lý**

- ☑️ **Check** vào folders muốn xử lý
- ☐ **Uncheck** folders không muốn xử lý
- Buttons:
  - **Chọn tất cả**: Check tất cả folders
  - **Bỏ chọn**: Uncheck tất cả
  - **🔄**: Refresh danh sách

---

### **Bước 4: Cấu hình**

**Cài đặt:**
- ☐ **Ẩn trình duyệt**: Check để chạy ở chế độ nền (khuyên dùng sau khi đã login)
- **Video đồng thời**: 2 (khuyến nghị, tránh quá tải)
- **Khoảng kiểm tra**: 10s (thời gian đợi giữa các lần check)

---

### **Bước 5: Đăng nhập (Lần đầu tiên)**

1. Click **"🌐 Mở trình duyệt"**
2. Trình duyệt sẽ mở trang Kling AI
3. **Đăng nhập** vào tài khoản của bạn
4. Sau khi login xong, click **"💾"** để lưu phiên
5. ✅ Status hiển thị: **"✓ Đã có phiên"**

**Lưu ý:**
- Phiên đăng nhập lưu trong `state.json`
- Lần sau không cần login lại
- Click **"🗑️"** để xóa phiên nếu muốn đổi tài khoản

---

### **Bước 6: Bắt đầu xử lý**

1. Click **"▶ Bắt đầu"**
2. Tool sẽ tự động:
   - Upload ảnh + prompt
   - Chờ video generate
   - **Verify prompt** trước khi download
   - Download video về thư mục gốc

**Theo dõi tiến độ:**
- 📊 **Progress bar**: Hiển thị % hoàn thành
- 📝 **Nhật ký**: Log real-time
- Màu log:
  - 🔵 **INFO**: Thông tin
  - 🟢 **SUCCESS**: Thành công
  - 🟡 **WARNING**: Cảnh báo
  - 🔴 **ERROR**: Lỗi

---

### **Bước 7: Điều khiển**

**Buttons:**
- **⏸ Tạm dừng**: Pause tạm thời (click lại để Resume)
- **⏹ Dừng lại**: Stop hoàn toàn

**Export logs:**
- Click **"Xuất nhật ký"** để lưu logs ra file text
- Click **"Xóa nhật ký"** để xóa logs hiện tại

---

## 🎯 Workflow Tự Động

```
┌──────────────────────────┐
│ 1. Chọn folder & check   │
├──────────────────────────┤
│ 2. Mở trình duyệt        │
├──────────────────────────┤
│ 3. Login (lần đầu)       │
├──────────────────────────┤
│ 4. Lưu phiên             │
├──────────────────────────┤
│ 5. Bắt đầu               │
└──────────────────────────┘
           ↓
    ┌─────────────┐
    │  Folder 1   │
    └─────────────┘
           ↓
    Upload ảnh + prompt
           ↓
    Generate video
           ↓
    ✓ Verify prompt
           ↓
    Download video
           ↓
    ┌─────────────┐
    │  Folder 2   │ ← Tự động chuyển
    └─────────────┘
           ↓
       [...]
           ↓
    ┌─────────────┐
    │ Hoàn thành  │
    └─────────────┘
```

---

## ⚙️ Tính Năng Nâng Cao

### **1. Prompt Verification**
- Hệ thống tự động verify prompt trước khi download
- Đảm bảo 100% tải đúng video
- Nếu prompt không khớp → Skip + Log warning

### **2. Position Tracking**
- Track vị trí mỗi video trên feed
- Tự động update khi có video mới
- Không bị nhầm lẫn giữa các videos

### **3. Multi-folder Processing**
- Xử lý tuần tự từng folder
- Progress bar tự động reset cho mỗi folder
- Có thể pause/stop bất cứ lúc nào

---

## 🐛 Xử Lý Lỗi

### **Lỗi: "Cannot find prompt element"**
- **Nguyên nhân**: Prompt không tìm thấy trên article
- **Giải pháp**: Hệ thống tự động skip, video này sẽ bị bỏ qua

### **Lỗi: "Prompt mismatch"**
- **Nguyên nhân**: Prompt không khớp (có thể từ folder khác)
- **Giải pháp**: Skip video này, tiếp tục xử lý videos khác

### **Lỗi: "Download button not found"**
- **Nguyên nhân**: Video chưa generate xong hoặc UI thay đổi
- **Giải pháp**: Hệ thống tự động retry sau 10s

### **App bị chặn bởi macOS**
- Right-click app → **"Open"**
- Hoặc: System Preferences → Security & Privacy → **"Open Anyway"**

---

## 💡 Tips & Best Practices

### **✅ Nên:**
- Dùng 2 videos đồng thời (tránh quá tải)
- Lưu phiên sau khi login (không cần login lại)
- Check log thường xuyên để phát hiện lỗi sớm
- Export log nếu gặp vấn đề cần report

### **❌ Không nên:**
- Tắt trình duyệt khi đang chạy
- Thao tác thủ công trên trang web trong lúc tool đang chạy
- Dùng chế độ ẩn trình duyệt nếu chưa login
- Queue quá nhiều videos đồng thời (>3)

---

## 📊 Kết Quả

Sau khi hoàn thành, mỗi folder sẽ có:

```
folder1/
  ├── 1.jpg
  ├── 1.mp4          ← Video đã download
  ├── 2.jpg
  ├── 2.mp4          ← Video đã download
  ├── 3.jpg
  ├── 3.mp4          ← Video đã download
  └── prompts.txt
```

---

## 🆘 Hỗ Trợ

**Nếu gặp vấn đề:**
1. Check log để xem lỗi cụ thể
2. Export log ra file
3. Thử xóa phiên và login lại
4. Restart app

**Liên hệ:**
- GitHub Issues: [Link to your repo]
- Email: [Your email]

---

## 📝 Changelog

**v1.0.0 (2025-09-28)**
- ✅ UI 2 cột gọn gàng
- ✅ Folder selection với checkbox
- ✅ Prompt verification
- ✅ Position tracking
- ✅ Session management
- ✅ Real-time progress tracking
- ✅ Log export

---

**Made with ❤️ for automated video generation**