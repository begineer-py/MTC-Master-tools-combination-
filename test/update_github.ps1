# 設置 PowerShell 環境為 UTF-8，確保輸出正常顯示
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 確保 PowerShell 使用 UTF-8 編碼
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'

# 提示用户输入提交信息
$commitMessage = Read-Host "请输入提交信息"

# 檢查提交信息是否为空
if (-not $commitMessage) {
    Write-Warning "提交信息不能为空，脚本终止。"
    exit
}

# 确保仓库目录存在
$repoPath = "C:\Users\User.DESKTOP-AQD9BKJ\Desktop\C2"
if (!(Test-Path $repoPath)) {
    Write-Error "错误: 仓库目录 $repoPath 不存在！"
    exit
}

# 切换到仓库根目录
Set-Location -Path $repoPath

# 确保 Git 不会显示中文路径乱码
git config --global core.quotepath false

# 添加所有更改
Write-Host "正在添加更改..." -ForegroundColor Green
git add .

# 使用提供的提交信息提交更改
Write-Host "正在提交更改，提交信息为: '$commitMessage'" -ForegroundColor Green
git commit -m $commitMessage

# 推送更改到远程仓库
Write-Host "正在推送更改..." -ForegroundColor Green
git push origin main

# 检查 Git 状态
Write-Host "正在检查 Git 状态..." -ForegroundColor Green
git status

Write-Host "脚本执行完毕。" -ForegroundColor Green
