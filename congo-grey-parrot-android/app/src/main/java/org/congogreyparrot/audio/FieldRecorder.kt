package org.congogreyparrot.audio

import android.content.Context
import android.media.MediaRecorder
import android.os.Build
import java.io.File

class FieldRecorder(private val context: Context) {
    private var recorder: MediaRecorder? = null
    var output: File? = null
        private set

    fun start(file: File) {
        val media = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            MediaRecorder(context)
        } else {
            @Suppress("DEPRECATION")
            MediaRecorder()
        }
        media.setAudioSource(MediaRecorder.AudioSource.MIC)
        media.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
        media.setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
        media.setOutputFile(file.absolutePath)
        media.prepare()
        media.start()
        recorder = media
        output = file
    }

    fun stop() {
        val current = recorder ?: return
        try {
            current.stop()
        } catch (_: RuntimeException) {
            output?.delete()
            output = null
        }
        current.release()
        recorder = null
    }
}
