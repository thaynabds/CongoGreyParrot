package org.congogreyparrot.ui

import android.Manifest
import android.content.pm.PackageManager
import android.os.Handler
import android.os.Looper
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.annotation.DrawableRes
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import org.congogreyparrot.R
import org.congogreyparrot.audio.FieldRecorder
import org.congogreyparrot.files.Cabinet
import org.congogreyparrot.files.copyToUri
import org.congogreyparrot.files.shareFile
import org.congogreyparrot.files.writeBytes
import org.congogreyparrot.speech.LocalReader
import java.io.File

private data class Destination(
    val key: String,
    val label: String,
    @DrawableRes val icon: Int,
    val hint: String,
)

private val destinations = listOf(
    Destination("home", "Início", R.drawable.ic_home, "Tela principal"),
    Destination("transcribe", "Gravar", R.drawable.ic_mic, "Microfone"),
    Destination("speech", "Ler", R.drawable.ic_read, "Texto em voz"),
    Destination("files", "Arquivos", R.drawable.ic_folder, "Pasta"),
    Destination("settings", "Ajustes", R.drawable.ic_settings, "Engrenagem"),
)

@Composable
fun CongoApp(
    mode: String,
    onMode: (String) -> Unit,
    filter: String = "none",
    onFilter: (String) -> Unit = {},
) {
    var page by remember { mutableStateOf("home") }
    Scaffold(
        bottomBar = {
            NavigationBar {
                destinations.forEach { item ->
                    NavigationBarItem(
                        selected = page == item.key,
                        onClick = { page = item.key },
                        icon = { Mark(item.icon, item.hint) },
                        label = { Text(item.label) },
                    )
                }
            }
        },
    ) { padding ->
        Column(
            Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 16.dp, vertical = 12.dp),
        ) {
            when (page) {
                "home" -> HomeScreen(onOpen = { page = it })
                "transcribe" -> RecordScreen()
                "speech" -> ReadScreen()
                "files" -> FilesScreen()
                else -> SettingsScreen(mode, onMode, filter, onFilter)
            }
        }
    }
}

@Composable
private fun Mark(@DrawableRes icon: Int, description: String, size: Int = 24) {
    Icon(
        painter = painterResource(icon),
        contentDescription = description,
        modifier = Modifier.size(size.dp),
    )
}

@Composable
private fun HomeScreen(onOpen: (String) -> Unit) {
    Column(Modifier.verticalScroll(rememberScrollState())) {
        Text("Congo Grey Parrot", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.SemiBold)
        Text(
            "Grave, leia em voz alta e guarde os arquivos neste aparelho.",
            modifier = Modifier.padding(top = 6.dp, bottom = 16.dp),
            color = MaterialTheme.colorScheme.onSurface,
        )
        ActionCard(
            icon = R.drawable.ic_mic,
            title = "Gravar áudio",
            detail = "O microfone grava um arquivo neste aparelho.",
            onClick = { onOpen("transcribe") },
        )
        Spacer(Modifier.height(10.dp))
        ActionCard(
            icon = R.drawable.ic_read,
            title = "Ler texto",
            detail = "A voz do aparelho lê o que você escrever.",
            onClick = { onOpen("speech") },
        )
        Spacer(Modifier.height(10.dp))
        ActionCard(
            icon = R.drawable.ic_folder,
            title = "Arquivos salvos",
            detail = "Compartilhe ou apague o que já foi gravado.",
            onClick = { onOpen("files") },
        )
    }
}

@Composable
private fun ActionCard(@DrawableRes icon: Int, title: String, detail: String, onClick: () -> Unit) {
    Card(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
    ) {
        Row(
            Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            Mark(icon, title, 36)
            Column {
                Text(title, style = MaterialTheme.typography.titleMedium)
                Text(detail, style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
}

@Composable
private fun RecordScreen() {
    val context = LocalContext.current
    val cabinet = remember { Cabinet(context) }
    val recorder = remember { FieldRecorder(context) }
    var recording by remember { mutableStateOf(false) }
    var message by remember { mutableStateOf("Toque no microfone. O arquivo fica neste aparelho.") }
    var lastFile by remember { mutableStateOf<File?>(null) }
    val saveRecording = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("audio/mp4")) { uri ->
        val file = lastFile
        if (uri == null || file == null) {
            message = "Nenhuma pasta foi escolhida. A gravação continua na lista Arquivos."
            return@rememberLauncherForActivityResult
        }
        message = if (copyToUri(context, uri, file)) {
            "Gravação salva no local escolhido. A cópia da lista Arquivos permanece."
        } else {
            "Não foi possível gravar nesse local."
        }
    }

    fun begin() {
        val file = cabinet.audioFile("gravacao", "m4a")
        recorder.start(file)
        lastFile = file
        recording = true
        message = "Gravando ${file.name}"
    }

    val permission = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted) {
            begin()
        } else {
            message = "Sem permissão de microfone, a gravação não começa."
        }
    }

    DisposableEffect(recorder) {
        onDispose { recorder.stop() }
    }

    Column(Modifier.fillMaxSize(), horizontalAlignment = Alignment.CenterHorizontally) {
        Text("Gravação", style = MaterialTheme.typography.headlineSmall)
        Spacer(Modifier.height(24.dp))
        Button(
            onClick = {
                if (recording) {
                    recorder.stop()
                    recording = false
                    message = lastFile?.let { "Gravação pronta: ${it.name}." }
                        ?: "A gravação não foi concluída."
                } else if (
                    ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO)
                    == PackageManager.PERMISSION_GRANTED
                ) {
                    begin()
                } else {
                    permission.launch(Manifest.permission.RECORD_AUDIO)
                }
            },
            modifier = Modifier.size(120.dp),
            shape = RoundedCornerShape(60.dp),
        ) {
            Mark(
                if (recording) R.drawable.ic_stop else R.drawable.ic_mic,
                if (recording) "Parar" else "Gravar",
                48,
            )
        }
        Text(
            if (recording) "Parar" else "Gravar",
            modifier = Modifier.padding(top = 12.dp),
            style = MaterialTheme.typography.titleMedium,
        )
        Text(message, modifier = Modifier.padding(top = 16.dp))
        lastFile?.let { file ->
            FilledTonalButton(
                onClick = { saveRecording.launch(file.name) },
                modifier = Modifier.fillMaxWidth().padding(top = 16.dp),
                enabled = !recording,
            ) {
                Mark(R.drawable.ic_save, "Salvar")
                Text("  Escolher pasta e salvar")
            }
            FilledTonalButton(
                onClick = { shareFile(context, file) },
                modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
            ) {
                Mark(R.drawable.ic_share, "Compartilhar")
                Text("  Compartilhar gravação", modifier = Modifier.padding(start = 8.dp))
            }
        }
    }
}

@Composable
private fun ReadScreen() {
    val context = LocalContext.current
    val cabinet = remember { Cabinet(context) }
    val reader = remember { LocalReader(context) }
    var text by remember { mutableStateOf("") }
    var speed by remember { mutableFloatStateOf(1f) }
    var message by remember { mutableStateOf("A voz escolhida não usa a rede. Ao salvar, você escolhe a pasta.") }
    var pendingAudio by remember { mutableStateOf<File?>(null) }
    val saveText = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("text/plain")) { uri ->
        if (uri == null) {
            message = "Nenhuma pasta foi escolhida."
            return@rememberLauncherForActivityResult
        }
        message = if (writeBytes(context, uri, text.toByteArray())) {
            "Texto salvo no local escolhido."
        } else {
            "Não foi possível gravar nesse local."
        }
    }
    val saveAudio = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("audio/wav")) { uri ->
        val file = pendingAudio
        if (uri == null || file == null) {
            message = "Nenhuma pasta foi escolhida. O áudio continua na lista Arquivos."
            return@rememberLauncherForActivityResult
        }
        message = if (copyToUri(context, uri, file)) {
            "Áudio salvo no local escolhido. A cópia da lista Arquivos permanece."
        } else {
            "Não foi possível gravar nesse local."
        }
    }

    DisposableEffect(reader) {
        reader.onFileReady = { file ->
            pendingAudio = file
            Handler(Looper.getMainLooper()).post { saveAudio.launch(file.name) }
        }
        onDispose { reader.shutdown() }
    }

    Column(Modifier.verticalScroll(rememberScrollState())) {
        Text("Leitura", style = MaterialTheme.typography.headlineSmall)
        OutlinedTextField(
            value = text,
            onValueChange = { text = it },
            modifier = Modifier.fillMaxWidth().padding(top = 12.dp),
            label = { Text("Texto") },
            minLines = 5,
        )
        Text("Velocidade ${"%.1f".format(speed)}x", modifier = Modifier.padding(top = 12.dp))
        Slider(value = speed, onValueChange = { speed = it }, valueRange = 0.5f..2f)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.padding(top = 8.dp)) {
            Button(onClick = {
                if (text.isBlank()) {
                    message = "Digite um texto antes de ler."
                } else if (!reader.ready) {
                    message = reader.notice.ifBlank { "O motor de voz do Android ainda não ficou pronto." }
                } else {
                    reader.speak(text, speed)
                    message = "Lendo com uma voz instalada neste aparelho."
                }
            }) {
                Mark(R.drawable.ic_read, "Ler")
                Text("  Ler")
            }
            OutlinedButton(onClick = { reader.stop() }) {
                Mark(R.drawable.ic_stop, "Parar")
                Text("  Parar")
            }
        }
        FilledTonalButton(
            onClick = {
                if (text.isBlank()) {
                    message = "Não há texto para salvar."
                    return@FilledTonalButton
                }
                cabinet.writeText("texto.txt", text)
                saveText.launch("texto.txt")
            },
            modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
        ) {
            Mark(R.drawable.ic_save, "Salvar texto")
            Text("  Salvar texto")
        }
        FilledTonalButton(
            onClick = {
                if (text.isBlank() || !reader.ready) {
                    message = reader.notice.ifBlank { "Digite um texto e espere o motor de voz ficar pronto." }
                    return@FilledTonalButton
                }
                val file = cabinet.audioFile("leitura", "wav")
                reader.saveWav(text, file, speed)
                message = "Gerando o áudio. Em seguida, escolha a pasta."
            },
            modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
        ) {
            Mark(R.drawable.ic_save, "Salvar áudio")
            Text("  Salvar áudio")
        }
        Text(message, modifier = Modifier.padding(top = 12.dp))
    }
}

@Composable
private fun FilesScreen() {
    val context = LocalContext.current
    val cabinet = remember { Cabinet(context) }
    var files by remember { mutableStateOf(cabinet.list()) }

    Column(Modifier.fillMaxSize()) {
        Text("Arquivos", style = MaterialTheme.typography.headlineSmall)
        if (files.isEmpty()) {
            Text("Nenhum arquivo salvo ainda.", modifier = Modifier.padding(top = 16.dp))
            return
        }
        LazyColumn(Modifier.fillMaxSize().padding(top = 8.dp)) {
            items(files, key = { it.absolutePath }) { file ->
                Card(
                    modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp),
                    shape = RoundedCornerShape(14.dp),
                ) {
                    Column(Modifier.padding(14.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Mark(
                                if (file.extension.equals("txt", true)) R.drawable.ic_read else R.drawable.ic_mic,
                                file.extension,
                            )
                            Text(file.name, modifier = Modifier.padding(start = 10.dp))
                        }
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.padding(top = 8.dp)) {
                            FilledTonalButton(onClick = { shareFile(context, file) }) {
                                Mark(R.drawable.ic_share, "Compartilhar")
                                Text("  Compartilhar")
                            }
                            OutlinedButton(onClick = {
                                cabinet.delete(file)
                                files = cabinet.list()
                            }) {
                                Mark(R.drawable.ic_delete, "Excluir")
                                Text("  Excluir")
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun Choice(label: String, active: Boolean, onClick: () -> Unit) {
    if (active) {
        Button(
            onClick = onClick,
            modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
        ) { Text("$label, ativo") }
    } else {
        OutlinedButton(
            onClick = onClick,
            modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
        ) { Text(label) }
    }
}

@Composable
private fun SettingsScreen(
    mode: String,
    onMode: (String) -> Unit,
    filter: String,
    onFilter: (String) -> Unit,
) {
    Column(Modifier.verticalScroll(rememberScrollState())) {
        Text("Aparência", style = MaterialTheme.typography.headlineSmall)
        listOf(
            "light" to "Claro",
            "dark" to "Escuro",
            "high_contrast" to "Alto contraste",
            "kuro" to "Kuro",
            "pink_void" to "PinkVoid",
            "red_void" to "RedVoid",
            "yellow_void" to "YellowVoid",
        ).forEach { (value, label) ->
            Choice(label, mode == value) { onMode(value) }
        }
        Text(
            "Filtro de cor",
            style = MaterialTheme.typography.titleMedium,
            modifier = Modifier.padding(top = 16.dp),
        )
        listOf(
            "none" to "Nenhum",
            "invert" to "Inversão clássica",
            "smart_invert" to "Inversão inteligente",
            "protanopia" to "Protanopia",
            "deuteranopia" to "Deuteranopia",
            "tritanopia" to "Tritanopia",
            "grayscale" to "Monocromia",
        ).forEach { (value, label) ->
            Choice(label, filter == value) { onFilter(value) }
        }
        Text(
            "A inversão inteligente troca as cores da interface e mantém fotos e vídeo. A inversão clássica, a monocromia e os filtros de protanopia, deuteranopia e tritanopia alteram a tela toda.",
            modifier = Modifier.padding(top = 12.dp),
        )
        Text(
            "Salvar abre o seletor do Android para você escolher a pasta e o nome. Uma cópia fica na lista Arquivos, na pasta privada do aplicativo. O backup automático está desligado.",
            modifier = Modifier.padding(top = 16.dp),
        )
    }
}
