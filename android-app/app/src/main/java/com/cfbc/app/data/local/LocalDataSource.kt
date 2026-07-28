package com.cfbc.app.data.local

import com.cfbc.app.data.local.dao.*
import com.cfbc.app.data.local.entity.*
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Local Data Source — wraps all Room DAO operations with caching logic.
 *
 * Handles:
 * - Reading cached data as Flow for reactive UI updates
 * - Writing fetched data to local cache
 * - LRU eviction for blog posts (max 50 posts or 30 days old)
 * - Clearing cache on logout
 *
 * Requirements: 12.1, 12.2, 12.6, 12.7
 */
@Singleton
class LocalDataSource @Inject constructor(
    private val blogDao: BlogDao,
    private val categoryDao: CategoryDao,
    private val courseDao: CourseDao,
    private val courseApplicationDao: CourseApplicationDao,
    private val studentDao: StudentDao
) {

    // =========================================================================
    // Blog Posts
    // =========================================================================

    /** Flow of all cached blog posts (newest first). */
    fun observeBlogPosts(): Flow<List<BlogPostEntity>> = blogDao.getAllPosts()

    /** Flow of cached blog posts with limit. */
    fun observeCachedPosts(limit: Int = 50): Flow<List<BlogPostEntity>> =
        blogDao.getCachedPosts(limit)

    /** Get a single cached post by slug. */
    suspend fun getCachedPostBySlug(slug: String): BlogPostEntity? =
        blogDao.getPostBySlug(slug)

    /** Get a single cached post by ID. */
    suspend fun getCachedPostById(id: Int): BlogPostEntity? =
        blogDao.getPostById(id)

    /** Cache blog posts (insert/replace). */
    suspend fun cacheBlogPosts(posts: List<BlogPostEntity>) {
        blogDao.insertPosts(posts)
    }

    /** Cache a single blog post. */
    suspend fun cacheBlogPost(post: BlogPostEntity) {
        blogDao.insertPost(post)
    }

    /** Update lastViewed timestamp (for LRU tracking). */
    suspend fun updatePostLastViewed(postId: Int, lastViewed: Long) {
        blogDao.updateLastViewed(postId, lastViewed)
    }

    /** Run LRU eviction: keep at most 50 most recently viewed posts. */
    suspend fun evictOldPostsByCount(limit: Int = 50) {
        blogDao.evictOldPostsByCount(limit)
    }

    /** Run age-based eviction: remove posts older than 30 days. */
    suspend fun evictOldPostsByAge() {
        blogDao.evictOldPostsByAge()
    }

    /** Search cached posts by title or content. */
    fun searchCachedPosts(query: String): Flow<List<BlogPostEntity>> =
        blogDao.searchPosts(query)

    /** Get cached posts by category. */
    fun observePostsByCategory(categoryId: Int): Flow<List<BlogPostEntity>> =
        blogDao.getPostsByCategory(categoryId)

    // =========================================================================
    // Categories
    // =========================================================================

    /** Flow of all cached categories. */
    fun observeCategories(): Flow<List<CategoryEntity>> = categoryDao.getAllCategories()

    /** Get a cached category by ID. */
    suspend fun getCachedCategoryById(id: Int): CategoryEntity? =
        categoryDao.getCategoryById(id)

    /** Get a cached category by slug. */
    suspend fun getCachedCategoryBySlug(slug: String): CategoryEntity? =
        categoryDao.getCategoryBySlug(slug)

    /** Cache categories. */
    suspend fun cacheCategories(categories: List<CategoryEntity>) {
        categoryDao.insertCategories(categories)
    }

    /** Cache a single category. */
    suspend fun cacheCategory(category: CategoryEntity) {
        categoryDao.insertCategory(category)
    }

    // =========================================================================
    // Courses
    // =========================================================================

    /** Flow of all cached courses. */
    fun observeCourses(): Flow<List<CourseEntity>> = courseDao.getAllCourses()

    /** Flow of available courses (statusAvailable = true). */
    fun observeAvailableCourses(limit: Int = 50): Flow<List<CourseEntity>> =
        courseDao.getAvailableCourses(limit)

    /** Get a cached course by ID. */
    suspend fun getCachedCourseById(courseId: Int): CourseEntity? =
        courseDao.getCourseById(courseId)

    /** Get cached courses by area. */
    fun observeCoursesByArea(area: String): Flow<List<CourseEntity>> =
        courseDao.getCoursesByArea(area)

    /** Get cached courses by tipo. */
    fun observeCoursesByTipo(tipo: String): Flow<List<CourseEntity>> =
        courseDao.getCoursesByTipo(tipo)

    /** Cache courses. */
    suspend fun cacheCourses(courses: List<CourseEntity>) {
        courseDao.insertCourses(courses)
    }

    /** Cache a single course. */
    suspend fun cacheCourse(course: CourseEntity) {
        courseDao.insertCourse(course)
    }

    // =========================================================================
    // Course Applications
    // =========================================================================

    /** Flow of all cached applications. */
    fun observeApplications(): Flow<List<CourseApplicationEntity>> =
        courseApplicationDao.getAllApplications()

    /** Flow of pending applications. */
    fun observePendingApplications(): Flow<List<CourseApplicationEntity>> =
        courseApplicationDao.getPendingApplications()

    /** Get a cached application by ID. */
    suspend fun getCachedApplicationById(id: Int): CourseApplicationEntity? =
        courseApplicationDao.getApplicationById(id)

    /** Get cached applications for a course. */
    fun observeApplicationsByCourse(courseId: Int): Flow<List<CourseApplicationEntity>> =
        courseApplicationDao.getApplicationsByCourse(courseId)

    /** Cache applications. */
    suspend fun cacheApplications(applications: List<CourseApplicationEntity>) {
        courseApplicationDao.insertApplications(applications)
    }

    /** Cache a single application. */
    suspend fun cacheApplication(application: CourseApplicationEntity) {
        courseApplicationDao.insertApplication(application)
    }

    /** Delete a cached application (e.g. after cancelling). */
    suspend fun deleteCachedApplication(applicationId: Int) {
        courseApplicationDao.deleteApplicationById(applicationId)
    }

    // =========================================================================
    // Student Profile
    // =========================================================================

    /** Observe cached student profile. */
    fun observeProfile(username: String): Flow<StudentProfileEntity?> =
        studentDao.getProfile(username)

    /** Get any cached profile (for single-user scenario). */
    suspend fun getAnyCachedProfile(): StudentProfileEntity? =
        studentDao.getAnyProfile()

    /** Cache student profile. */
    suspend fun cacheProfile(profile: StudentProfileEntity) {
        studentDao.insertProfile(profile)
    }

    // =========================================================================
    // Enrollments
    // =========================================================================

    /** Flow of all cached enrollments. */
    fun observeEnrollments(): Flow<List<EnrollmentEntity>> =
        studentDao.getAllEnrollments()

    /** Flow of active cached enrollments. */
    fun observeActiveEnrollments(): Flow<List<EnrollmentEntity>> =
        studentDao.getActiveEnrollments()

    /** Get a cached enrollment by ID. */
    suspend fun getCachedEnrollmentById(id: Int): EnrollmentEntity? =
        studentDao.getEnrollmentById(id)

    /** Observe cached enrollments for a course. */
    fun observeEnrollmentsByCourse(courseId: Int): Flow<List<EnrollmentEntity>> =
        studentDao.getEnrollmentsByCourse(courseId)

    /** Cache enrollments. */
    suspend fun cacheEnrollments(enrollments: List<EnrollmentEntity>) {
        studentDao.insertEnrollments(enrollments)
    }

    /** Cache a single enrollment. */
    suspend fun cacheEnrollment(enrollment: EnrollmentEntity) {
        studentDao.insertEnrollment(enrollment)
    }

    // =========================================================================
    // Cache Management
    // =========================================================================

    /** Clear all cached blog data (posts + categories) — used on logout. */
    suspend fun clearBlogCache() {
        blogDao.deleteAll()
        categoryDao.deleteAll()
    }

    /** Clear all cached course data (courses + applications) — used on logout. */
    suspend fun clearCourseCache() {
        courseDao.deleteAll()
        courseApplicationDao.deleteAll()
    }

    /** Clear all cached user data (profile + enrollments) — used on logout. */
    suspend fun clearUserCache() {
        studentDao.deleteProfile()
        studentDao.deleteAllEnrollments()
    }

    /** Clear ALL cached data — used on full logout. */
    suspend fun clearAll() {
        clearBlogCache()
        clearCourseCache()
        clearUserCache()
    }
}
