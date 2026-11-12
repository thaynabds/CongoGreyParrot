package org.congogreyparrot.ai

import android.content.ContentProvider
import android.content.ContentValues
import android.content.Context
import android.database.Cursor
import android.net.Uri
import android.os.Binder
import android.os.Bundle
import android.os.Process
import android.util.Base64
import org.congogreyparrot.files.Cabinet
import org.congogreyparrot.speech.LocalReader
import org.congogreyparrot.text.Resumo
import org.json.JSONObject
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

/**
 * AI Conector do celular: o computador manda pedidos pelo cabo USB com
 * `adb shell content call --uri content://org.congogreyparrot.ai --method <ação> --arg <base64>`.
 *
 * Só o usuário shell do adb (uid 2000) ou o root passam. Outro aplicativo do celular
 * recebe recusa, mesmo com o provider exportado: o call() não tem trava automática,
 * então a conferência do uid fica aqui. Texto entra e sai em base64 para não passar
 * pelo shell do aparelho como comando.
 */
class AiBridgeProvider : ContentProvider() {
    private var reader: LocalReader? = null

    override fun onCreate(): Boolean = true

    override fun call(method: String, arg: String?, extras: Bundle?): Bundle {
        val uid = Binder.getCallingUid()
        if (uid != SHELL_UID && uid != Process.ROOT_UID) {
            return reply(false, "Pedido recusado: só o adb do computador usa o AI Conector.")
        }
        val ctx = context ?: return reply(false, "Aplicativo ainda abrindo.")
        val input = decode(arg)
        return try {
            val text = run(ctx, method, input)
            log(ctx, method, true)
            reply(true, text)
        } catch (exc: IllegalArgumentException) {
            log(ctx, method, false)
            reply(false, exc.message ?: "Pedido inválido.")
        }
    }

    private fun run(ctx: Context, method: String, input: JSONObject): String {
        val cabinet = Cabinet(ctx)
        return when (method) {
            "status" -> {
                val voice = voice(ctx)
                "Congo Grey Parrot no celular. Arquivos: ${cabinet.list().size}. ${voice.notice}"
            }
            "listar" -> cabinet.list().joinToString("\n") { "${it.name} (${it.length()} bytes)" }
                .ifBlank { "Nenhum arquivo salvo ainda." }
            "ler_arquivo" -> {
                val file = find(cabinet, input.optString("nome"))
                require(file.extension.lowercase() in TEXT_TYPES) { "Só leio arquivos de texto (txt ou md)." }
                require(file.length() <= MAX_FILE) { "O arquivo passa de 2 MB." }
                file.readText().take(MAX_TEXT)
            }
            "salvar" -> {
                val body = text(input)
                val name = input.optString("nome").ifBlank { "texto.txt" }
                require(name.substringAfterLast('.', "").lowercase() in TEXT_TYPES) { "Use um nome terminado em .txt ou .md." }
                val file = cabinet.writeText(name, body)
                "Salvo como ${file.name}."
            }
            "excluir" -> {
                val file = find(cabinet, input.optString("nome"))
                cabinet.delete(file)
                "Arquivo ${file.name} apagado."
            }
            "resumir" -> Resumo.texto(Resumo.resumir(text(input), input.optInt("frases", 0).coerceIn(0, 30)))
            "falar" -> {
                val voice = voice(ctx)
                require(voice.ready) { voice.notice.ifBlank { "A voz do aparelho ainda não está pronta." } }
                voice.speak(text(input), input.optDouble("velocidade", 1.0).toFloat().coerceIn(0.5f, 2.5f))
                "Lendo em voz alta no celular."
            }
            "parar_fala" -> {
                reader?.stop()
                "Leitura parada."
            }
            "salvar_audio" -> {
                val voice = voice(ctx)
                require(voice.ready) { voice.notice.ifBlank { "A voz do aparelho ainda não está pronta." } }
                val file = cabinet.audioFile(input.optString("nome").ifBlank { "leitura" }, "wav")
                val done = CountDownLatch(1)
                voice.onFileReady = { done.countDown() }
                voice.saveWav(text(input), file, input.optDouble("velocidade", 1.0).toFloat().coerceIn(0.5f, 2.5f))
                require(done.await(120, TimeUnit.SECONDS)) { "A voz demorou demais para gravar o áudio." }
                "Áudio salvo como ${file.name}."
            }
            else -> throw IllegalArgumentException("Ação desconhecida: use status, listar, ler_arquivo, salvar, excluir, resumir, falar, parar_fala ou salvar_audio.")
        }
    }

    private fun voice(ctx: Context): LocalReader {
        val current = reader ?: LocalReader(ctx.applicationContext).also { reader = it }
        val deadline = System.currentTimeMillis() + 4000
        while (current.notice.isBlank() && System.currentTimeMillis() < deadline) {
            Thread.sleep(100)
        }
        return current
    }

    private fun find(cabinet: Cabinet, raw: String): File {
        val name = raw.trim()
        require(name.isNotEmpty() && !name.contains('/') && !name.contains("..")) { "Informe só o nome do arquivo, como aparece em listar." }
        return cabinet.list().firstOrNull { it.name == name } ?: throw IllegalArgumentException("Não achei $name. Use listar.")
    }

    private fun text(input: JSONObject): String {
        val body = input.optString("texto")
        require(body.isNotBlank()) { "Escreva o texto." }
        require(body.length <= MAX_TEXT) { "O texto passa de 200 mil caracteres." }
        return body
    }

    private fun decode(arg: String?): JSONObject {
        if (arg.isNullOrBlank()) return JSONObject()
        return try {
            JSONObject(String(Base64.decode(arg, Base64.DEFAULT), Charsets.UTF_8))
        } catch (_: Exception) {
            JSONObject()
        }
    }

    private fun reply(ok: Boolean, text: String): Bundle = Bundle().apply {
        putBoolean("ok", ok)
        putString("resultado", Base64.encodeToString(text.toByteArray(Charsets.UTF_8), Base64.NO_WRAP))
    }

    private fun log(ctx: Context, method: String, ok: Boolean) {
        // Guarda só a ação e a hora, nunca o texto, para a tela AI Conector mostrar o que a IA fez.
        val prefs = ctx.getSharedPreferences(LOG_PREFS, Context.MODE_PRIVATE)
        val stamp = SimpleDateFormat("dd/MM HH:mm:ss", Locale("pt", "BR")).format(Date())
        val line = "$stamp · $method · ${if (ok) "ok" else "recusado"}"
        val old = prefs.getString(LOG_KEY, "").orEmpty().lines().filter { it.isNotBlank() }.take(MAX_LOG - 1)
        prefs.edit().putString(LOG_KEY, (listOf(line) + old).joinToString("\n")).apply()
    }

    override fun query(uri: Uri, projection: Array<out String>?, selection: String?, selectionArgs: Array<out String>?, sortOrder: String?): Cursor? = null
    override fun getType(uri: Uri): String? = null
    override fun insert(uri: Uri, values: ContentValues?): Uri? = null
    override fun delete(uri: Uri, selection: String?, selectionArgs: Array<out String>?): Int = 0
    override fun update(uri: Uri, values: ContentValues?, selection: String?, selectionArgs: Array<out String>?): Int = 0

    companion object {
        const val SHELL_UID = 2000
        const val LOG_PREFS = "ai_conector"
        const val LOG_KEY = "log"
        private const val MAX_LOG = 30
        private const val MAX_TEXT = 200_000
        private const val MAX_FILE = 2L * 1024 * 1024
        private val TEXT_TYPES = setOf("txt", "md")

        fun recent(ctx: Context): List<String> =
            ctx.getSharedPreferences(LOG_PREFS, Context.MODE_PRIVATE).getString(LOG_KEY, "").orEmpty()
                .lines().filter { it.isNotBlank() }
    }
}
