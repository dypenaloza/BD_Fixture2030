# Hito 10 - Pruebas de integración
# Fixture Mundial 2030

$baseUrl = "http://127.0.0.1:8000"

$pruebas = @(

    # MongoDB
    @{
        Nombre = "MongoDB - Seleccion existente"
        Ruta = "/selecciones/ARG"
        Esperado = 200
    },

    # Neo4j
    @{
        Nombre = "Neo4j - Eventos de partido"
        Ruta = "/partidos/P001/eventos?limit=20"
        Esperado = 200
    },

    # Cassandra
    @{
        Nombre = "Cassandra - Comentarios"
        Ruta = "/partidos/M001/comentarios?bucket_temporal=20%3A00-20%3A05&limit=5"
        Esperado = 200
    },

    # Redis
    @{
        Nombre = "Redis - Sesion activa"
        Ruta = "/sesiones/U99998"
        Esperado = 200
    },

    # InfluxDB
    @{
        Nombre = "InfluxDB - Estadisticas"
        Ruta = "/partidos/M001/estadisticas?equipo_id=ARG&desde=2030-10-08T08%3A00%3A00Z&hasta=2030-10-08T08%3A00%3A05Z&limit=20"
        Esperado = 200
    },

    # IRIS
    @{
        Nombre = "IRIS - Partido existente"
        Ruta = "/partidos/M004/detalle"
        Esperado = 200
    },

    # Validaciones
    @{
        Nombre = "MongoDB - Codigo invalido"
        Ruta = "/selecciones/12"
        Esperado = 400
    },

    @{
        Nombre = "Neo4j - Partido invalido"
        Ruta = "/partidos/ABCDEF/eventos"
        Esperado = 400
    },

    @{
        Nombre = "Cassandra - Limite invalido"
        Ruta = "/partidos/M001/comentarios?bucket_temporal=20%3A00-20%3A05&limit=500"
        Esperado = 400
    },

    @{
        Nombre = "Redis - Sesion inexistente"
        Ruta = "/sesiones/U00000"
        Esperado = 404
    },

    @{
        Nombre = "InfluxDB - Intervalo invalido"
        Ruta = "/partidos/M001/estadisticas?equipo_id=ARG&desde=2030-10-08T09%3A00%3A00Z&hasta=2030-10-08T08%3A00%3A00Z"
        Esperado = 400
    },

    @{
        Nombre = "IRIS - Partido inexistente"
        Ruta = "/partidos/M999/detalle"
        Esperado = 404
    }

)

$correctas = 0
$incorrectas = 0

$archivoTemporal = Join-Path $env:TEMP "fixture2030_respuesta.json"

Write-Output "=================================="
Write-Output "PRUEBAS API REST - FIXTURE 2030"
Write-Output "=================================="

try {

    foreach ($prueba in $pruebas) {

        $url = "$baseUrl$($prueba.Ruta)"

        $codigo = & curl.exe `
            --silent `
            --show-error `
            --max-time 20 `
            --output $archivoTemporal `
            --write-out "%{http_code}" `
            "$url"

        if (
            $LASTEXITCODE -eq 0 -and
            $codigo -eq [string]$prueba.Esperado
        ) {

            Write-Output "[OK] $($prueba.Nombre) - HTTP $codigo"

            $correctas++

        } else {

            Write-Output "[ERROR] $($prueba.Nombre)"
            Write-Output "Esperado: $($prueba.Esperado)"
            Write-Output "Obtenido: $codigo"

            $incorrectas++

        }
    }

} finally {

    Remove-Item $archivoTemporal -ErrorAction SilentlyContinue

}

Write-Output ""
Write-Output "=================================="
Write-Output "RESULTADOS"
Write-Output "=================================="

Write-Output "Correctas: $correctas"
Write-Output "Incorrectas: $incorrectas"
Write-Output "Total: $($pruebas.Count)"

if ($incorrectas -gt 0) {
    throw "Hay pruebas pendientes de corregir."
}