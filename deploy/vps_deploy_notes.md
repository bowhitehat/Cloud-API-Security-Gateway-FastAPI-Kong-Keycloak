# VPS / Cloud deploy notes

Muc tieu: dua cung stack Docker Compose len mot VPS/cloud server de the hien mo hinh cloud API.

## 1. Chuan bi VPS

- VPS Ubuntu 22.04/24.04, RAM toi thieu 1GB, khuyen nghi 2GB.
- Cai Docker Engine va Docker Compose plugin.
- Mo firewall cac port can dung:
  - 80 hoac 8080 neu demo HTTP.
  - 443 hoac 8443 neu demo HTTPS.
  - Khong mo port 8001 ra Internet neu khong can vi day la Kong Admin API.

## 2. Dua source len VPS

```bash
scp -r capstone_api_cloud_gateway user@YOUR_SERVER_IP:/home/user/
ssh user@YOUR_SERVER_IP
cd /home/user/capstone_api_cloud_gateway
```

## 3. Chay stack

```bash
docker compose up --build -d
```

## 4. Kiem tra

```bash
curl http://localhost:8080/health
curl -k https://localhost:8443/health
```

## 5. HTTPS production

Ban demo hien tai dung self-signed certificate trong thu muc `certs/` nen trinh duyet se canh bao.
Khi deploy that, nen dung domain that va Let's Encrypt/Certbot hoac Cloudflare Tunnel/Cloudflare SSL.

Kien truc production goi y:

```text
Internet -> HTTPS 443 -> Kong Gateway -> FastAPI internal -> PostgreSQL internal
```

Khong expose truc tiep FastAPI va PostgreSQL ra Internet.
