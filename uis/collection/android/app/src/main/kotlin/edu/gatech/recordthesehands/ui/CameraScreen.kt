package edu.gatech.recordthesehands.ui

import android.Manifest
import android.util.Log
import androidx.compose.foundation.background
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.EnterTransition
import androidx.compose.animation.ExitTransition
import androidx.compose.animation.SizeTransform
import androidx.compose.animation.togetherWith
import androidx.compose.animation.core.tween
import androidx.compose.animation.core.Animatable
import androidx.compose.foundation.gestures.detectHorizontalDragGestures
import androidx.compose.foundation.gestures.detectVerticalDragGestures
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.pager.PagerState
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.launch
import com.google.accompanist.permissions.ExperimentalPermissionsApi
import com.google.accompanist.permissions.isGranted
import com.google.accompanist.permissions.rememberPermissionState
import com.google.accompanist.permissions.shouldShowRationale
import kotlinx.coroutines.delay
import edu.gatech.recordthesehands.R
import edu.gatech.recordthesehands.model.PromptDetails
import android.widget.VideoView
import androidx.compose.foundation.pager.PageSize
import androidx.constraintlayout.compose.ConstraintLayout
import androidx.constraintlayout.compose.Dimension

private const val COUNTDOWN_DURATION_MS = 15 * 60 * 1000L // 15 minutes

/**
 * Applies a rubber-band effect to a drag value.
 * Within the threshold, the value passes through unchanged.
 * Beyond the threshold, a quadratic falloff is applied so the drag feels springy.
 */
private fun rubberBand(value: Float, threshold: Float, maxStretch: Float = threshold * 0.5f): Float {
    return when {
        value > threshold -> {
            val overflow = value - threshold
            val dampened = maxStretch * (1 - 1 / (overflow / maxStretch + 1))
            threshold + dampened
        }
        value < -threshold -> {
            val overflow = -value - threshold
            val dampened = maxStretch * (1 - 1 / (overflow / maxStretch + 1))
            -(threshold + dampened)
        }
        else -> value
    }
}

private val samplePrompts = listOf(
    PromptDetails("1", "One", R.raw.time),
    PromptDetails("2", "Two", R.raw.time),
    PromptDetails("3", "Three", R.raw.time),
    PromptDetails("4", "Four", R.raw.time),
    PromptDetails("5", "Five", R.raw.time),
    PromptDetails("6", "Six", R.raw.time),
    PromptDetails("7", "Seven", R.raw.time),
    PromptDetails("8", "Eight", R.raw.time),
    PromptDetails("9", "Nine", R.raw.time),
    PromptDetails("10", "Ten", R.raw.time)
)

@OptIn(ExperimentalPermissionsApi::class)
@Composable
fun CameraScreen() {
    val cameraPermissionState = rememberPermissionState(Manifest.permission.CAMERA)

    when {
        cameraPermissionState.status.isGranted -> {
            CameraScreenContent()
        }
        cameraPermissionState.status.shouldShowRationale -> {
            PermissionRationale(
                onRequestPermission = { cameraPermissionState.launchPermissionRequest() }
            )
        }
        else -> {
            PermissionRequest(
                onRequestPermission = { cameraPermissionState.launchPermissionRequest() }
            )
        }
    }
}

@Composable
private fun CameraScreenContent() {
    var remainingTimeMs by remember { mutableLongStateOf(COUNTDOWN_DURATION_MS) }
    val textPagerState = rememberPagerState(
        initialPage = 0,
        pageCount = { samplePrompts.size }
    )
    val videoPagerState = rememberPagerState(
        initialPage = 0,
        pageCount = { samplePrompts.size }
    )
    val coroutineScope = rememberCoroutineScope()
    var accumulatedDrag by remember { mutableFloatStateOf(0f) }
    var startPage by remember { mutableIntStateOf(0) }
    val density = LocalDensity.current
    val dragThreshold = with(density) { 100.dp.toPx() }
    val context = LocalContext.current
    val configuration = LocalConfiguration.current
    val screenWidthDp = configuration.screenWidthDp.dp

    // Video expansion state (0 = collapsed, 1 = expanded)
    val videoExpansion = remember { Animatable(0f) }

    // Preload video views for all prompts
    val videoPlayers = remember {
        samplePrompts.mapNotNull { prompt ->
            prompt.videoResId?.let { resId ->
                prompt.id to createVideoView(context, resId, playWhenReady = false, loop = true)
            }
        }.toMap()
    }

    // Clean up video players when leaving
    DisposableEffect(Unit) {
        onDispose {
            videoPlayers.values.forEach { it.stopPlayback() }
        }
    }

    // Control which video is playing based on current page
    // Also prepare adjacent videos so they're ready when swiping
    LaunchedEffect(textPagerState.currentPage) {
        val currentPage = textPagerState.currentPage
        val currentPromptId = samplePrompts[currentPage].id

        // Get adjacent page IDs
        val prevPromptId = if (currentPage > 0) samplePrompts[currentPage - 1].id else null
        val nextPromptId = if (currentPage < samplePrompts.size - 1) samplePrompts[currentPage + 1].id else null

        videoPlayers.forEach { (id, player) ->
            when (id) {
                currentPromptId -> {
                    // Current page: play
                    player.seekTo(0)
                    player.start()
                }
                prevPromptId, nextPromptId -> {
                    // Adjacent pages: prepare but pause
                    // Start then immediately pause to trigger loading
                    player.seekTo(0)
                    player.start()
                    player.pause()
                }
                else -> {
                    // Other pages: just pause
                    player.pause()
                }
            }
        }
    }

    LaunchedEffect(Unit) {
        while (remainingTimeMs > 0) {
            delay(1000L)
            remainingTimeMs -= 1000L
        }
    }

    // Sync video pager with text pager
    LaunchedEffect(textPagerState.currentPage, textPagerState.currentPageOffsetFraction) {
        val targetPage = textPagerState.currentPage
        val targetOffset = textPagerState.currentPageOffsetFraction
        videoPagerState.scrollToPage(targetPage, targetOffset)
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black)
            // Horizontal drag for page navigation
            .pointerInput(textPagerState) {
                detectHorizontalDragGestures(
                    onDragStart = {
                        accumulatedDrag = 0f
                        startPage = textPagerState.currentPage
                    },
                    onDragEnd = {
                        coroutineScope.launch {
                            Log.d("CameraScreen", "onDragEnd: startPage=$startPage, currentPage=${textPagerState.currentPage}, accumulatedDrag=$accumulatedDrag")
                            val maxDrag = dragThreshold * 2.5f
                            val clampedDrag = accumulatedDrag.coerceIn(-maxDrag, maxDrag)
                            val targetPage = when {
                                clampedDrag < -dragThreshold && startPage < samplePrompts.size - 1 -> startPage + 1
                                clampedDrag > dragThreshold && startPage > 0 -> startPage - 1
                                else -> startPage
                            }
                            // Animate both pagers in parallel for smooth transition
                            launch { textPagerState.animateScrollToPage(targetPage) }
                            launch { videoPagerState.animateScrollToPage(targetPage) }
                            accumulatedDrag = 0f
                        }
                    },
                    onHorizontalDrag = { _, dragAmount ->
                        accumulatedDrag += dragAmount
                        val previousRubberBanded = rubberBand(accumulatedDrag - dragAmount, dragThreshold)
                        val currentRubberBanded = rubberBand(accumulatedDrag, dragThreshold)
                        val rubberBandedDragAmount = currentRubberBanded - previousRubberBanded

                        if (rubberBandedDragAmount != 0f) {
                            coroutineScope.launch {
                                // Scroll text pager - video pager syncs via LaunchedEffect
                                textPagerState.scroll {
                                    scrollBy(-rubberBandedDragAmount)
                                }
                            }
                        }
                    }
                )
            }
            // Vertical drag for video expansion
            .pointerInput(videoExpansion) {
                // Scaling factor: how many pixels of drag = full expansion (0 to 1)
                // Lower value = more sensitive, higher value = requires more drag
                val dragScaleFactor = 300f  // pixels to go from 0 to 1
                val snapThreshold = 0.5f  // Snap to expanded if above this, collapsed if below

                detectVerticalDragGestures(
                    onDragStart = { },
                    onDragEnd = {
                        coroutineScope.launch {
                            // Snap to nearest state based on current progress
                            val targetExpansion = if (videoExpansion.value >= snapThreshold) 1f else 0f
                            videoExpansion.animateTo(targetExpansion, tween(300))
                        }
                    },
                    onVerticalDrag = { _, dragAmount ->
                        // Convert drag pixels to progress delta
                        val progressDelta = dragAmount / dragScaleFactor
                        val newExpansion = (videoExpansion.value + progressDelta).coerceIn(0f, 1f)
                        coroutineScope.launch {
                            videoExpansion.snapTo(newExpansion)
                        }
                    }
                )
            }
    ) {
        // Two-phase expansion configuration
        val slideDownThreshold = 0.3f  // Phase (a) ends, phase (b) begins
        val progress = videoExpansion.value

        // Phase (a): 0 <= progress < slideDownThreshold
        // - "Sign the following:" slides up and disappears
        // - Text prompt shrinks
        // - Video slides down (top-right corner stays fixed, so it moves down by its height increase)

        // Phase (b): slideDownThreshold <= progress < 1.0
        // - Video expands width (top-right corner stays fixed)
        // - Text stays at reduced size

        // Calculate phase-specific progress values (0 to 1 within each phase)
        val phaseAProgress = (progress / slideDownThreshold).coerceIn(0f, 1f)
        val phaseBProgress = ((progress - slideDownThreshold) / (1f - slideDownThreshold)).coerceIn(0f, 1f)

        // Spacing - match camera preview margins (8.dp horizontal)
        val horizontalPadding = 8.dp
        val videoTextGap = 16.dp
        val videoBottomMargin = 8.dp  // Constant margin between video and camera preview

        // Video dimensions - larger base size to avoid text clipping
        val collapsedVideoWidth = 160.dp
        val expandedVideoWidth = screenWidthDp - (horizontalPadding * 2)  // Full width minus margins
        // Video width only changes during phase (b)
        val videoWidth = collapsedVideoWidth + (expandedVideoWidth - collapsedVideoWidth) * phaseBProgress
        val collapsedVideoHeight = collapsedVideoWidth * 9f / 16f
        val videoHeight = videoWidth * 9f / 16f

        // Video corner radius - fixed at 24dp to match camera preview
        val videoCornerRadius = 24.dp

        // Text size interpolation (shrinks during phase a, stays constant in phase b)
        val collapsedTextSize = 45.sp
        val expandedTextSize = 22.sp
        val textSize = androidx.compose.ui.unit.lerp(collapsedTextSize, expandedTextSize, phaseAProgress)
        
        // Text pager width - expands to full width during phase (b)
        val gapBetweenTextAndVideo = 16.dp
        val collapsedTextPagerWidth = screenWidthDp - (horizontalPadding * 2) - collapsedVideoWidth - gapBetweenTextAndVideo
        val expandedTextPagerWidth = screenWidthDp - (horizontalPadding * 2)
        val textPagerWidth = collapsedTextPagerWidth + (expandedTextPagerWidth - collapsedTextPagerWidth) * phaseBProgress

        // Top padding - shrinks from 48dp to 8dp during phase (a)
        val collapsedTopPadding = 48.dp
        val expandedTopPadding = 24.dp
        val topPadding = collapsedTopPadding + (expandedTopPadding - collapsedTopPadding) * phaseAProgress

        // "Sign the following:" label offset (slides up during phase a)
        val labelSlideDistance = 60.dp  // How far the label slides up
        val labelOffsetY = with(density) { (-labelSlideDistance * phaseAProgress).toPx() }
        val labelAlpha = 1f - phaseAProgress

        // Video vertical offset during phase (a): slides down to clear text
        // The video needs to move down enough to not clip the text
        val videoSlideDistance = 64.dp  // Adjust as needed
        val videoOffsetY = with(density) { (videoSlideDistance * phaseAProgress).toPx() }

        // Text bottom padding - animates from 12dp to 0dp during phase (a)
        val collapsedTextBottomPadding = 12.dp
        val expandedTextBottomPadding = 0.dp
        val textBottomPadding = collapsedTextBottomPadding + (expandedTextBottomPadding - collapsedTextBottomPadding) * phaseAProgress

        // Horizontal bias for text centering during phase (b)
        // 0f = left-aligned, 0.5f = centered
        val textHorizontalBias = 0.5f * phaseBProgress

        // Calculate the total height of the prompt area (accounts for video offset + video height)
        val promptAreaHeight = videoSlideDistance * phaseAProgress + videoHeight + videoBottomMargin

        Column(
            modifier = Modifier.fillMaxSize(),
            horizontalAlignment = Alignment.Start
        ) {
            // Prompt area: contains label, text prompt, and video using ConstraintLayout
            ConstraintLayout(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = horizontalPadding)
                    .padding(top = topPadding)
                    .height(promptAreaHeight)
            ) {
                val (textArea, videoArea) = createRefs()

                // Label + Text prompt (stacked vertically)
                // Horizontal bias animates from 0 (left) to 0.5 (center) during phase (b)
                Column(
                    modifier = Modifier
                        .constrainAs(textArea) {
                            top.linkTo(parent.top)
                            linkTo(
                                start = parent.start,
                                end = parent.end,
                                bias = textHorizontalBias
                            )
                            width = Dimension.wrapContent
                        }
                        .padding(bottom = textBottomPadding)
                ) {
                    // "Sign the following:" label - slides up and fades out during phase (a)
                    Text(
                        text = "Sign the following:",
                        style = MaterialTheme.typography.bodyLarge,
                        color = Color.White.copy(alpha = 0.7f * labelAlpha),
                        modifier = Modifier
                            .offset { androidx.compose.ui.unit.IntOffset(0, labelOffsetY.toInt()) }
                            .padding(bottom = 8.dp)
                    )

                    // Text prompt pager
                    HorizontalPager(
                        state = textPagerState,
                        userScrollEnabled = false,
                        modifier = Modifier.width(textPagerWidth)
                    ) { page ->
                        PromptDisplay(
                            prompt = samplePrompts[page].text,
                            modifier = Modifier,
                            fontSize = textSize,
                            phaseBProgress = phaseBProgress
                        )
                    }
                }

                // Video - top-right corner stays fixed
                // During phase (a): slides down (offset increases)
                // During phase (b): expands leftward and downward (width/height increase, position anchored top-right)
                Box(
                    modifier = Modifier
                        .constrainAs(videoArea) {
                            top.linkTo(parent.top)
                            end.linkTo(parent.end)
                        }
                        .offset { androidx.compose.ui.unit.IntOffset(0, videoOffsetY.toInt()) }
                        .width(videoWidth)
                        .aspectRatio(16f / 9f)
                        .clip(RoundedCornerShape(videoCornerRadius))
                ) {
                    HorizontalPager(
                        state = videoPagerState,
                        userScrollEnabled = false,
                        pageSpacing = 4.dp,
                        beyondViewportPageCount = 1,  // Keep adjacent pages loaded
                        modifier = Modifier.fillMaxSize()
                    ) { page ->
                        val prompt = samplePrompts[page]
                        videoPlayers[prompt.id]?.let { player ->
                            VideoPlayer(
                                videoView = player,
                                cornerRadius = videoCornerRadius,
                                modifier = Modifier.fillMaxSize()
                            )
                        }
                    }
                }
            }

            // Camera preview (persists across all pages)
            CameraPreview(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 8.dp)
                    .aspectRatio(3f / 4f),  // Portrait 4:3 (width:height = 3:4)
                timerContent = {
                    CountdownTimer(remainingTimeMs = remainingTimeMs)
                }
            )
        }
    }
}

@Composable
private fun PromptDisplay(
    prompt: String,
    modifier: Modifier = Modifier,
    fontSize: androidx.compose.ui.unit.TextUnit = 45.sp,
    phaseBProgress: Float = 0f
) {
    // Horizontal bias animates from 0 (left) to 0.5 (center) during phase (b)
    val textHorizontalBias = 0.5f * phaseBProgress

    ConstraintLayout(
        modifier = modifier.fillMaxWidth()
    ) {
        val textRef = createRef()

        Text(
            text = prompt,
            fontSize = fontSize,
            color = Color.White,
            fontWeight = FontWeight.Light,
            modifier = Modifier.constrainAs(textRef) {
                top.linkTo(parent.top)
                linkTo(
                    start = parent.start,
                    end = parent.end,
                    bias = textHorizontalBias
                )
                width = Dimension.wrapContent
            }
        )
    }
}

@Composable
private fun CountdownTimer(
    remainingTimeMs: Long,
    modifier: Modifier = Modifier
) {
    val minutes = (remainingTimeMs / 1000 / 60).toInt()
    val seconds = ((remainingTimeMs / 1000) % 60).toInt()
    // Don't pad minutes with leading zero to allow width to shrink
    val timeText = "%d:%02d".format(minutes, seconds)

    Box(
        modifier = modifier
            .clip(RoundedCornerShape(12.dp))
            .background(Color.Black.copy(alpha = 0.8f))
            .padding(horizontal = 16.dp, vertical = 8.dp)
    ) {
        AnimatedContent(
            targetState = timeText,
            transitionSpec = {
                (EnterTransition.None togetherWith ExitTransition.None)
                    .using(SizeTransform(clip = false, sizeAnimationSpec = { _, _ -> tween(200) }))
            },
            contentAlignment = Alignment.CenterEnd,
            label = "timer"
        ) { text ->
            Text(
                text = text,
                color = Color.White,
                fontSize = 20.sp,
                fontWeight = FontWeight.Medium,
                fontFamily = FontFamily.Monospace,
                textAlign = TextAlign.End,
            )
        }
    }
}

@Composable
private fun PermissionRequest(
    onRequestPermission: () -> Unit
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
            modifier = Modifier.padding(32.dp)
        ) {
            Text(
                text = "Camera Permission Required",
                style = MaterialTheme.typography.headlineSmall,
                color = Color.White,
                textAlign = TextAlign.Center
            )
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = "This app needs camera access to record sign language videos.",
                style = MaterialTheme.typography.bodyMedium,
                color = Color.White.copy(alpha = 0.8f),
                textAlign = TextAlign.Center
            )
            Spacer(modifier = Modifier.height(24.dp))
            Button(onClick = onRequestPermission) {
                Text("Grant Permission")
            }
        }
    }
}

@Composable
private fun PermissionRationale(
    onRequestPermission: () -> Unit
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
            modifier = Modifier.padding(32.dp)
        ) {
            Text(
                text = "Camera Access Needed",
                style = MaterialTheme.typography.headlineSmall,
                color = Color.White,
                textAlign = TextAlign.Center
            )
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = "The camera is essential for recording sign language videos. " +
                        "Please grant camera permission to continue.",
                style = MaterialTheme.typography.bodyMedium,
                color = Color.White.copy(alpha = 0.8f),
                textAlign = TextAlign.Center
            )
            Spacer(modifier = Modifier.height(24.dp))
            Button(onClick = onRequestPermission) {
                Text("Grant Permission")
            }
        }
    }
}
