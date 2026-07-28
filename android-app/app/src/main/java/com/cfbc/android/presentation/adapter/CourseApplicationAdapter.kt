package com.cfbc.android.presentation.adapter

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.RecyclerView
import com.cfbc.android.databinding.ItemApplicationCardBinding
import com.cfbc.app.presentation.model.CourseApplicationUiModel

/**
 * RecyclerView adapter for displaying course application cards.
 *
 * Used by: ApplicationListFragment
 * Layout: item_application_card.xml
 *
 * @param onCancelClick Callback when cancel button is tapped, receives application ID.
 */
class CourseApplicationAdapter(
    private val onCancelClick: (Int) -> Unit
) : RecyclerView.Adapter<CourseApplicationAdapter.ApplicationViewHolder>() {

    private var applications: List<CourseApplicationUiModel> = emptyList()

    fun submitList(newApplications: List<CourseApplicationUiModel>) {
        applications = newApplications
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ApplicationViewHolder {
        val binding = ItemApplicationCardBinding.inflate(
            LayoutInflater.from(parent.context), parent, false
        )
        return ApplicationViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ApplicationViewHolder, position: Int) {
        holder.bind(applications[position])
    }

    override fun getItemCount(): Int = applications.size

    inner class ApplicationViewHolder(
        private val binding: ItemApplicationCardBinding
    ) : RecyclerView.ViewHolder(binding.root) {

        fun bind(application: CourseApplicationUiModel) {
            binding.courseName.text = application.courseName
            binding.teacherName.text = application.courseTeacherName ?: ""
            binding.submissionDate.text = application.submissionDate
                ?.let { "Solicitado: $it" } ?: ""

            // Status badge color using app-defined status colors
            val bgColor = when (application.status) {
                "pending" -> R.color.status_pending
                "approved" -> R.color.status_approved
                "rejected" -> R.color.status_rejected
                else -> R.color.status_archivado
            }
            binding.statusBadge.setChipBackgroundColorResource(bgColor)
            binding.statusBadge.setTextColor(
                ContextCompat.getColor(binding.root.context, android.R.color.white)
            )
            binding.statusBadge.text = application.statusDisplay

            // Cancel button only for pending applications
            if (application.status == "pending") {
                binding.cancelButton.visibility = View.VISIBLE
                binding.cancelButton.setOnClickListener {
                    onCancelClick(application.id)
                }
            } else {
                binding.cancelButton.visibility = View.GONE
            }
        }
    }
}
