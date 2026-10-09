Class Fixture.Partido Extends %Persistent
{
    Property Codigo As %String [Required];
    Property Estado As %String [Required];

    Index idxCodigo On Codigo [Unique];

    Relationship Eventos As Fixture.Evento
        [Cardinality = children, Inverse = Partido];

    Method CambiarEstado(nuevo As %String) As %Boolean
    {
        If (..Estado = "Programado") && (nuevo = "Jugando") {
            Set ..Estado = nuevo
            Quit 1
        }

        If (..Estado = "Jugando") && (nuevo = "Finalizado") {
            Set ..Estado = nuevo
            Quit 1
        }

        Quit 0
    }
}


