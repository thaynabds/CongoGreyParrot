package org.congogreyparrot.files

import android.content.ClipData
import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.core.content.FileProvider
import java.io.File

class Cabinet(context: Context) {
    private val root = File(context.filesDir, "cabinet").apply { mkdirs() }

    fun list(): List<File> = root.listFiles()?.sortedByDescending { it.lastModified() }.orEmpty()

    fun writeText(name: String, text: String): File {
        val file = File(root, sanitize(name))
        file.writeText(text)
        return file
    }

    fun audioFile(prefix: String, extension: String): File {
        return File(root, "${sanitize(prefix)}-${System.currentTimeMillis()}.${extension}")
    }

    fun delete(file: File) {
        if (file.parentFile == root) {
            file.delete()
        }
    }

    private fun sanitize(name: String): String {
        val cleaned = name.replace(Regex("[^\\w.\\- ]"), "_").trim().ifBlank { "arquivo" }
        return cleaned.take(80)
    }
}

fun writeBytes(context: Context, uri: Uri, bytes: ByteArray): Boolean {
    return try {
        val stream = context.contentResolver.openOutputStream(uri) ?: return false
        stream.use { it.write(bytes) }
        true
    } catch (_: Exception) {
        false
    }
}

fun copyToUri(context: Context, uri: Uri, file: File): Boolean {
    return try {
        val stream = context.contentResolver.openOutputStream(uri) ?: return false
        stream.use { output -> file.inputStream().use { input -> input.copyTo(output) } }
        true
    } catch (_: Exception) {
        false
    }
}

fun shareFile(context: Context, file: File) {
    val uri = FileProvider.getUriForFile(context, "${context.packageName}.files", file)
    val intent = Intent(Intent.ACTION_SEND).apply {
        type = when (file.extension.lowercase()) {
            "wav", "m4a", "mp3" -> "audio/*"
            "txt", "md" -> "text/plain"
            else -> "*/*"
        }
        putExtra(Intent.EXTRA_STREAM, uri)
        clipData = ClipData.newRawUri("arquivo", uri)
        addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    }
    context.startActivity(Intent.createChooser(intent, "Compartilhar arquivo"))
}
