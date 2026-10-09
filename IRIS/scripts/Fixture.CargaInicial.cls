Class Fixture.CargaInicial Extends %RegisteredObject
{
    ClassMethod Ejecutar()
    {
        Write "=== CARGA INICIAL FIXTURE 2030 ===",!

        Set partido = ##class(Fixture.Partido).%New()
        Set partido.Codigo = "M004"
        Set partido.Estado = "Programado"

        Set evento = ##class(Fixture.Evento).%New()
        Set evento.Tipo = "Gol"
        Set evento.Minuto = 15

        Do partido.Eventos.Insert(evento)

        Set sc = partido.%Save()

        If '$System.Status.IsOK(sc) {
            Do $System.Status.DisplayError(sc)
            Quit
        }

        Write "Partido guardado: ",partido.%Id(),!
        Write "Evento guardado: ",evento.%Id(),!
        Write "Carga finalizada correctamente",!
    }
}