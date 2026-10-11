package org.congogreyparrot

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import org.congogreyparrot.ui.CongoApp
import org.congogreyparrot.ui.theme.CongoTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val preferences = getSharedPreferences("congo", MODE_PRIVATE)
        setContent {
            val mode = remember {
                mutableStateOf(preferences.getString("theme", "light") ?: "light")
            }
            val filter = remember {
                mutableStateOf(preferences.getString("color_filter", "none") ?: "none")
            }
            CongoTheme(mode = mode.value, filter = filter.value) {
                CongoApp(
                    mode = mode.value,
                    onMode = { value ->
                        preferences.edit().putString("theme", value).apply()
                        mode.value = value
                    },
                    filter = filter.value,
                    onFilter = { value ->
                        preferences.edit().putString("color_filter", value).apply()
                        filter.value = value
                    },
                )
            }
        }
    }
}
