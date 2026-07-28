package com.cfbc.android.presentation.adapter

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.RecyclerView
import com.cfbc.android.R
import com.cfbc.android.databinding.ItemEnrollmentCardBinding
import com.cfbc.app.presentation.model.EnrollmentUiModel

/**
 * RecyclerView adapter for displaying enrollment cards.
 *
 * Used by: ProfileFragment
 * Layout: item_enrollment_card.xml
 */
class EnrollmentAdapter : RecyclerView.Adapter<EnrollmentAdapter.EnrollmentViewHolder>() {

    private var enrollments: List<EnrollmentUiModel> = emptyList()

    fun submitList(newEnrollments: List<EnrollmentUiModel>) {
        enrollments = newEnrollments
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): EnrollmentViewHolder {
        val binding = ItemEnrollmentCardBinding.inflate(
            LayoutInflater.from(parent.context), parent, false
        )
        return EnrollmentViewHolder(binding)
    }

    override fun onBindViewHolder(holder: EnrollmentViewHolder, position: Int) {
        holder.bind(enrollments[position])
    }

    override fun getItemCount(): Int = enrollments.size

    inner class EnrollmentViewHolder(
        private val binding: ItemEnrollmentCardBinding
    ) : RecyclerView.ViewHolder(binding.root) {

        fun bind(enrollment: EnrollmentUiModel) {
            binding.courseName.text = enrollment.courseName
            binding.courseType.text = buildString {
                append(enrollment.courseAreaDisplay)
                append(" · ${enrollment.courseTipoDisplay}")
            }
            binding.teacherName.text = enrollment.courseTeacherName
            binding.matriculaDate.text = enrollment.fechaMatricula
                ?.let { "Matriculado: $it" } ?: ""

            // Status badge color using app-defined status colors
            val bgColor = when (enrollment.estado) {
                "P" -> R.color.status_activo
                "A" -> R.color.status_aprobado
                "B" -> R.color.status_baja
                "R" -> R.color.status_retirado
                else -> R.color.status_archivado
            }
            binding.statusBadge.setChipBackgroundColorResource(bgColor)
            binding.statusBadge.setTextColor(
                ContextCompat.getColor(binding.root.context, android.R.color.white)
            )
            binding.statusBadge.text = enrollment.estadoDisplay
        }
    }
}
