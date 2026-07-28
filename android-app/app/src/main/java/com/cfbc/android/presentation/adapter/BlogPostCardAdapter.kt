package com.cfbc.android.presentation.adapter

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import coil.load
import com.cfbc.android.databinding.ItemBlogPostCardBinding
import com.cfbc.app.presentation.model.BlogPostListItemUiModel

/**
 * RecyclerView adapter for displaying blog post cards.
 *
 * Used by: BlogListFragment, HomeFragment (news section)
 * Layout: item_blog_post_card.xml
 *
 * @param onPostClick Callback when a post card is tapped, receives post slug.
 */
class BlogPostCardAdapter(
    private val onPostClick: (String) -> Unit
) : RecyclerView.Adapter<BlogPostCardAdapter.BlogPostViewHolder>() {

    private var posts: List<BlogPostListItemUiModel> = emptyList()

    fun submitList(newPosts: List<BlogPostListItemUiModel>) {
        posts = newPosts
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): BlogPostViewHolder {
        val binding = ItemBlogPostCardBinding.inflate(
            LayoutInflater.from(parent.context), parent, false
        )
        return BlogPostViewHolder(binding)
    }

    override fun onBindViewHolder(holder: BlogPostViewHolder, position: Int) {
        holder.bind(posts[position])
    }

    override fun getItemCount(): Int = posts.size

    inner class BlogPostViewHolder(
        private val binding: ItemBlogPostCardBinding
    ) : RecyclerView.ViewHolder(binding.root) {

        fun bind(post: BlogPostListItemUiModel) {
            binding.postTitle.text = post.titulo
            binding.postSummary.text = post.resumen
            binding.postMeta.text = buildString {
                append(post.autorUsername)
                post.fechaPublicacion?.let {
                    append(" · $it")
                }
            }

            // Featured badge
            binding.featuredBadge.visibility =
                if (post.destacada) android.view.View.VISIBLE else android.view.View.GONE

            // Load thumbnail
            post.imagenPrincipalUrl?.let { url ->
                binding.postImage.load(url) {
                    placeholder(android.R.drawable.ic_menu_gallery)
                    error(android.R.drawable.ic_menu_gallery)
                    crossfade(true)
                }
            }

            // Click listener
            binding.root.setOnClickListener {
                onPostClick(post.slug)
            }
        }
    }
}
