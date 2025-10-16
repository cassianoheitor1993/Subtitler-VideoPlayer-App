package com.subtitleplayer.cast

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.card.MaterialCardView

data class TrackInfo(
    val name: String,
    val info: String,
    val index: Int,
    val isSelected: Boolean = false
)

class TrackAdapter(
    private val tracks: List<TrackInfo>,
    private val onTrackSelected: (Int) -> Unit
) : RecyclerView.Adapter<TrackAdapter.TrackViewHolder>() {

    class TrackViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val card: MaterialCardView = view.findViewById(R.id.track_item_card)
        val trackName: TextView = view.findViewById(R.id.track_name)
        val trackInfo: TextView = view.findViewById(R.id.track_info)
        val selectedIcon: ImageView = view.findViewById(R.id.track_selected_icon)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): TrackViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_track, parent, false)
        return TrackViewHolder(view)
    }

    override fun onBindViewHolder(holder: TrackViewHolder, position: Int) {
        val track = tracks[position]
        
        holder.trackName.text = track.name
        holder.trackInfo.text = track.info
        holder.selectedIcon.visibility = if (track.isSelected) View.VISIBLE else View.GONE
        
        holder.card.setOnClickListener {
            onTrackSelected(track.index)
        }
    }

    override fun getItemCount() = tracks.size
}
