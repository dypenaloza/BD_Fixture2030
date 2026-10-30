param(
    [ValidateSet("linea_base_refuerzo", "optimizada_refuerzo")]
    [string]$Tipo
)

$raiz = (Resolve-Path "$PSScriptRoot\..\..").Path
$evidencia = Join-Path $raiz "Hito12\docs\evidencia"

$archivo = Join-Path $evidencia "recursos_$Tipo.csv"

# Guardar una copia de las mediciones anteriores
foreach ($extension in @("csv", "json")) {
    $original = Join-Path $evidencia "$Tipo.$extension"

    if (Test-Path $original) {
        Copy-Item $original (
            Join-Path $evidencia "${Tipo}_previo.$extension"
        ) -Force
    }
}

# Crear archivo de monitoreo
"fecha;cpu_mongodb;memoria_mongodb" |
    Set-Content $archivo

# Monitorear MongoDB cada 2 segundos
$trabajo = Start-Job -ArgumentList $archivo -ScriptBlock {
    param($ruta)

    while ($true) {
        $datos = docker stats --no-stream `
            --format "{{.CPUPerc}};{{.MemUsage}}" `
            fixture2030-mongodb 2>$null

        if ($datos) {
            "$(Get-Date -Format o);$datos" |
                Add-Content $ruta
        }

        Start-Sleep -Seconds 2
    }
}

try {
    # Ejecutar prueba de carga
    & "$raiz\API_REST\.venv311\Scripts\python.exe" `
      "$raiz\Hito12\scripts\ejecutar_carga.py" $Tipo
}
finally {
    Stop-Job $trabajo
    Remove-Job $trabajo
}

Write-Host "Monitoreo guardado en: $archivo"