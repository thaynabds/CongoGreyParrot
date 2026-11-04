package org.congogreyparrot.text

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ResumoTest {
    private val reuniao = """
        Ana: Bom dia a todos. Hoje vamos revisar o cronograma do projeto do aplicativo.
        Bruno: O cronograma do aplicativo atrasou duas semanas por causa da integração com o servidor.
        Ana: Ficou decidido que a integração com o servidor terá prioridade nesta semana.
        Carla: Eu vou preparar o relatório de testes do aplicativo até sexta.
        Bruno: Quem vai falar com o cliente sobre o novo prazo?
        Ana: Combinamos de apresentar o cronograma novo ao cliente na segunda.
    """.trimIndent()

    @Test
    fun frasesVemDoProprioTexto() {
        val resumo = Resumo.resumir(reuniao)
        assertTrue(resumo.frases.isNotEmpty())
        resumo.frases.forEach { frase -> assertTrue(frase, reuniao.contains(frase.substringAfter(": "))) }
    }

    @Test
    fun separaDecisoesTarefasEPerguntas() {
        val resumo = Resumo.resumir(reuniao)
        assertTrue(resumo.decisoes.any { it.startsWith("Ana: Ficou decidido") })
        assertTrue(resumo.tarefas.any { it.startsWith("Carla: Eu vou preparar") })
        assertTrue(resumo.perguntas.any { it.startsWith("Bruno: Quem vai falar") })
    }

    @Test
    fun textoVazioETextoGigante() {
        assertEquals("Não há texto para resumir.", Resumo.texto(Resumo.resumir("   ")))
        val grande = Resumo.resumir("palavra repetida aqui. ".repeat(30_000))
        assertTrue(grande.cortado)
        assertTrue(grande.frases.size <= 30)
    }
}
