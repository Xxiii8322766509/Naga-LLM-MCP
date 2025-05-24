# 一键配置脚本 for NagaAgent 2.0 (极致码高尔夫)
$ErrorActionPreference = "Stop" # 设置错误时停止执行
$modelPath = "models/text2vec-base-chinese" # 模型路径
$modelRepo = "shibing624/text2vec-base-chinese" # 模型仓库名
$pythonMinVersion = "3.8" # Python最低版本要求
$venvPath = ".venv" # 虚拟环境路径

# 检查Python版本
$pythonVersion = (python --version 2>&1) -replace "Python "
if ([version]$pythonVersion -lt [version]$pythonMinVersion) {
    Write-Error "需要Python $pythonMinVersion或更高版本，当前版本: $pythonVersion"
    exit 1
}

# 设置工作目录
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# 创建并激活虚拟环境
if (-not (Test-Path $venvPath)) {
    Write-Host "创建虚拟环境..."
    python -m venv $venvPath
}

# 激活虚拟环境
. "$venvPath/Scripts/Activate.ps1"

# 安装依赖（用清华源加速）
Write-Host "安装依赖（使用清华镜像源加速）..."
Get-ChildItem -Filter "requirements*.txt" | ForEach-Object {
    pip install -r $_.FullName -i https://pypi.tuna.tsinghua.edu.cn/simple
}

# 安装playwright浏览器驱动
Write-Host "安装playwright浏览器驱动..."
python -m playwright install chromium

# 验证playwright安装
Write-Host "验证playwright安装..."
$playwrightVersion = python -m playwright --version
if ($LASTEXITCODE -ne 0) {
    Write-Error "Playwright安装验证失败"
    exit 1
}
Write-Host "Playwright版本: $playwrightVersion"

# 检查并下载模型
if (-not (Test-Path $modelPath)) {
    Write-Host "下载模型中..."
    python -c "from huggingface_hub import snapshot_download; snapshot_download('$modelRepo', local_dir='$modelPath')"
}

Write-Host "环境设置完成！"
Write-Host "如需安装其他浏览器驱动，请运行:"
Write-Host "python -m playwright install firefox  # 安装Firefox"
Write-Host "python -m playwright install webkit   # 安装WebKit" 
