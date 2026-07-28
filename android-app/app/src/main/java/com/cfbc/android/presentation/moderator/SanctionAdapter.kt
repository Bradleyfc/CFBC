package com.cfbc.android.presentation.moderator

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.RecyclerView
import com.cfbc.android.R
import com.cfbc.android.databinding.ItemSanctionCardBinding
import com.cfbc.app.presentation.model.SanctionUiModel

/**
 * Adapter for active user sanctions (read-only).
 *
 * Layout: item_sanction_card.xml
 */
class SanctionAdapter : RecyclerView.Adapter<SanctionAdapter.SanctionViewHolder>() {

    private var sanctions: List<SanctionUiModel> = emptyList()

    fun submitList(newSanctions: List<SanctionUiModel>) {
        sanctions = newSanctions
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): SanctionViewHolder {
        val binding = ItemSanctionCardBinding.inflate(
            LayoutInflater.from(parent.context), parent, false
        )
        return SanctionViewHolder(binding)
    }

    override fun onBindViewHolder(holder: SanctionViewHolder, position: Int) {
        holder.bind(sanctions[position])
    }

    override fun getItemCount(): Int = sanctions.size

    inner class SanctionViewHolder(
        private val binding: ItemSanctionCardBinding
    ) : RecyclerView.ViewHolder(binding.root) {

        fun bind(sanction: SanctionUiModel) {
            binding.userName.text = sanction.usuarioUsername
            binding.sanctionType.text = sanction.tipoSancion
            binding.reasonText.text = sanction.motivo
            binding.dateRange.text = buildString {
                sanction.fechaInicio?.let { append("Inicio: $it") }
                sanction.fechaFin?.let { append("\nFin: $it") }
            }

            // Color based on active status
            val color = if (sanction.activa) {
                ContextCompat.getColor(binding.root.context, android.R.color.holo_red_dark)
            } else {
                ContextCompat.getColor(binding.root.context, android.R.color.darker_gray)
            }
            binding.statusIndicator.setBackgroundColor(color)
        }
    }
}
