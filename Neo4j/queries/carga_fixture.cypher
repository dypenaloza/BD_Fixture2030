// =============================================================================
// NOTA: este archivo contenía un único partido/estadio/evento de prueba
// (P001, E001, EV001) creado a mano durante la exploración inicial del
// modelo — cruzaba selecciones de grupos distintos (ARG vs BRA) y no
// representaba una fase de grupos coherente.
//
// La carga real y reproducible del fixture (16 sedes, 128 partidos —fase de
// grupos + eliminatorias—, 591 eventos con sus relaciones SE_JUEGA_EN,
// PARTICIPA_EN, OCURRE_EN y PROTAGONIZADO_POR) se hace con:
//
//     python scripts/generar_fixture.py
//
// Es reproducible (semilla fija SEED=2030 en el script) e idempotente
// (MERGE en toda la carga, ver RNF4). Al ejecutarse elimina además el
// partido y el evento de prueba de este archivo (P001/EV001) si todavía
// existieran en la base, para no dejar datos inconsistentes mezclados con
// el fixture generado. Este archivo se conserva sólo como referencia
// histórica del primer boceto del modelo.
// =============================================================================
