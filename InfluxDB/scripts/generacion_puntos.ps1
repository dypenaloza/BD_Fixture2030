$salida = Join-Path $PSScriptRoot "puntos_fixture2030.lp"

$puntos = @(
    "estadisticas,partido_id=M001,equipo_id=ARG posesion_pct=55.0,pases=100i,tiros=1i 1917676800",
    "estadisticas,partido_id=M001,equipo_id=POR posesion_pct=45.0,pases=90i,tiros=0i 1917676800",

    "estadisticas,partido_id=M001,equipo_id=ARG posesion_pct=56.0,pases=105i,tiros=0i 1917676801",
    "estadisticas,partido_id=M001,equipo_id=POR posesion_pct=44.0,pases=94i,tiros=1i 1917676801",

    "estadisticas,partido_id=M001,equipo_id=ARG posesion_pct=58.0,pases=110i,tiros=1i 1917676802",
    "estadisticas,partido_id=M001,equipo_id=POR posesion_pct=42.0,pases=98i,tiros=0i 1917676802",

    "estadisticas,partido_id=M001,equipo_id=ARG posesion_pct=57.0,pases=115i,tiros=0i 1917676803",
    "estadisticas,partido_id=M001,equipo_id=POR posesion_pct=43.0,pases=103i,tiros=1i 1917676803"
)

$contenido = ($puntos -join "`n") + "`n"

[System.IO.File]::WriteAllText(
    $salida,
    $contenido,
    [System.Text.UTF8Encoding]::new($false)
)

Write-Host "Generados $($puntos.Count) puntos en:"
Write-Host $salida