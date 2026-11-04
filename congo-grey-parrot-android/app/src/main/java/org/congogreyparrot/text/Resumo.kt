package org.congogreyparrot.text

import kotlin.math.max
import kotlin.math.min
import kotlin.math.roundToInt
import kotlin.math.sqrt

/**
 * Resumo local, sem IA e sem internet. Escolhe frases do próprio texto e separa
 * decisões, tarefas e perguntas. Mesma regra do resumo.py dos programas em Python.
 */
data class ResumoResult(
    val frases: List<String>,
    val decisoes: List<String>,
    val tarefas: List<String>,
    val perguntas: List<String>,
    val palavras: List<String>,
    val total: Int,
    val cortado: Boolean,
)

object Resumo {
    const val MAX_CHARS = 400_000
    private const val MAX_SENTENCES = 30
    private const val MAX_SENTENCE_CHARS = 600
    private const val MAX_ITEMS = 6

    private val split = Regex("(?<=[.!?…])\\s+|\\n+")
    private val word = Regex("[\\p{L}]{3,}")
    private val speaker = Regex("^(?:\\[[^\\]\\n]{1,20}\\]\\s*)?([^:\\n]{1,60}):\\s+(\\S.*)$")

    private val stopwords = """
        que não uma para com por mais como mas foi são ser tem você vocês ele ela eles elas isso isto esse essa
        este esta aqui ali então também muito muita já quando onde porque pra pro dos das nos nas num numa
        está estão estava era eram ter tinha vai vou vamos sim seu sua seus suas meu minha nosso nossa
        pelo pela pelos pelas sobre entre até depois antes ainda só sem tudo nada cada qual quem lhe
        gente coisa acho assim aí né tá aquele aquela the and that this with for are was were have has had
        you your they them their there here what when where which who will would could should about from
        into just also been being not but our out can all any some than then its it's i'm don't yes okay
        del los las por con para una uno unos unas como pero más este esta esto ese esa eso aquí allí
        también muy ya cuando donde porque sí sus mis nuestro nuestra está están era fue ser hay tiene
        vamos todo nada cada quien entonces bueno
    """.trim().split(Regex("\\s+")).toSet()

    private val decision = Regex(
        "\\b(decidi(?:mos|do|da|u)|ficou (?:decidido|definido|combinado)|combina(?:mos|do)|aprova(?:mos|do|da)|" +
            "fica definido|fechamos|decided|agreed|we will go with|approved|acordamos|queda (?:decidido|acordado)|" +
            "aprobado)\\b",
        RegexOption.IGNORE_CASE,
    )
    private val task = Regex(
        "\\b(vou (?:fazer|mandar|enviar|ver|criar|preparar|revisar|ligar)|fica com|responsável|prazo|" +
            "até (?:amanhã|segunda|terça|quarta|quinta|sexta|sábado|domingo|o dia|dia)|preciso que|pode (?:fazer|mandar|enviar)|" +
            "tarefa|próximos passos|i'll|i will|will send|action item|deadline|next steps|by (?:monday|tuesday|wednesday|" +
            "thursday|friday|tomorrow)|voy a|me encargo|plazo|hasta el|próximos pasos)\\b",
        RegexOption.IGNORE_CASE,
    )

    fun resumir(texto: String, frases: Int = 0): ResumoResult {
        val cortado = texto.length > MAX_CHARS
        val pares = texto.take(MAX_CHARS).replace("\r\n", "\n").split("\n").mapNotNull { raw ->
            val linha = raw.trim()
            if (linha.isEmpty()) return@mapNotNull null
            val match = speaker.find(linha)
            if (match != null && !match.groupValues[1].last().isDigit()) {
                match.groupValues[1].trim() to match.groupValues[2]
            } else {
                "" to linha
            }
        }
        return resumirUnidades(unidades(pares), frases, cortado)
    }

    private fun unidades(pares: List<Pair<String, String>>): List<Pair<String, String>> {
        val result = mutableListOf<Pair<String, String>>()
        for ((pessoa, texto) in pares) {
            for (parte in texto.split(split)) {
                var frase = parte.trim().split(Regex("\\s+")).joinToString(" ")
                if (frase.length < 3) continue
                if (frase.length > MAX_SENTENCE_CHARS) frase = frase.take(MAX_SENTENCE_CHARS).trimEnd() + "…"
                result.add(pessoa to frase)
            }
        }
        return result
    }

    private fun palavras(frase: String): List<String> =
        word.findAll(frase).map { it.value.lowercase() }.filter { it !in stopwords }.toList()

    private fun resumirUnidades(unidades: List<Pair<String, String>>, frases: Int, cortado: Boolean): ResumoResult {
        if (unidades.isEmpty()) return ResumoResult(emptyList(), emptyList(), emptyList(), emptyList(), emptyList(), 0, cortado)
        val porFrase = unidades.map { palavras(it.second) }
        val frequencia = mutableMapOf<String, Int>()
        porFrase.flatten().forEach { frequencia[it] = (frequencia[it] ?: 0) + 1 }
        val maior = (frequencia.values.maxOrNull() ?: 1).toDouble()

        val notas = unidades.indices.map { i ->
            val lista = porFrase[i]
            if (lista.size < 3) {
                0.0
            } else {
                val unicas = lista.toSet()
                var valor = unicas.sumOf { (frequencia[it] ?: 0) / maior } / sqrt(unicas.size.toDouble())
                val frase = unidades[i].second
                if (decision.containsMatchIn(frase) || task.containsMatchIn(frase)) valor *= 1.3
                valor
            }
        }
        val total = unidades.size
        var quantidade = if (frases > 0) frases else max(3, min(8, (total * 0.2).roundToInt()))
        quantidade = minOf(quantidade, MAX_SENTENCES, total)
        val ordem = unidades.indices.sortedWith(compareBy({ -notas[it] }, { it }))
        val escolhidas = ordem.take(quantidade).filter { notas[it] > 0 }.sorted()
            .ifEmpty { (0 until min(quantidade, total)).toList() }

        fun mostrar(i: Int): String {
            val (pessoa, frase) = unidades[i]
            return if (pessoa.isNotEmpty()) "$pessoa: $frase" else frase
        }

        fun unicos(itens: Sequence<String>) = itens.distinct().take(MAX_ITEMS).toList()

        return ResumoResult(
            frases = escolhidas.map(::mostrar),
            decisoes = unicos(unidades.indices.asSequence().filter { decision.containsMatchIn(unidades[it].second) }.map(::mostrar)),
            tarefas = unicos(
                unidades.indices.asSequence()
                    .filter { task.containsMatchIn(unidades[it].second) && !unidades[it].second.endsWith("?") }
                    .map(::mostrar),
            ),
            perguntas = unicos(
                unidades.indices.asSequence()
                    .filter { unidades[it].second.endsWith("?") && porFrase[it].size >= 2 }
                    .map(::mostrar),
            ),
            palavras = frequencia.entries.filter { it.value > 1 }
                .sortedWith(compareBy({ -it.value }, { it.key })).take(8).map { it.key },
            total = total,
            cortado = cortado,
        )
    }

    fun texto(resumo: ResumoResult, titulo: String = "Resumo"): String {
        if (resumo.frases.isEmpty()) return "Não há texto para resumir."
        val partes = mutableListOf("$titulo (${resumo.frases.size} de ${resumo.total} frases, escolhidas do próprio texto):")
        resumo.frases.forEach { partes.add("- $it") }
        listOf("Decisões" to resumo.decisoes, "Tarefas" to resumo.tarefas, "Perguntas" to resumo.perguntas).forEach { (nome, itens) ->
            if (itens.isNotEmpty()) {
                partes.add("")
                partes.add("$nome:")
                itens.forEach { partes.add("- $it") }
            }
        }
        if (resumo.palavras.isNotEmpty()) {
            partes.add("")
            partes.add("Palavras que mais aparecem: " + resumo.palavras.joinToString(", "))
        }
        if (resumo.cortado) {
            partes.add("")
            partes.add("O texto passou de $MAX_CHARS caracteres; o resumo usou só o começo.")
        }
        return partes.joinToString("\n")
    }
}
