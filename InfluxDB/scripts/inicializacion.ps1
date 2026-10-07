# Ajuste local para PowerShell en Windows
if (-not $env:HOME) {
    $env:HOME = $env:USERPROFILE
}

# Crear carpeta de persistencia si no existe
$persistencia = Join-Path $env:HOME "docker\data\influxdb"

if (-not (Test-Path $persistencia)) {
    New-Item -ItemType Directory -Force $persistencia | Out-Null
    Write-Host "Carpeta de persistencia creada:"
    Write-Host $persistencia
}

Write-Host ""
Write-Host "Iniciando InfluxDB..."

docker compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Error "No se pudo iniciar InfluxDB."
    exit 1
}

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "Estado del contenedor:"
docker compose ps

Write-Host ""
Write-Host "Version de InfluxDB:"
docker exec fixture2030-influxdb influxdb3 --version

if ($LASTEXITCODE -ne 0) {
    Write-Error "InfluxDB no responde correctamente."
    exit 1
}

Write-Host ""
Write-Host "OK: ambiente InfluxDB iniciado correctamente."