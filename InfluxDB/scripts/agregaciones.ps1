$tokenPath = Join-Path $PSScriptRoot "..\.influxdb3-token"
$token = (Get-Content $tokenPath -Raw).Trim()

Write-Host "Agregaciones del partido M001"
Write-Host ""

docker exec `
    -e "INFLUXDB3_AUTH_TOKEN=$token" `
    fixture2030-influxdb `
    influxdb3 query `
    --database fixture2030 `
    "SELECT equipo_id,
            AVG(posesion_pct) AS posesion_promedio,
            SUM(tiros) AS tiros_totales,
            MAX(pases) - MIN(pases) AS pases_nuevos
     FROM estadisticas
     WHERE partido_id = 'M001'
     GROUP BY equipo_id
     ORDER BY equipo_id"