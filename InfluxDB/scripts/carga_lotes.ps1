param(
    [string]$Archivo = "puntos_fixture2030.lp",
    [int]$TamanoLote = 2000,
    [int]$Concurrencia = 2,
    [int]$MaxReintentos = 3
)

# =============================================================================
# Carga por lotes, con concurrencia y reintentos (ver
# docs/cardinalidad_y_escalabilidad.md: "para escalar se deben considerar
# tamaño de lote, concurrencia, manejo de errores, reintentos, validación
# de puntos cargados"). Reemplaza la versión anterior, que cargaba el
# archivo completo en una sola llamada a `influxdb3 write` y por lo tanto
# no implementaba ninguno de esos puntos a pesar de mencionarlos.
# =============================================================================

$tokenPath = Join-Path $PSScriptRoot "..\.influxdb3-token"
$token = (Get-Content $tokenPath -Raw).Trim()

$archivoLocal = Join-Path $PSScriptRoot $Archivo

if (-not (Test-Path $archivoLocal)) {
    Write-Error "No existe el archivo: $archivoLocal"
    exit 1
}

$lineas = Get-Content $archivoLocal
$totalPuntos = $lineas.Count

Write-Host "Archivo: $Archivo"
Write-Host "Puntos a cargar: $totalPuntos"
Write-Host "Tamano de lote: $TamanoLote | Concurrencia: $Concurrencia | Reintentos por lote: $MaxReintentos"

# -----------------------------------------------------------------------
# 1. Particionar en lotes
# -----------------------------------------------------------------------
$lotes = @()
for ($i = 0; $i -lt $lineas.Count; $i += $TamanoLote) {
    $fin = [Math]::Min($i + $TamanoLote, $lineas.Count) - 1
    $lotes += [PSCustomObject]@{
        Indice = $lotes.Count
        Lineas = $lineas[$i..$fin]
    }
}

Write-Host "Lotes generados: $($lotes.Count)"

$carpetaTemporal = Join-Path $PSScriptRoot "_lotes_tmp"
if (Test-Path $carpetaTemporal) {
    Remove-Item -Recurse -Force $carpetaTemporal
}
New-Item -ItemType Directory -Path $carpetaTemporal | Out-Null

foreach ($lote in $lotes) {
    $rutaLote = Join-Path $carpetaTemporal "lote_$($lote.Indice).lp"
    [System.IO.File]::WriteAllText(
        $rutaLote,
        (($lote.Lineas -join "`n") + "`n"),
        [System.Text.UTF8Encoding]::new($false)
    )
}

# -----------------------------------------------------------------------
# 2. Validación de puntos cargados: se cuenta el total ANTES de cargar,
#    para poder comparar el delta real contra lo que se intentó cargar.
# -----------------------------------------------------------------------
function Contar-PuntosTotales {
    param($tokenActual)

    $resultado = docker exec `
        -e "INFLUXDB3_AUTH_TOKEN=$tokenActual" `
        fixture2030-influxdb `
        influxdb3 query `
        --database fixture2030 `
        --format csv `
        "SELECT COUNT(*) AS total FROM estadisticas"

    if ($LASTEXITCODE -ne 0) {
        return -1
    }
    return [int](($resultado | ConvertFrom-Csv).total)
}

$totalAntes = Contar-PuntosTotales -tokenActual $token
if ($totalAntes -lt 0) {
    Write-Error "No se pudo contar el estado inicial de la tabla antes de cargar."
    Remove-Item -Recurse -Force $carpetaTemporal
    exit 1
}
Write-Host "Puntos existentes antes de la carga: $totalAntes"

# -----------------------------------------------------------------------
# 3. Carga concurrente por lotes, con reintentos y backoff por lote
# -----------------------------------------------------------------------
$cronometro = [System.Diagnostics.Stopwatch]::StartNew()

$scriptBlockLote = {
    param($nombreLote, $tokenJob, $maxReintentosJob)

    $intento = 0
    $exito = $false

    while (-not $exito -and $intento -lt $maxReintentosJob) {
        $intento++
        docker exec `
            -e "INFLUXDB3_AUTH_TOKEN=$tokenJob" `
            fixture2030-influxdb `
            influxdb3 write `
            --database fixture2030 `
            --file "/scripts/_lotes_tmp/$nombreLote" `
            --precision s
        if ($LASTEXITCODE -eq 0) {
            $exito = $true
        }
        elseif ($intento -lt $maxReintentosJob) {
            Start-Sleep -Seconds ([Math]::Pow(2, $intento))
        }
    }

    [PSCustomObject]@{
        Lote     = $nombreLote
        Exito    = $exito
        Intentos = $intento
    }
}

$pendientes = [System.Collections.Generic.Queue[object]]::new()
foreach ($lote in $lotes) {
    $pendientes.Enqueue("lote_$($lote.Indice).lp")
}

$trabajos = @()
$resultados = @()

while ($pendientes.Count -gt 0 -or $trabajos.Count -gt 0) {

    while ($trabajos.Count -lt $Concurrencia -and $pendientes.Count -gt 0) {
        $nombreLote = $pendientes.Dequeue()
        $trabajos += Start-Job -ScriptBlock $scriptBlockLote -ArgumentList $nombreLote, $token, $MaxReintentos
    }

    Start-Sleep -Milliseconds 300
    $terminados = @($trabajos | Where-Object { $_.State -ne 'Running' })

    foreach ($trabajo in $terminados) {
        $resultados += Receive-Job -Job $trabajo
        Remove-Job -Job $trabajo
    }

    $trabajos = @($trabajos | Where-Object { $_.State -eq 'Running' })
}

$cronometro.Stop()

# -----------------------------------------------------------------------
# 4. Reporte por lote y validación final
# -----------------------------------------------------------------------
$fallidos = @($resultados | Where-Object { -not $_.Exito })

Write-Host ""
Write-Host "Resultado por lote:"
foreach ($r in ($resultados | Sort-Object { [int]($_.Lote -replace '[^\d]', '') })) {
    $estado = if ($r.Exito) { "OK" } else { "FALLO" }
    Write-Host "  $($r.Lote): $estado (intentos: $($r.Intentos))"
}

if ($fallidos.Count -gt 0) {
    Write-Error "$($fallidos.Count) de $($lotes.Count) lotes fallaron despues de $MaxReintentos reintentos cada uno."
    Remove-Item -Recurse -Force $carpetaTemporal
    exit 1
}

$totalDespues = Contar-PuntosTotales -tokenActual $token
$delta = $totalDespues - $totalAntes

Write-Host ""
Write-Host "Puntos existentes despues de la carga: $totalDespues"
Write-Host "Delta observado: $delta (puntos intentados: $totalPuntos)"
Write-Host "Tiempo total: $($cronometro.Elapsed.TotalSeconds) segundos"

Remove-Item -Recurse -Force $carpetaTemporal

if ($delta -ne $totalPuntos) {
    Write-Error "Validacion de puntos cargados fallida: se intentaron cargar $totalPuntos puntos pero el conteo de la tabla solo aumento en $delta. Puede deberse a puntos duplicados (misma serie y mismo timestamp, que InfluxDB sobrescribe en vez de duplicar) o a una perdida real de datos: revisar antes de dar la carga por valida."
    exit 1
}

Write-Host ""
Write-Host "Carga finalizada y validada correctamente: todos los lotes se escribieron y el conteo aumento exactamente lo esperado."
