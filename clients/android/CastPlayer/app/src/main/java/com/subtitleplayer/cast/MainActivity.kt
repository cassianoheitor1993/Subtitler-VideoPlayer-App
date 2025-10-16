package com.subtitleplayer.cast

import android.content.pm.ActivityInfo
import android.content.res.Configuration
import android.net.Uri
import android.os.Bundle
import android.view.View
import android.view.WindowManager
import android.view.animation.AnimationUtils
import android.widget.ImageButton
import android.widget.TextView
import androidx.activity.ComponentActivity
import androidx.activity.viewModels
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import androidx.lifecycle.lifecycleScope
import androidx.media3.common.MediaItem
import androidx.media3.common.MimeTypes
import androidx.media3.common.PlaybackException
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.PlayerView
import com.google.android.material.bottomsheet.BottomSheetDialog
import com.google.android.material.button.MaterialButton
import com.google.android.material.card.MaterialCardView
import com.google.android.material.floatingactionbutton.FloatingActionButton
import com.google.android.material.textfield.TextInputEditText
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MainActivity : ComponentActivity() {

    private lateinit var playerView: PlayerView
    private var player: ExoPlayer? = null
    private lateinit var playButton: MaterialButton
    private lateinit var stopButton: MaterialButton
    private lateinit var statusLabel: TextView
    private lateinit var urlInput: TextInputEditText
    private lateinit var urlInputCard: MaterialCardView
    private lateinit var fabSubtitles: FloatingActionButton
    private lateinit var fabAudio: FloatingActionButton
    
    private var isFullscreen = false
    private val viewModel: PlayerViewModel by viewModels()
    
    private val playerListener = object : Player.Listener {
        override fun onPlayerError(error: PlaybackException) {
            statusLabel.text = getString(R.string.status_error, error.errorCodeName)
        }
        
        override fun onPlaybackStateChanged(playbackState: Int) {
            when (playbackState) {
                Player.STATE_BUFFERING -> statusLabel.text = getString(R.string.status_loading)
                Player.STATE_READY -> statusLabel.text = getString(R.string.status_playing)
                Player.STATE_ENDED -> statusLabel.text = getString(R.string.status_stopped)
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Enable edge-to-edge display
        WindowCompat.setDecorFitsSystemWindows(window, false)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        
        setContentView(R.layout.activity_main)

        // Initialize views
        playerView = findViewById(R.id.playerView)
        playButton = findViewById(R.id.playButton)
        stopButton = findViewById(R.id.stopButton)
        statusLabel = findViewById(R.id.statusLabel)
        urlInput = findViewById(R.id.urlInput)
        urlInputCard = findViewById(R.id.url_input_card)
        fabSubtitles = findViewById(R.id.fab_subtitles)
        fabAudio = findViewById(R.id.fab_audio)

        urlInput.setText(viewModel.streamUrl)

        // Setup button listeners
        playButton.setOnClickListener {
            val normalized = normalizeUrl(urlInput.text?.toString().orEmpty())
            if (normalized.isNotEmpty()) {
                urlInput.setText(normalized)
                viewModel.streamUrl = normalized
                startPlayback(normalized)
                
                // Hide URL card with animation
                val fadeOut = AnimationUtils.loadAnimation(this, R.anim.slide_down)
                urlInputCard.startAnimation(fadeOut)
                urlInputCard.visibility = View.GONE
            }
        }

        stopButton.setOnClickListener {
            stopPlayback()
        }
        
        // Setup FAB listeners
        fabSubtitles.setOnClickListener {
            showSubtitleSettings()
        }
        
        fabAudio.setOnClickListener {
            showAudioTrackSelection()
        }
        
        // Setup custom player controls
        setupPlayerControls()
        
        // Handle orientation changes
        handleOrientation()
    }

    override fun onStart() {
        super.onStart()
        if (player == null) {
            initPlayer()
        }
    }

    override fun onStop() {
        super.onStop()
        releasePlayer()
    }
    
    override fun onConfigurationChanged(newConfig: Configuration) {
        super.onConfigurationChanged(newConfig)
        handleOrientation()
    }
    
    private fun handleOrientation() {
        val isLandscape = resources.configuration.orientation == Configuration.ORIENTATION_LANDSCAPE
        
        if (isLandscape) {
            enterFullscreen()
        } else {
            exitFullscreen()
        }
    }
    
    private fun enterFullscreen() {
        isFullscreen = true
        
        // Hide system UI
        val windowInsetsController = WindowCompat.getInsetsController(window, window.decorView)
        windowInsetsController.apply {
            systemBarsBehavior = WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
            hide(WindowInsetsCompat.Type.systemBars())
        }
        
        // Hide URL input and FABs in landscape
        if (resources.configuration.orientation == Configuration.ORIENTATION_LANDSCAPE) {
            fabSubtitles.visibility = View.GONE
            fabAudio.visibility = View.GONE
        }
    }
    
    private fun exitFullscreen() {
        isFullscreen = false
        
        // Show system UI
        val windowInsetsController = WindowCompat.getInsetsController(window, window.decorView)
        windowInsetsController.show(WindowInsetsCompat.Type.systemBars())
        
        // Show URL input and FABs in portrait
        if (resources.configuration.orientation == Configuration.ORIENTATION_PORTRAIT) {
            fabSubtitles.visibility = View.VISIBLE
            fabAudio.visibility = View.VISIBLE
        }
    }
    
    private fun setupPlayerControls() {
        // Find custom controls in player view
        val subtitleButton = playerView.findViewById<ImageButton>(R.id.subtitle_button)
        val audioButton = playerView.findViewById<ImageButton>(R.id.audio_button)
        val fullscreenButton = playerView.findViewById<ImageButton>(R.id.exo_fullscreen)
        val backButton = playerView.findViewById<ImageButton>(R.id.exo_back)
        
        subtitleButton?.setOnClickListener {
            showSubtitleSettings()
        }
        
        audioButton?.setOnClickListener {
            showAudioTrackSelection()
        }
        
        fullscreenButton?.setOnClickListener {
            toggleFullscreen()
        }
        
        backButton?.setOnClickListener {
            if (isFullscreen) {
                exitFullscreen()
                requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_PORTRAIT
            } else {
                finish()
            }
        }
    }
    
    private fun toggleFullscreen() {
        if (isFullscreen) {
            requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_PORTRAIT
        } else {
            requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE
        }
    }
    
    private fun showSubtitleSettings() {
        val dialog = BottomSheetDialog(this)
        val view = layoutInflater.inflate(R.layout.bottom_sheet_subtitles, null)
        dialog.setContentView(view)
        
        val exoPlayer = player ?: return
        val subtitleToggle = view.findViewById<com.google.android.material.switchmaterial.SwitchMaterial>(R.id.subtitle_toggle)
        val subtitleList = view.findViewById<androidx.recyclerview.widget.RecyclerView>(R.id.subtitle_list)
        val noSubtitlesMessage = view.findViewById<TextView>(R.id.no_subtitles_message)
        
        // Get available subtitle tracks
        val tracks = exoPlayer.currentTracks
        val subtitleTracks = mutableListOf<TrackInfo>()
        
        tracks.groups.forEachIndexed { groupIndex, trackGroup ->
            if (trackGroup.type == androidx.media3.common.C.TRACK_TYPE_TEXT) {
                for (i in 0 until trackGroup.length) {
                    val format = trackGroup.getTrackFormat(i)
                    val language = format.language ?: "Unknown"
                    val label = format.label ?: language
                    val isSelected = trackGroup.isTrackSelected(i)
                    
                    subtitleTracks.add(
                        TrackInfo(
                            name = label,
                            info = "Subtitle • ${format.sampleMimeType ?: "Unknown"}",
                            index = groupIndex,
                            isSelected = isSelected
                        )
                    )
                }
            }
        }
        
        if (subtitleTracks.isEmpty()) {
            noSubtitlesMessage?.visibility = View.VISIBLE
            subtitleList?.visibility = View.GONE
        } else {
            noSubtitlesMessage?.visibility = View.GONE
            subtitleList?.visibility = View.VISIBLE
            
            subtitleList?.layoutManager = androidx.recyclerview.widget.LinearLayoutManager(this)
            subtitleList?.adapter = TrackAdapter(subtitleTracks) { trackIndex ->
                // Handle subtitle track selection
                dialog.dismiss()
            }
        }
        
        subtitleToggle?.setOnCheckedChangeListener { _, isChecked ->
            // TODO: Enable/disable subtitles
        }
        
        dialog.show()
    }
    
    private fun showAudioTrackSelection() {
        val dialog = BottomSheetDialog(this)
        val view = layoutInflater.inflate(R.layout.bottom_sheet_audio, null)
        dialog.setContentView(view)
        
        val exoPlayer = player ?: return
        val audioTrackList = view.findViewById<androidx.recyclerview.widget.RecyclerView>(R.id.audio_track_list)
        val noAudioTracksMessage = view.findViewById<TextView>(R.id.no_audio_tracks_message)
        
        // Get available audio tracks
        val tracks = exoPlayer.currentTracks
        val audioTracks = mutableListOf<TrackInfo>()
        
        tracks.groups.forEachIndexed { groupIndex, trackGroup ->
            if (trackGroup.type == androidx.media3.common.C.TRACK_TYPE_AUDIO) {
                for (i in 0 until trackGroup.length) {
                    val format = trackGroup.getTrackFormat(i)
                    val language = format.language ?: "Unknown"
                    val label = format.label ?: language
                    val codec = format.codecs ?: "Unknown"
                    val isSelected = trackGroup.isTrackSelected(i)
                    
                    audioTracks.add(
                        TrackInfo(
                            name = label,
                            info = "Audio • $codec • ${format.channelCount}ch",
                            index = groupIndex,
                            isSelected = isSelected
                        )
                    )
                }
            }
        }
        
        if (audioTracks.isEmpty()) {
            noAudioTracksMessage?.visibility = View.VISIBLE
            audioTrackList?.visibility = View.GONE
        } else {
            noAudioTracksMessage?.visibility = View.GONE
            audioTrackList?.visibility = View.VISIBLE
            
            audioTrackList?.layoutManager = androidx.recyclerview.widget.LinearLayoutManager(this)
            audioTrackList?.adapter = TrackAdapter(audioTracks) { trackIndex ->
                // Handle audio track selection
                dialog.dismiss()
            }
        }
        
        dialog.show()
    }

    private fun initPlayer() {
        player = ExoPlayer.Builder(this).build().also { exoPlayer ->
            exoPlayer.addListener(playerListener)
            playerView.player = exoPlayer
        }
    }

    private fun startPlayback(url: String) {
        val exoPlayer = player ?: run {
            initPlayer()
            player!!
        }

        lifecycleScope.launch {
            statusLabel.text = getString(R.string.status_loading)
            withContext(Dispatchers.Main) {
                exoPlayer.setMediaItem(buildMediaItem(url))
                exoPlayer.prepare()
                exoPlayer.playWhenReady = true
                statusLabel.text = getString(R.string.status_playing)
            }
        }
    }

    private fun stopPlayback() {
        player?.run {
            stop()
            clearMediaItems()
        }
        statusLabel.text = getString(R.string.status_stopped)
        
        // Show URL card with animation
        if (resources.configuration.orientation == Configuration.ORIENTATION_PORTRAIT) {
            val slideUp = AnimationUtils.loadAnimation(this, R.anim.slide_up)
            urlInputCard.visibility = View.VISIBLE
            urlInputCard.startAnimation(slideUp)
        }
    }

    private fun releasePlayer() {
        player?.removeListener(playerListener)
        player?.release()
        player = null
    }

    private fun normalizeUrl(raw: String): String {
        val trimmed = raw.trim()
        if (trimmed.isEmpty()) {
            return ""
        }

        val uri = runCatching { Uri.parse(trimmed) }.getOrNull()
        if (uri?.host == "0.0.0.0") {
            val fallback = runCatching { Uri.parse(viewModel.streamUrl) }.getOrNull()
            if (fallback?.host != null && fallback.host != "0.0.0.0") {
                val authority = if (fallback.port != -1) "${fallback.host}:${fallback.port}" else fallback.host
                return uri.buildUpon().encodedAuthority(authority).build().toString()
            }
        }

        return trimmed
    }

    private fun buildMediaItem(url: String): MediaItem {
        val builder = MediaItem.Builder().setUri(url)
        if (url.contains(".m3u8", ignoreCase = true)) {
            builder.setMimeType(MimeTypes.APPLICATION_M3U8)
        }
        return builder.build()
    }
}
