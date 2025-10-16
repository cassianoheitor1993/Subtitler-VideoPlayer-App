package com.subtitleplayer.cast

import android.net.Uri
import android.os.Bundle
import android.widget.TextView
import androidx.activity.ComponentActivity
import androidx.activity.viewModels
import androidx.lifecycle.lifecycleScope
import androidx.media3.common.MediaItem
import androidx.media3.common.MimeTypes
import androidx.media3.common.PlaybackException
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.PlayerView
import com.google.android.material.button.MaterialButton
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

    private val viewModel: PlayerViewModel by viewModels()
    private val playerListener = object : Player.Listener {
        override fun onPlayerError(error: PlaybackException) {
            statusLabel.text = getString(R.string.status_error, error.errorCodeName)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        playerView = findViewById(R.id.playerView)
        playButton = findViewById(R.id.playButton)
        stopButton = findViewById(R.id.stopButton)
        statusLabel = findViewById(R.id.statusLabel)
        urlInput = findViewById(R.id.urlInput)

        urlInput.setText(viewModel.streamUrl)

        playButton.setOnClickListener {
            val normalized = normalizeUrl(urlInput.text?.toString().orEmpty())
            if (normalized.isNotEmpty()) {
                urlInput.setText(normalized)
                viewModel.streamUrl = normalized
                startPlayback(normalized)
            }
        }

        stopButton.setOnClickListener {
            stopPlayback()
        }
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
