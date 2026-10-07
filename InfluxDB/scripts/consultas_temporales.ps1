$tokenPath = Join-Path $PSScriptRoot "..\.influxdb3-token"
$token = (Get-Content $tokenPath -Raw).Trim()

Write-Host "Consulta 1 - Evolucion de Argentina en el partido M001"
Write-Host ""

docker exec `
    -e "INFLUXDB3_AUTH_TOKEN=$token" `
    fixture2030-influxdb `
    influxdb3 query `
    --database fixture2030 `
    "SELECT time, equipo_id, posesion_pct, pases, tiros
     FROM estadisticas
     WHERE partido_id = 'M001'
       AND equipo_id = 'ARG'
     ORDER BY time"

Write-Host ""
Write-Host "Consulta 2 - Comparacion entre los equipos del partido M001"
Write-Host ""

docker exec `
    -e "INFLUXDB3_AUTH_TOKEN=$token" `
    fixture2030-influxdb `
    influxdb3 query `
    --database fixture2030 `
    "SELECT time, equipo_id, posesion_pct, pases, tiros
     FROM estadisticas
     WHERE partido_id = 'M001'
     ORDER BY time, equipo_id"

Write-Host ""
Write-Host "Consulta 3 - Ventana temporal de Argentina en M001"
Write-Host ""

docker exec `
    -e "INFLUXDB3_AUTH_TOKEN=$token" `
    fixture2030-influxdb `
    influxdb3 query `
    --database fixture2030 `
    "SELECT time, equipo_id, posesion_pct, pases, tiros
     FROM estadisticas
     WHERE partido_id = 'M001'
       AND equipo_id = 'ARG'
       AND time >= '2030-10-08T08:00:01Z'
       AND time <= '2030-10-08T08:00:02Z'
     ORDER BY time"