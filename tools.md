
根據項目分析，我為您整理了C2 Django AI項目中需要安裝的Go工具和Docker鏡像命令：

## 🐳 Docker鏡像安裝命令

### 安全掃描工具
```bash
# 子域名發現工具
docker pull projectdiscovery/subfinder:latest

# URL發現工具 (GetAllUrls)
docker pull sxcurity/gau:latest

# 子域名枚舉工具
```

## 🛠 Go工具安裝命令

### Project Discovery工具集
```bash
# 子域名發現工具
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

# DNS解析工具
go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest

```bash
# CDN檢測工具
go install -v github.com/projectdiscovery/cdncheck/cmd/cdncheck@latest
```

### 其他安全工具
```bash
# 技術棧檢測工具
# 端口掃描工具 (Python包，但有Go實現)
pip install python-nmap
# 或系統安裝
sudo apt install nmap
```

## 📦 批量安裝腳本

### 創建Go工具安裝腳本
```bash
cat > install_go_tools.sh << 'EOF'
#!/bin/bash
echo "安裝Go安全工具..."

# 確保Go已安裝
if ! command -v go &> /dev/null; then
    echo "請先安裝Go語言環境"
    exit 1
fi

# 創建Go工具目錄
mkdir -p ~/go/bin
export PATH=$PATH:~/go/bin

# 安裝Project Discovery工具
echo "安裝Project Discovery工具..."
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest
go install -v github.com/projectdiscovery/cdncheck/cmd/cdncheck@latest

# 安裝其他工具
echo "安裝其他安全工具..."
go install -v github.com/Edu4rdSHL/wafw00f@latest

echo "Go工具安裝完成！"
echo "請將以下行添加到您的 ~/.bashrc 或 ~/.zshrc："
echo "export PATH=\$PATH:~/go/bin"
EOF

chmod +x install_go_tools.sh
./install_go_tools.sh
```

### 批量Docker鏡像下載
```bash
cat > pull_docker_images.sh << 'EOF'
#!/bin/bash
echo "批量下載Docker鏡像..."

# 安全掃描工具
docker pull projectdiscovery/subfinder:latest
docker pull sxcurity/gau:latest
docker pull caffix/amass:latest

# 系統服務
docker pull postgres:14-bullseye
docker pull redis:8.0
docker pull hasura/graphql-engine:v2.36.0
docker pull nocodb/nocodb:latest

# 代理和繞過工具
docker pull ghcr.io/flaresolverr/flaresolverr:latest
docker pull ghcr.io/kljensen/flareproxygo:latest
docker pull k3scat/nya-proxy:0.4.6

echo "所有Docker鏡像下載完成！"
EOF

chmod +x pull_docker_images.sh
./pull_docker_images.sh
```

## 🔧 系統依賴安裝

### Ubuntu/Debian系統包
```bash
sudo apt update
sudo apt install -y \
    python3-dev python3-pip python3-venv \
    build-essential \
    docker.io \
    libssl-dev libffi-dev \
    libxml2-dev libxslt1-dev \
    zlib1g-dev libjpeg-dev libpng-dev \
    libmagic1 libmagic-dev \
    nmap masscan \
    git curl wget \
    postgresql-client mysql-client sqlite3 \
    libpq-dev libmysqlclient-dev libsqlite3-dev \
    golang-go
```

## 🚀 一鍵安裝所有依賴

```bash
# 創建完整安裝腳本
cat > full_install.sh << 'EOF'
#!/bin/bash
echo "=== C2 Django AI 完整安裝腳本 ==="

# 1. 安裝系統依賴
echo "1. 安裝系統依賴..."
sudo apt update
sudo apt install -y \
    python3-dev python3-pip python3-venv \
    build-essential docker.io \
    libssl-dev libffi-dev \
    libxml2-dev libxslt1-dev \
    zlib1g-dev libjpeg-dev libpng-dev \
    libmagic1 libmagic-dev \
    nmap masscan git curl wget \
    postgresql-client mysql-client sqlite3 \
    libpq-dev libmysqlclient-dev libsqlite3-dev \
    golang-go

# 2. 安裝Go工具
echo "2. 安裝Go工具..."
export PATH=$PATH:~/go/bin
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest
go install -v github.com/projectdiscovery/cdncheck/cmd/cdncheck@latest
go install -v github.com/Edu4rdSHL/wafw00f@latest

# 3. 下載Docker鏡像
echo "3. 下載Docker鏡像..."
docker pull projectdiscovery/subfinder:latest
docker pull sxcurity/gau:latest
docker pull caffix/amass:latest
docker pull postgres:14-bullseye
docker pull redis:8.0
docker pull hasura/graphql-engine:v2.36.0
docker pull nocodb/nocodb:latest
docker pull ghcr.io/flaresolverr/flaresolverr:latest
docker pull ghcr.io/kljensen/flareproxygo:latest
docker pull k3scat/nya-proxy:0.4.6

echo "=== 安裝完成！==="
echo "請記得將以下行添加到您的shell配置中："
echo "export PATH=\$PATH:~/go/bin"
EOF

chmod +x full_install.sh
sudo ./full_install.sh
```

