package com.cfbc.android.presentation.adapter

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import coil.load
import com.cfbc.android.databinding.ItemCourseCardBinding
import com.cfbc.app.presentation.model.CourseUiModel

/**
 * RecyclerView adapter for displaying course cards.
 *
 * Used by: CoursesListFragment, HomeFragment (courses section)
 * Layout: item_course_card.xml
 *
 * @param onCourseClick Callback when a course card is tapped, receives course ID.
 */
class CourseCardAdapter(
    private val onCourseClick: (Int) -> Unit
) : RecyclerView.Adapter<CourseCardAdapter.CourseViewHolder>() {

    private var courses: List<CourseUiModel> = emptyList()

    fun submitList(newCourses: List<CourseUiModel>) {
        courses = newCourses
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): CourseViewHolder {
        val binding = ItemCourseCardBinding.inflate(
            LayoutInflater.from(parent.context), parent, false
        )
        return CourseViewHolder(binding)
    }

    override fun onBindViewHolder(holder: CourseViewHolder, position: Int) {
        holder.bind(courses[position])
    }

    override fun getItemCount(): Int = courses.size

    inner class CourseViewHolder(
        private val binding: ItemCourseCardBinding
    ) : RecyclerView.ViewHolder(binding.root) {

        fun bind(course: CourseUiModel) {
            binding.courseName.text = course.name
            binding.teacherName.text = course.teacherName
            binding.startDate.text = course.startDate ?: course.enrollmentDeadline ?: ""

            // Area badge
            binding.areaBadge.text = course.areaDisplay

            // Load image
            course.imageUrl?.let { url ->
                binding.courseImage.load(url) {
                    placeholder(android.R.drawable.ic_menu_gallery)
                    error(android.R.drawable.ic_menu_gallery)
                    crossfade(true)
                }
            }

            // Click listener
            binding.root.setOnClickListener {
                onCourseClick(course.id)
            }
        }
    }
}
