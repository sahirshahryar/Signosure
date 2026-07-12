package edu.gatech.recordthesehands.ui

import android.graphics.Outline
import android.util.Log
import android.util.Size
import android.view.View
import android.view.ViewOutlineProvider
import androidx.camera.core.CameraSelector
import androidx.camera.core.Preview
import androidx.camera.core.resolutionselector.AspectRatioStrategy
import androidx.camera.core.resolutionselector.ResolutionSelector
import androidx.camera.core.resolutionselector.ResolutionStrategy
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.LocalLifecycleOwner

import androidx.compose.ui.tooling.preview.Preview as Preview2


private const val TAG = "CameraPreview"

/**
 * Maximum resolution in pixels (9 megapixels).
 * This limits the camera to reasonable resolutions while still getting full-sensor width.
 */
private const val MAXIMUM_RESOLUTION = 9_000_000

@Preview2 @Composable
fun CameraPreview(
    modifier: Modifier = Modifier,
    cameraSelector: CameraSelector = CameraSelector.DEFAULT_FRONT_CAMERA,
    cornerRadius: Dp = 24.dp,
    timerContent: @Composable (() -> Unit)? = null
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current

    var cameraProvider by remember { mutableStateOf<ProcessCameraProvider?>(null) }
    var isLoading by remember { mutableStateOf(true) }
    var errorMessage by remember { mutableStateOf<String?>(null) }

    DisposableEffect(Unit) {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(context)

        cameraProviderFuture.addListener({
            try {
                cameraProvider = cameraProviderFuture.get()
                isLoading = false
            } catch (e: Exception) {
                Log.e(TAG, "Failed to get camera provider", e)
                errorMessage = "Failed to initialize camera: ${e.message}"
                isLoading = false
            }
        }, ContextCompat.getMainExecutor(context))

        onDispose {
            cameraProvider?.unbindAll()
        }
    }

    Box(modifier = modifier) {
        when {
            isLoading -> {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator(color = Color.White)
                }
            }
            errorMessage != null -> {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = errorMessage!!,
                        color = Color.White
                    )
                }
            }
            cameraProvider != null -> {
                CameraPreviewView(
                    cameraProvider = cameraProvider!!,
                    lifecycleOwner = lifecycleOwner,
                    cameraSelector = cameraSelector,
                    cornerRadius = cornerRadius,
                    modifier = Modifier.fillMaxSize()
                )

                // Timer overlay positioned at top-end of the preview
                if (timerContent != null) {
                    Box(
                        modifier = Modifier
                            .align(Alignment.TopEnd)
                            .padding(16.dp)
                    ) {
                        timerContent()
                    }
                }
            }
        }
    }
}

@Composable
private fun CameraPreviewView(
    cameraProvider: ProcessCameraProvider,
    lifecycleOwner: androidx.lifecycle.LifecycleOwner,
    cameraSelector: CameraSelector,
    cornerRadius: Dp,
    modifier: Modifier = Modifier
) {
    val previewView = remember { mutableStateOf<PreviewView?>(null) }
    val density = LocalDensity.current
    val cornerRadiusPx = with(density) { cornerRadius.toPx() }

    AndroidView(
        factory = { ctx ->
            PreviewView(ctx).also { view ->
                // Use FIT_CENTER to show the full sensor image without cropping
                // This ensures we see the full width of the sensor
                view.scaleType = PreviewView.ScaleType.FIT_CENTER
                previewView.value = view

                // Apply rounded corners to the PreviewView itself
                view.outlineProvider = object : ViewOutlineProvider() {
                    override fun getOutline(view: View, outline: Outline) {
                        outline.setRoundRect(0, 0, view.width, view.height, cornerRadiusPx)
                    }
                }
                view.clipToOutline = true

                // Build a resolution selector that prefers 4:3 aspect ratio
                // (which typically gives the full sensor width) and targets
                // the highest resolution within our maximum limit
                val resolutionSelector = ResolutionSelector.Builder()
                    .setAspectRatioStrategy(
                        AspectRatioStrategy(
                            AspectRatioStrategy.RATIO_4_3_FALLBACK_AUTO_STRATEGY.preferredAspectRatio,
                            AspectRatioStrategy.FALLBACK_RULE_AUTO
                        )
                    )
                    .setResolutionStrategy(
                        ResolutionStrategy(
                            // Target a large 4:3 resolution (3000x2250 = 6.75MP)
                            // The camera will pick the closest available size
                            Size(3000, 2250),
                            ResolutionStrategy.FALLBACK_RULE_CLOSEST_HIGHER_THEN_LOWER
                        )
                    )
                    .build()

                val preview = Preview.Builder()
                    .setResolutionSelector(resolutionSelector)
                    .build()
                    .also { it.setSurfaceProvider(view.surfaceProvider) }

                try {
                    cameraProvider.unbindAll()
                    cameraProvider.bindToLifecycle(
                        lifecycleOwner,
                        cameraSelector,
                        preview
                    )

                    // Log the actual selected resolution
                    val resolutionInfo = preview.resolutionInfo
                    if (resolutionInfo != null) {
                        val resolution = resolutionInfo.resolution
                        Log.d(TAG, "Selected resolution: ${resolution.width}x${resolution.height}")
                        Log.d(TAG, "Crop rect: ${resolutionInfo.cropRect}")
                        Log.d(TAG, "Rotation degrees: ${resolutionInfo.rotationDegrees}")
                    } else {
                        Log.d(TAG, "ResolutionInfo not yet available")
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "Failed to bind camera use cases", e)
                }
            }
        },
        modifier = modifier
    )
}
