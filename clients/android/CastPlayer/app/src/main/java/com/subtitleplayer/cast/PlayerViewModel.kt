package com.subtitleplayer.cast

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class PlayerViewModel(application: Application) : AndroidViewModel(application) {

    private val prefs = application.getSharedPreferences("cast_prefs", Application.MODE_PRIVATE)

    var streamUrl: String = prefs.getString(KEY_STREAM_URL, DEFAULT_URL) ?: DEFAULT_URL
        set(value) {
            field = value
            viewModelScope.launch {
                withContext(Dispatchers.IO) {
                    prefs.edit().putString(KEY_STREAM_URL, value).apply()
                }
            }
        }

    companion object {
        private const val KEY_STREAM_URL = "stream_url"
        private const val DEFAULT_URL = "http://10.0.0.59:8080/live.ts"
    }
}
