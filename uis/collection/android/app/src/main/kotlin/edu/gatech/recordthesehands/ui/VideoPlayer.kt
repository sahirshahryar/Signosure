package edu.gatech.recordthesehands.ui

import android.content.Context
import android.graphics.Outline
import android.net.Uri
import android.view.View
import android.view.ViewOutlineProvider
import android.widget.VideoView
import androidx.annotation.RawRes
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView

/**
 * Creates a VideoView for a raw resource video.
 * Returns the VideoView instance for external control.
 */
fun createVideoView(
    context: Context,
    @RawRes videoResId: Int,
    playWhenReady: Boolean = true,
    loop: Boolean = true
): VideoView {
    return VideoView(context).apply {
        val uri = Uri.parse("android.resource://${context.packageName}/$videoResId")
        setVideoURI(uri)
        setOnPreparedListener { mp ->
            mp.isLooping = loop
            if (playWhenReady) {
                start()
            }
        }
    }
}

@Composable
fun VideoPlayer(
    videoView: VideoView,
    modifier: Modifier = Modifier,
    cornerRadius: Dp = 12.dp
) {
    val density = LocalDensity.current
    val cornerRadiusPx = with(density) { cornerRadius.toPx() }
    
    AndroidView(
        factory = { _ ->
            videoView.apply {
                // Apply rounded corners
                outlineProvider = object : ViewOutlineProvider() {
                    override fun getOutline(view: View, outline: Outline) {
                        outline.setRoundRect(0, 0, view.width, view.height, cornerRadiusPx)
                    }
                }
                clipToOutline = true
            }
        },
        update = { _ ->
            // VideoView is managed externally
        },
        modifier = modifier
    )
}

@Composable
fun VideoPlayer(
    @RawRes videoResId: Int,
    modifier: Modifier = Modifier,
    cornerRadius: Dp = 12.dp,
    playWhenReady: Boolean = true,
    loop: Boolean = true
) {
    val context = LocalContext.current
    val videoView = remember(videoResId) {
        createVideoView(context, videoResId, playWhenReady, loop)
    }
    
    DisposableEffect(videoResId) {
        onDispose {
            videoView.stopPlayback()
        }
    }
    
    VideoPlayer(
        videoView = videoView,
        modifier = modifier,
        cornerRadius = cornerRadius
    )
}
