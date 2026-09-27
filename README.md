# Capstone API Security Demo - Cloud API & Network Security

Dự án này là minh họa cho đề tài **Bảo mật Ứng dụng Mạng Dựa trên API trên Cloud cho Dịch vụ Công ty Nhỏ** (Môn NT219 - Cryptography). 

Hệ thống được thiết kế theo kiến trúc **API-first** kết hợp các tiêu chuẩn bảo mật đám mây (Cloud Security), bao gồm: API Gateway, Identity Provider (IdP) độc lập, tự động hóa DevSecOps và các biện pháp chống lại các lỗ hổng API phổ biến nhất (OWASP API Security Top 10).

## 1. Kiến trúc hệ thống

```text
Browser / Postman
      |
      | HTTP 8080 hoặc HTTPS 8443
      v
Kong API Gateway  <--->  Keycloak IdP (Cổng 8081 - Xác thực SSO, OAuth2 PKCE)
      |
      | internal Docker network
      v
FastAPI Backend
      |
      v
PostgreSQL Database
```

## 2. Các tính năng bảo mật đã triển khai

### 2.1. Bảo vệ mặt phẳng API (API Security)
- **Identity Provider (IdP):** Hệ thống tích hợp **Keycloak** làm trung tâm quản lý danh tính (SSO).
- **Xác thực an toàn:** Sử dụng luồng **OAuth2 Authorization Code + PKCE** chuẩn công nghiệp cho Frontend SPA (Thay vì tự xử lý user/password ở backend).
- **Xác thực JWT (RS256):** FastAPI backend tải cấu hình JWKS (Public Keys) từ Keycloak để tự động xác minh tính hợp lệ của Token chữ ký số.

### 2.2. Kiểm soát luồng mạng (Network Security)
- **API Gateway (Kong):** Đứng làm ranh giới (Edge), xử lý HTTPS/TLS termination để mã hóa đường truyền.
- **Chứng chỉ số TLS tự ký (Self-signed):** Cấu hình `localhost.crt` áp dụng ở Kong.
- **Bảo mật mạng nội bộ:** FastAPI và PostgreSQL chỉ giao tiếp qua mạng nội bộ Docker (`capstone_net`), không mở cổng trực tiếp ra Internet.

### 2.3. Tự động hóa DevSecOps (CI/CD Pipeline)
- **Quét bảo mật mã nguồn (SAST):** Tích hợp `Bandit`.
- **Quét lỗ hổng thư viện (SCA):** Tích hợp `Safety`.
- **Quét rò rỉ mã bí mật (Secret Scanning):** Tích hợp `TruffleHog`.
- **Kiểm thử động (DAST):** Tích hợp `OWASP ZAP`.
*(Xem cấu hình tại `.github/workflows/security-scan.yml`)*

### 2.4. Khắc phục lỗ hổng OWASP API Top 10
Hệ thống có trang bị sẵn các endpoint mô phỏng tấn công (Vulnerable) và cách phòng thủ (Secure):
1. **BOLA (Broken Object Level Authorization):** 
   - Lỗi: API cho phép người dùng đổi `id` để xem hóa đơn của người khác. 
   - Fix: Kiểm tra quyền sở hữu (`owner_id`) và phân quyền RBAC ở server.
2. **SSRF (Server-Side Request Forgery):**
   - Lỗi: API tải nội dung URL độc hại, làm rò rỉ cổng nội bộ.
   - Fix: Cơ chế DNS Lookup và chặn dải IP Private/Loopback.
3. **Webhook Forgery:**
   - Lỗi: Gửi payload giả mạo báo thanh toán thành công.
   - Fix: Yêu cầu chữ ký xác thực `X-Hub-Signature-256` bằng HMAC SHA-256.
4. **Excessive Data Exposure:**
   - Lỗi: API trả về tất cả thông tin trong DB (kể cả chuỗi Hash mật khẩu).
   - Fix: Dùng `response_model` (Pydantic Schema) để tự động lọc dữ liệu nhạy cảm.
5. **Rate Limiting chống Brute-force:**
   - Cấu hình tại Kong: Chặn các đợt gọi API quá tần suất (ví dụ: tối đa 100 request/phút toàn hệ thống).

---

## 3. Hướng dẫn chạy dự án

**Yêu cầu:** Máy đã cài Docker và Docker Compose.

1. **Clone dự án & Khởi động Docker:**
   Mở Terminal ở thư mục chứa mã nguồn và chạy ngầm (chế độ detached):
   ```bash
   docker compose up -d --build
   ```
   *(Lưu ý: Lần đầu tiên khởi động Keycloak bằng Java có thể mất 1-2 phút).*

2. **Theo dõi log hệ thống:**
   Để xem log (nhật ký hoạt động) của tất cả các service theo thời gian thực (như request API, cảnh báo lỗi), bạn chạy lệnh:
   ```bash
   docker compose logs -f
   ```
   *(Bấm `Ctrl + C` để thoát khỏi chế độ xem log, hệ thống vẫn tiếp tục chạy ngầm).*

3. **Truy cập ứng dụng:**
   - Giao diện Web chính (có chứng chỉ HTTPS tự ký): `https://localhost:8443`
   - Tài liệu API (Swagger UI): `https://localhost:8443/docs`
   *(Trình duyệt sẽ cảnh báo SSL do là self-signed, bạn bấm Advanced -> Proceed).*

4. **Tài khoản mẫu (Đăng nhập qua Keycloak):**

   | Username | Password    | Role  |
   |----------|-------------|-------|
   | user1    | password123 | user  |
   | user2    | password123 | user  |
   | admin    | admin123    | admin |

---

## 4. Hướng dẫn Demo & Thuyết trình

Toàn bộ các lỗ hổng đều có giao diện trực quan trên trang web chính (`https://localhost:8443/`).
- Bấm nút **Đăng nhập bằng Keycloak**, trình duyệt sẽ chuyển hướng sang IdP. Nhập tài khoản `user1` để đăng nhập. *(Nếu Keycloak yêu cầu cập nhật Profile, hãy nhập 1 email và tên giả bất kỳ).*
- Lướt xuống từng Section trên màn hình để kiểm tra trực tiếp:
  - **Mục 4:** Demo lấy danh sách đơn hàng (Chỉ thấy đơn của user1). Đổi sang `admin` sẽ thấy tất cả.
  - **Mục 6:** Nhập URL nội bộ (vd: `http://localhost:5432`) vào ô SSRF -> Gọi API Vulnerable sẽ bị lộ dữ liệu / Gọi API Secure sẽ bị chặn 403.
  - **Mục 7:** Thử gửi Webhook Forgery. API Secure sẽ báo Invalid Signature.
  - **Mục 8:** Gọi API Exposure Vulnerable để thấy chuỗi mật khẩu băm bị lộ tung tóe. Gọi API Secure để thấy dữ liệu sạch sẽ, gọn gàng.

---

## 5. Cấu trúc mã nguồn chính

- `docker-compose.yml`: Kiến trúc tổng (FastAPI, Postgres, Kong, Keycloak).
- `app/main.py`: Khai báo API Gateway Backend.
- `app/routers/`: Chứa các endpoint API (Orders, Fetch SSRF, Webhooks, Users).
- `app/core/security.py`: Logic xác minh JWT chữ ký số với Keycloak JWKS.
- `app/frontend/`: Chứa giao diện Web (HTML/JS) đã code sẵn luồng OAuth2 PKCE.
- `idp/realm-export.json`: Cấu hình Keycloak Realm xuất sẵn (Client, Users, Roles).
- `gateway/kong.yml`: Cấu hình khai báo Route và Plugin cho Kong.
- `.github/workflows/`: Chứa kịch bản Pipeline CI/CD tự động quét lỗi bảo mật.
