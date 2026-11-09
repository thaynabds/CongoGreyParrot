package org.congogreyparrot.ui.theme

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.ColorScheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawWithCache
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ColorFilter
import androidx.compose.ui.graphics.ColorMatrix
import androidx.compose.ui.graphics.Paint
import androidx.compose.ui.graphics.drawscope.drawIntoCanvas

private val LightColors = lightColorScheme(
    primary = Color(0xFF1B6B45),
    onPrimary = Color.White,
    background = Color(0xFFF4F7F5),
    surface = Color.White,
    onBackground = Color(0xFF1C2420),
    onSurface = Color(0xFF1C2420),
)

private val DarkColors = darkColorScheme(
    primary = Color(0xFF8FD4B4),
    onPrimary = Color(0xFF052117),
    background = Color(0xFF121816),
    surface = Color(0xFF1B2621),
    onBackground = Color(0xFFEEF5F1),
    onSurface = Color(0xFFEEF5F1),
)

private val KuroColors = darkColorScheme(
    primary = Color(0xFFB794F6),
    onPrimary = Color(0xFF1A1030),
    background = Color(0xFF100E16),
    surface = Color(0xFF1C1730),
    onBackground = Color(0xFFF4EEFE),
    onSurface = Color(0xFFF4EEFE),
)

private val PinkVoidColors = darkColorScheme(
    primary = Color(0xFFE56AA3),
    onPrimary = Color(0xFF2A1020),
    background = Color(0xFF160E12),
    surface = Color(0xFF2A1520),
    onBackground = Color(0xFFFBEFF4),
    onSurface = Color(0xFFFBEFF4),
)

private val RedVoidColors = darkColorScheme(
    primary = Color(0xFFE26464),
    onPrimary = Color(0xFF2A1010),
    background = Color(0xFF160E0E),
    surface = Color(0xFF2A1515),
    onBackground = Color(0xFFFBEEEE),
    onSurface = Color(0xFFFBEEEE),
)

private val YellowVoidColors = darkColorScheme(
    primary = Color(0xFFE6C200),
    onPrimary = Color(0xFF1A1404),
    background = Color(0xFF14120C),
    surface = Color(0xFF262014),
    onBackground = Color(0xFFFBF6E8),
    onSurface = Color(0xFFFBF6E8),
)

private val GreenVoidColors = darkColorScheme(
    primary = Color(0xFF5FD08A),
    onPrimary = Color(0xFF04210F),
    background = Color(0xFF0C140E),
    surface = Color(0xFF142A1A),
    onBackground = Color(0xFFEEFBF1),
    onSurface = Color(0xFFEEFBF1),
)

private val BlueVoidColors = darkColorScheme(
    primary = Color(0xFF6AA8E5),
    onPrimary = Color(0xFF0C1B2A),
    background = Color(0xFF0C1016),
    surface = Color(0xFF14202F),
    onBackground = Color(0xFFEEF4FB),
    onSurface = Color(0xFFEEF4FB),
)

private val KuroLightColors = lightColorScheme(
    primary = Color(0xFF5534A8),
    onPrimary = Color.White,
    background = Color(0xFFF5F1FD),
    surface = Color.White,
    onBackground = Color(0xFF1F1833),
    onSurface = Color(0xFF1F1833),
)

private val PinkVoidLightColors = lightColorScheme(
    primary = Color(0xFF9A2864),
    onPrimary = Color.White,
    background = Color(0xFFFDF1F6),
    surface = Color.White,
    onBackground = Color(0xFF2F1420),
    onSurface = Color(0xFF2F1420),
)

private val RedVoidLightColors = lightColorScheme(
    primary = Color(0xFF8E2424),
    onPrimary = Color.White,
    background = Color(0xFFFDF1F1),
    surface = Color.White,
    onBackground = Color(0xFF2F1414),
    onSurface = Color(0xFF2F1414),
)

private val YellowVoidLightColors = lightColorScheme(
    primary = Color(0xFF6B5600),
    onPrimary = Color.White,
    background = Color(0xFFFDF8E6),
    surface = Color.White,
    onBackground = Color(0xFF2B2408),
    onSurface = Color(0xFF2B2408),
)

private val GreenVoidLightColors = lightColorScheme(
    primary = Color(0xFF1A6B35),
    onPrimary = Color.White,
    background = Color(0xFFEFFAF1),
    surface = Color.White,
    onBackground = Color(0xFF12291A),
    onSurface = Color(0xFF12291A),
)

private val BlueVoidLightColors = lightColorScheme(
    primary = Color(0xFF1F55A8),
    onPrimary = Color.White,
    background = Color(0xFFEFF5FD),
    surface = Color.White,
    onBackground = Color(0xFF12203A),
    onSurface = Color(0xFF12203A),
)

private val ContrastLightColors = lightColorScheme(
    primary = Color.Blue,
    onPrimary = Color.White,
    background = Color.White,
    surface = Color.White,
    onBackground = Color.Black,
    onSurface = Color.Black,
    outline = Color.Blue,
)

private val ContrastColors = darkColorScheme(
    primary = Color.Yellow,
    onPrimary = Color.Black,
    background = Color.Black,
    surface = Color.Black,
    onBackground = Color.White,
    onSurface = Color.White,
    outline = Color.Yellow,
)

@Composable
fun CongoTheme(mode: String, filter: String = "none", content: @Composable () -> Unit) {
    val base = when (mode) {
        "dark" -> DarkColors
        "high_contrast" -> ContrastColors
        "kuro" -> KuroColors
        "pink_void" -> PinkVoidColors
        "red_void" -> RedVoidColors
        "yellow_void" -> YellowVoidColors
        "green_void" -> GreenVoidColors
        "blue_void" -> BlueVoidColors
        "high_contrast_light" -> ContrastLightColors
        "kuro_light" -> KuroLightColors
        "pink_void_light" -> PinkVoidLightColors
        "red_void_light" -> RedVoidLightColors
        "yellow_void_light" -> YellowVoidLightColors
        "green_void_light" -> GreenVoidLightColors
        "blue_void_light" -> BlueVoidLightColors
        else -> LightColors
    }
    val colors = if (filter == "smart_invert") base.opposite() else base
    MaterialTheme(colorScheme = colors) {
        Box(Modifier.fillMaxSize().screenFilter(filter)) {
            content()
        }
    }
}

private fun Color.opposite(): Color = Color(
    red = 1f - red,
    green = 1f - green,
    blue = 1f - blue,
    alpha = alpha,
)

private fun ColorScheme.opposite(): ColorScheme = copy(
    primary = primary.opposite(),
    onPrimary = onPrimary.opposite(),
    primaryContainer = primaryContainer.opposite(),
    onPrimaryContainer = onPrimaryContainer.opposite(),
    background = background.opposite(),
    onBackground = onBackground.opposite(),
    surface = surface.opposite(),
    onSurface = onSurface.opposite(),
    surfaceVariant = surfaceVariant.opposite(),
    onSurfaceVariant = onSurfaceVariant.opposite(),
    outline = outline.opposite(),
)

private fun Modifier.screenFilter(filter: String): Modifier {
    val values = colorMatrices[filter] ?: return this
    return drawWithCache {
        val paint = Paint().apply {
            colorFilter = ColorFilter.colorMatrix(ColorMatrix(values))
        }
        val bounds = Rect(0f, 0f, size.width, size.height)
        onDrawWithContent {
            drawIntoCanvas { canvas ->
                canvas.saveLayer(bounds, paint)
                drawContent()
                canvas.restore()
            }
        }
    }
}

// Mesmas matrizes do desktop. Daltonizer do Android, modo Correction:
// https://android.googlesource.com/platform/frameworks/native/+/refs/heads/master/services/surfaceflinger/Effects/Daltonizer.cpp
// Monocromia: Rec. ITU-R BT.709, https://www.itu.int/rec/R-REC-BT.709
// O deslocamento do ColorMatrix fica na escala 0..255.
private val colorMatrices = mapOf(
    "invert" to floatArrayOf(
        -1f, 0f, 0f, 0f, 255f,
        0f, -1f, 0f, 0f, 255f,
        0f, 0f, -1f, 0f, 255f,
        0f, 0f, 0f, 1f, 0f,
    ),
    "protanopia" to floatArrayOf(
        0.46111f, 0.53889f, 0f, 0f, 0f,
        0.37754f, 0.62246f, 0f, 0f, 0f,
        0.30974f, -0.30974f, 1f, 0f, 0f,
        0f, 0f, 0f, 1f, 0f,
    ),
    "deuteranopia" to floatArrayOf(
        -0.01672f, 1.01672f, 0f, 0f, 0f,
        0.07530f, 0.92470f, 0f, 0f, 0f,
        -0.36845f, 0.36845f, 1f, 0f, 0f,
        0f, 0f, 0f, 1f, 0f,
    ),
    "tritanopia" to floatArrayOf(
        1f, -1.15102f, 1.15102f, 0f, 0f,
        0f, 0.11263f, 0.88737f, 0f, 0f,
        0f, 0.14975f, 0.85025f, 0f, 0f,
        0f, 0f, 0f, 1f, 0f,
    ),
    "grayscale" to floatArrayOf(
        0.2126f, 0.7152f, 0.0722f, 0f, 0f,
        0.2126f, 0.7152f, 0.0722f, 0f, 0f,
        0.2126f, 0.7152f, 0.0722f, 0f, 0f,
        0f, 0f, 0f, 1f, 0f,
    ),
)
