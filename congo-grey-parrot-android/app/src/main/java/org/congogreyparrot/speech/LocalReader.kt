package org.congogreyparrot.speech

import android.content.Context
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import java.io.File
import java.util.Locale

class LocalReader(context: Context) : TextToSpeech.OnInitListener {
    private val engine = TextToSpeech(context, this)
    var ready: Boolean = false
        private set
    var notice: String = ""
        private set
    var onFileReady: ((File) -> Unit)? = null

    override fun onInit(status: Int) {
        if (status != TextToSpeech.SUCCESS) {
            ready = false
            notice = "O motor de voz do Android não iniciou."
            return
        }
        engine.language = Locale("pt", "BR")
        val offline = engine.voices.orEmpty().filter { voice -> !voice.isNetworkConnectionRequired }
        val chosen = offline.firstOrNull { it.locale.language == "pt" && it.locale.country == "BR" }
            ?: offline.firstOrNull { it.locale.language == "pt" }
            ?: offline.firstOrNull()
        if (chosen == null) {
            ready = false
            notice = "Não há voz instalada que funcione sem internet."
            return
        }
        engine.voice = chosen
        ready = true
        notice = ""
    }

    fun speak(text: String, speed: Float) {
        engine.setSpeechRate(speed)
        engine.speak(text, TextToSpeech.QUEUE_FLUSH, null, "read")
    }

    fun stop() {
        engine.stop()
    }

    fun saveWav(text: String, file: File, speed: Float) {
        engine.setSpeechRate(speed)
        engine.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
            override fun onStart(utteranceId: String?) = Unit

            override fun onDone(utteranceId: String?) {
                if (utteranceId == "save") {
                    onFileReady?.invoke(file)
                }
            }

            @Deprecated("Compatibilidade com APIs antigas")
            override fun onError(utteranceId: String?) = Unit
        })
        engine.synthesizeToFile(text, null, file, "save")
    }

    fun shutdown() {
        engine.shutdown()
    }
}
