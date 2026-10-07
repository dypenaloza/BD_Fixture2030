$tokenPath = Join-Path $PSScriptRoot "..\.influxdb3-token"
$token = (Get-Content $tokenPath -Raw).Trim()

# --------------------------------------------------
# VALIDACION DEL CONJUNTO PEQUENO - PARTIDO M001
# --------------------------------------------------

Write-Host "Validando cantidad de puntos de M001..."

$resultadoTotal = docker exec `
    -e "INFLUXDB3_AUTH_TOKEN=$token" `
    fixture2030-influxdb `
    influxdb3 query `
    --database fixture2030 `
    --format csv `
    "SELECT COUNT(*) AS total_puntos
     FROM estadisticas
     WHERE partido_id = 'M001'"

if ($LASTEXITCODE -ne 0) {
    Write-Error "No se pudo realizar la consulta de validacion."
    exit 1
}

$total = ($resultadoTotal | ConvertFrom-Csv).total_puntos

Write-Host "Puntos encontrados para M001: $total"

if ([int]$total -eq 8) {
    Write-Host "OK: se encontraron los 8 puntos esperados."
}
else {
    Write-Error "ERROR: se esperaban 8 puntos y se encontraron $total."
}

Write-Host ""
Write-Host "Validando distribucion por equipo en M001..."

$resultadoEquipos = docker exec `
    -e "INFLUXDB3_AUTH_TOKEN=$token" `
    fixture2030-influxdb `
    influxdb3 query `
    --database fixture2030 `
    --format csv `
    "SELECT equipo_id, COUNT(*) AS puntos
     FROM estadisticas
     WHERE partido_id = 'M001'
     GROUP BY equipo_id
     ORDER BY equipo_id"

$equipos = $resultadoEquipos | ConvertFrom-Csv

$equipos | Format-Table -AutoSize


# --------------------------------------------------
# VALIDACION DE PRUEBA DE VOLUMEN - PARTIDO M002
# --------------------------------------------------

Write-Host ""
Write-Host "Validando prueba de volumen M002..."

$resultadoVolumen = docker exec `
    -e "INFLUXDB3_AUTH_TOKEN=$token" `
    fixture2030-influxdb `
    influxdb3 query `
    --database fixture2030 `
    --format csv `
    "SELECT COUNT(*) AS total_puntos
     FROM estadisticas
     WHERE partido_id = 'M002'"

if ($LASTEXITCODE -ne 0) {
    Write-Error "No se pudo realizar la validacion de M002."
    exit 1
}

$totalVolumen = ($resultadoVolumen | ConvertFrom-Csv).total_puntos

Write-Host "Puntos encontrados para M002: $totalVolumen"

if ([int]$totalVolumen -eq 10000) {
    Write-Host "OK: se encontraron los 10000 puntos esperados."
}
else {
    Write-Error "ERROR: se esperaban 10000 puntos y se encontraron $totalVolumen."
}

Write-Host ""
Write-Host "Validando distribucion por equipo en M002..."

$resultadoEquiposVolumen = docker exec `
    -e "INFLUXDB3_AUTH_TOKEN=$token" `
    fixture2030-influxdb `
    influxdb3 query `
    --database fixture2030 `
    --format csv `
    "SELECT equipo_id, COUNT(*) AS puntos
     FROM estadisticas
     WHERE partido_id = 'M002'
     GROUP BY equipo_id
     ORDER BY equipo_id"

$equiposVolumen = $resultadoEquiposVolumen | ConvertFrom-Csv

$equiposVolumen | Format-Table -AutoSize