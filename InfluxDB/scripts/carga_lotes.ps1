param(
    [string]$Archivo = "puntos_fixture2030.lp"
)

$tokenPath = Join-Path $PSScriptRoot "..\.influxdb3-token"
$token = (Get-Content $tokenPath -Raw).Trim()

$archivoLocal = Join-Path $PSScriptRoot $Archivo

if (-not (Test-Path $archivoLocal)) {
    Write-Error "No existe el archivo: $archivoLocal"
    exit 1
}

$cantidadPuntos = (Get-Content $archivoLocal).Count

Write-Host "Archivo: $Archivo"
Write-Host "Puntos a cargar: $cantidadPuntos"
Write-Host "Iniciando carga..."

$cronometro = [System.Diagnostics.Stopwatch]::StartNew()

docker exec `
    -e "INFLUXDB3_AUTH_TOKEN=$token" `
    fixture2030-influxdb `
    influxdb3 write `
    --database fixture2030 `
    --file "/scripts/$Archivo" `
    --precision s

$codigoSalida = $LASTEXITCODE
$cronometro.Stop()

if ($codigoSalida -eq 0) {
    Write-Host ""
    Write-Host "Carga finalizada correctamente."
    Write-Host "Puntos procesados: $cantidadPuntos"
    Write-Host "Tiempo observado: $($cronometro.Elapsed.TotalSeconds) segundos"
}
else {
    Write-Error "La carga de puntos fallo."
    exit 1
}