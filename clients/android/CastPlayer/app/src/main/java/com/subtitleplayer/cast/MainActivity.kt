package com.subtitleplayer.cast

import android.os.Bundle
import android.widget.TextView
import androidx.activity.ComponentActivity
import androidx.activity.viewModels
import androidx.lifecycle.lifecycleScope
import androidx.media3.common.MediaItem
import androidx.media3.common.util.UnstableApi
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
            val url = urlInput.text?.toString().orEmpty().trim()
            if (url.isNotEmpty()) {
                viewModel.streamUrl = url
                startPlayback(url)
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
            playerView.player = exoPlayer
        }
    }

    private fun startPlayback(url: String) {
        val exoPlayer = player ?: run {
            initPlayer()
            player!!
        }

        lifecycleScope.launch {
            statusLabel.text = getString(R.string.status_ready)
            withContext(Dispatchers.Main) {
                exoPlayer.setMediaItem(MediaItem.fromUri(url))
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
        player?.release()
        player = null
    }
}
