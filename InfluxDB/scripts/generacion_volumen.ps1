$salida = Join-Path $PSScriptRoot "puntos_volumen.lp"

$puntos = New-Object System.Collections.Generic.List[string]

$timestampInicial = 1917680000

for ($i = 0; $i -lt 5000; $i++) {

    $timestamp = $timestampInicial + $i

    $posesionArg = 50 + ($i % 10)
    $posesionPor = 100 - $posesionArg

    $pasesArg = 200 + $i
    $pasesPor = 180 + $i

    $tirosArg = $i % 2
    $tirosPor = ($i + 1) % 2

    $puntos.Add(
        "estadisticas,partido_id=M002,equipo_id=ARG posesion_pct=$posesionArg,pases=${pasesArg}i,tiros=${tirosArg}i $timestamp"
    )

    $puntos.Add(
        "estadisticas,partido_id=M002,equipo_id=POR posesion_pct=$posesionPor,pases=${pasesPor}i,tiros=${tirosPor}i $timestamp"
    )
}

$contenido = ($puntos -join "`n") + "`n"

[System.IO.File]::WriteAllText(
    $salida,
    $contenido,
    [System.Text.UTF8Encoding]::new($false)
)

Write-Host "Generados $($puntos.Count) puntos."
Write-Host "Archivo: $salida"