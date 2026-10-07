$tokenPath = Join-Path $PSScriptRoot "..\.influxdb3-token"

# Si el token ya existe, no generar otro
if (Test-Path $tokenPath) {
    Write-Host "OK: ya existe un token local de InfluxDB."
    Write-Host "No se genera uno nuevo."
    exit 0
}

Write-Host "No se encontro un token local."
Write-Host "Generando token administrador..."

$resultado = docker exec `
    fixture2030-influxdb `
    influxdb3 create token --admin --format text

if ($LASTEXITCODE -ne 0) {
    Write-Error "No se pudo crear el token administrador."
    exit 1
}

$token = ($resultado | Out-String).Trim()

if ([string]::IsNullOrWhiteSpace($token)) {
    Write-Error "InfluxDB no devolvio un token."
    exit 1
}

[System.IO.File]::WriteAllText(
    $tokenPath,
    $token,
    [System.Text.UTF8Encoding]::new($false)
)

Write-Host "OK: token creado y guardado localmente."
Write-Host "Archivo: .influxdb3-token"
Write-Host "El token no se muestra por seguridad."