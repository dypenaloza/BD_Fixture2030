# =============================================================================
# Hito 5 — Fixture 2030 | Carga completa del subgrafo (Windows / PowerShell)
#
# Ejecuta, en orden: estructura -> carga -> verificación.
# Es idempotente: puede correrse tantas veces como se quiera.
#
# Uso, desde la raíz del módulo (fixture2030-neo4j):
#     .\scripts\cargar.ps1
#     .\scripts\cargar.ps1 -Regenerar     # regenera los CSV antes de cargar
# =============================================================================
param(
    [switch]$Regenerar
)

$ErrorActionPreference = "Stop"

# Ubicarse en la raíz del módulo, sin importar desde dónde se invoque.
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz

# --- Credenciales: se leen de .env, nunca están escritas en el script --------
$usuario = "neo4j"
$clave = "fixture2030"
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*NEO4J_USER\s*=\s*(.+)\s*$')     { $usuario = $Matches[1].Trim() }
        if ($_ -match '^\s*NEO4J_PASSWORD\s*=\s*(.+)\s*$') { $clave  = $Matches[1].Trim() }
    }
} else {
    Write-Host "AVISO: no existe .env; se usan los valores por defecto del compose." -ForegroundColor Yellow
}

function Invoke-Cypher([string]$archivo) {
    Write-Host ""
    Write-Host "==> $archivo" -ForegroundColor Cyan
    docker compose exec -T neo4j cypher-shell -u $usuario -p $clave --format plain -f "/queries/$archivo"
    if ($LASTEXITCODE -ne 0) { throw "Fallo al ejecutar $archivo" }
}

# --- 0. Dataset ---------------------------------------------------------------
if ($Regenerar) {
    Write-Host "==> Regenerando los CSV desde los datos del Hito 4" -ForegroundColor Cyan
    python import\generar_dataset.py
    if ($LASTEXITCODE -ne 0) { throw "Fallo la generacion del dataset" }
}

# --- 1. Ambiente --------------------------------------------------------------
Write-Host "==> Levantando el servicio Neo4j" -ForegroundColor Cyan
docker compose up -d

Write-Host "==> Esperando a que Neo4j acepte consultas" -ForegroundColor Cyan
$listo = $false
foreach ($intento in 1..30) {
    $estado = docker inspect --format '{{.State.Health.Status}}' fixture2030-neo4j 2>$null
    if ($estado -eq "healthy") { $listo = $true; break }
    Start-Sleep -Seconds 5
}
if (-not $listo) {
    throw "Neo4j no quedo disponible. Revisar: docker compose logs neo4j"
}
Write-Host "    Neo4j disponible en http://localhost:7474" -ForegroundColor Green

# --- 2. Estructura, carga y verificación --------------------------------------
Invoke-Cypher "estructura.cypher"
Invoke-Cypher "carga.cypher"
Invoke-Cypher "verificacion.cypher"

Write-Host ""
Write-Host "Carga completa. Neo4j Browser: http://localhost:7474 (usuario: $usuario)" -ForegroundColor Green
