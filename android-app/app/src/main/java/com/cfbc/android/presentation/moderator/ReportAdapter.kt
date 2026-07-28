package com.cfbc.android.presentation.moderator

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.cfbc.android.databinding.ItemReportCardBinding
import com.cfbc.app.presentation.model.ReportUiModel

/**
 * Adapter for pending comment reports with approve/reject actions.
 *
 * Layout: item_report_card.xml
 *
 * @param onApprove Callback when report is approved, receives report ID.
 * @param onReject Callback when report is rejected, receives report ID.
 */
class ReportAdapter(
    private val onApprove: (Int) -> Unit,
    private val onReject: (Int) -> Unit
) : RecyclerView.Adapter<ReportAdapter.ReportViewHolder>() {

    private var reports: List<ReportUiModel> = emptyList()
    private var processingId: Int? = null

    fun submitList(newReports: List<ReportUiModel>, processingReportId: Int? = null) {
        reports = newReports
        processingId = processingReportId
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ReportViewHolder {
        val binding = ItemReportCardBinding.inflate(
            LayoutInflater.from(parent.context), parent, false
        )
        return ReportViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ReportViewHolder, position: Int) {
        holder.bind(reports[position])
    }

    override fun getItemCount(): Int = reports.size

    inner class ReportViewHolder(
        private val binding: ItemReportCardBinding
    ) : RecyclerView.ViewHolder(binding.root) {

        fun bind(report: ReportUiModel) {
            binding.commentContent.text = report.comentarioContenido
            binding.commentAuthor.text = "Autor: ${report.comentarioAutor}"
            binding.reportedBy.text = "Reportado por: ${report.reportadoPorUsername}"
            binding.reasonText.text = "Motivo: ${report.motivo}"
            binding.reportDate.text = report.fechaReporte?.let { "Fecha: $it" } ?: ""

            val isProcessing = report.id == processingId
            binding.approveButton.isEnabled = !isProcessing
            binding.rejectButton.isEnabled = !isProcessing
            binding.processingIndicator.visibility = if (isProcessing) View.VISIBLE else View.GONE

            binding.approveButton.setOnClickListener { onApprove(report.id) }
            binding.rejectButton.setOnClickListener { onReject(report.id) }
        }
    }
}
