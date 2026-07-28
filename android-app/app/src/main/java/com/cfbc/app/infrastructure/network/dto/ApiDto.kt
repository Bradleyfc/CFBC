package com.cfbc.app.infrastructure.network.dto

import com.google.gson.annotations.SerializedName

// =============================================================================
// Generic Paginated Response
// DRF PageNumberPagination format: { count, next, previous, results }
// =============================================================================

data class PaginatedResponse<T>(
    val count: Int,
    val next: String?,
    val previous: String?,
    val results: List<T>
)

// =============================================================================
// Generic Error / Detail Response
// =============================================================================

data class DetailResponse(
    val detail: String? = null
)

// =============================================================================
// Auth Endpoints
// POST /api/v1/auth/login/
// POST /api/v1/auth/logout/
// =============================================================================

data class LoginRequest(
    val username: String,
    val password: String
)

data class LoginResponse(
    val token: String,
    val username: String,
    val groups: List<String>
)

// =============================================================================
// Student Profile Endpoints
// GET  /api/v1/profile/
// PATCH /api/v1/profile/
// =============================================================================

data class StudentProfileResponse(
    val username: String,
    val email: String,
    @SerializedName("first_name") val firstName: String,
    @SerializedName("last_name") val lastName: String,
    val nacionalidad: String?,
    val carnet: String?,
    val sexo: String,
    @SerializedName("image_url") val imageUrl: String?,
    val address: String?,
    val location: String?,
    val provincia: String?,
    val telephone: String?,
    val movil: String?
)

data class StudentProfileUpdateRequest(
    val nacionalidad: String? = null,
    val carnet: String? = null,
    val sexo: String? = null,
    val address: String? = null,
    val location: String? = null,
    val provincia: String? = null,
    val telephone: String? = null,
    val movil: String? = null
)

// =============================================================================
// Course Endpoints
// GET /api/v1/courses/
// GET /api/v1/courses/{id}/
// =============================================================================

data class CourseResponse(
    val id: Int,
    val name: String,
    val description: String?,
    val area: String,
    @SerializedName("area_display") val areaDisplay: String,
    val tipo: String,
    @SerializedName("tipo_display") val tipoDisplay: String,
    val teacher: Int,
    @SerializedName("teacher_name") val teacherName: String,
    @SerializedName("teacher_username") val teacherUsername: String,
    @SerializedName("class_quantity") val classQuantity: Int,
    val status: String,
    @SerializedName("status_display") val statusDisplay: String,
    @SerializedName("dynamic_status") val dynamicStatus: String,
    @SerializedName("dynamic_status_display") val dynamicStatusDisplay: String,
    @SerializedName("curso_academico") val cursoAcademico: Int?,
    @SerializedName("curso_academico_nombre") val cursoAcademicoNombre: String?,
    @SerializedName("enrollment_deadline") val enrollmentDeadline: String?, // Date "YYYY-MM-DD"
    @SerializedName("start_date") val startDate: String?, // Date "YYYY-MM-DD"
    @SerializedName("image_url") val imageUrl: String?,
    @SerializedName("fecha_creacion") val fechaCreacion: String?, // DateTime ISO
    @SerializedName("fecha_actualizacion") val fechaActualizacion: String? // DateTime ISO
)

// =============================================================================
// Enrollment Endpoints
// GET /api/v1/enrollments/
// GET /api/v1/enrollments/{id}/
// =============================================================================

data class EnrollmentResponse(
    val id: Int,
    val course: Int,
    @SerializedName("course_id") val courseId: Int,
    @SerializedName("course_name") val courseName: String,
    @SerializedName("course_area") val courseArea: String,
    @SerializedName("course_area_display") val courseAreaDisplay: String,
    @SerializedName("course_tipo") val courseTipo: String,
    @SerializedName("course_tipo_display") val courseTipoDisplay: String,
    @SerializedName("course_teacher_name") val courseTeacherName: String,
    val student: Int,
    @SerializedName("student_username") val studentUsername: String,
    val activo: Boolean,
    @SerializedName("curso_academico") val cursoAcademico: Int?,
    @SerializedName("curso_academico_nombre") val cursoAcademicoNombre: String?,
    val semestre: Int?,
    @SerializedName("fecha_matricula") val fechaMatricula: String, // Date "YYYY-MM-DD"
    val estado: String,
    @SerializedName("estado_display") val estadoDisplay: String
)

// =============================================================================
// Home Page Endpoint
// GET /api/v1/home/
// =============================================================================

data class HomePageResponse(
    @SerializedName("available_courses") val availableCourses: List<CourseResponse>,
    @SerializedName("latest_news") val latestNews: List<BlogPostListResponse>
)

// =============================================================================
// Blog - Public Post Endpoints
// GET /api/v1/blog/posts/
// GET /api/v1/blog/posts/{slug}/
// =============================================================================

data class BlogPostListResponse(
    val id: Int,
    val titulo: String,
    val slug: String,
    val resumen: String,
    @SerializedName("imagen_principal_url") val imagenPrincipalUrl: String?,
    val categoria: String, // StringRelatedField returns category name
    @SerializedName("autor_username") val autorUsername: String,
    val estado: String,
    @SerializedName("fecha_publicacion") val fechaPublicacion: String?, // DateTime ISO
    @SerializedName("meta_descripcion") val metaDescripcion: String?,
    val destacada: Boolean
)

data class BlogPostDetailResponse(
    val id: Int,
    val titulo: String,
    val slug: String,
    val resumen: String,
    val contenido: String,
    @SerializedName("imagen_principal_url") val imagenPrincipalUrl: String?,
    val categoria: String, // StringRelatedField returns category name
    @SerializedName("autor_username") val autorUsername: String,
    val estado: String,
    val visibilidad: String,
    val destacada: Boolean,
    @SerializedName("permitir_comentarios") val permitirComentarios: Boolean,
    @SerializedName("fecha_creacion") val fechaCreacion: String?, // DateTime ISO
    @SerializedName("fecha_actualizacion") val fechaActualizacion: String?, // DateTime ISO
    @SerializedName("fecha_publicacion") val fechaPublicacion: String?, // DateTime ISO
    @SerializedName("meta_descripcion") val metaDescripcion: String?,
    @SerializedName("notas_editor") val notasEditor: String?
)

data class CreatePostRequest(
    val titulo: String,
    val resumen: String,
    val contenido: String,
    val categoria: Int? = null,
    @SerializedName("meta_descripcion") val metaDescripcion: String? = null,
    @SerializedName("imagen_principal") val imagenPrincipal: String? = null,
    val destacada: Boolean = false,
    @SerializedName("permitir_comentarios") val permitirComentarios: Boolean = true,
    val visibilidad: String = "publico"
)

data class UpdatePostRequest(
    val titulo: String? = null,
    val resumen: String? = null,
    val contenido: String? = null,
    val categoria: Int? = null,
    @SerializedName("meta_descripcion") val metaDescripcion: String? = null,
    val destacada: Boolean? = null,
    @SerializedName("permitir_comentarios") val permitirComentarios: Boolean? = null,
    val visibilidad: String? = null
)

// =============================================================================
// Blog - Category Endpoints
// GET /api/v1/blog/categories/
// =============================================================================

data class CategoryResponse(
    val id: Int,
    val nombre: String,
    val descripcion: String?,
    val slug: String
)

// =============================================================================
// Blog - Moderator Endpoints
// GET  /api/v1/blog/moderator/reports/
// POST /api/v1/blog/moderator/reports/{id}/approve/
// POST /api/v1/blog/moderator/reports/{id}/reject/
// GET  /api/v1/blog/moderator/sanctions/
// GET  /api/v1/blog/moderator/metrics/
// =============================================================================

data class CommentReportResponse(
    val id: Int,
    val comentario: Int,
    @SerializedName("comentario_contenido") val comentarioContenido: String,
    @SerializedName("comentario_autor") val comentarioAutor: String,
    @SerializedName("reportado_por") val reportadoPor: Int,
    @SerializedName("reportado_por_username") val reportadoPorUsername: String,
    val motivo: String,
    @SerializedName("fecha_reporte") val fechaReporte: String, // DateTime ISO
    val estado: String,
    @SerializedName("resuelto_por") val resueltoPor: Int?,
    @SerializedName("resuelto_por_username") val resueltoPorUsername: String?,
    @SerializedName("fecha_resolucion") val fechaResolucion: String? // DateTime ISO
)

data class SanctionResponse(
    val id: Int,
    val usuario: Int,
    @SerializedName("usuario_username") val usuarioUsername: String,
    @SerializedName("tipo_sancion") val tipoSancion: String,
    val motivo: String,
    @SerializedName("fecha_inicio") val fechaInicio: String, // DateTime ISO
    @SerializedName("fecha_fin") val fechaFin: String?, // DateTime ISO
    @SerializedName("aplicada_por") val aplicadaPor: Int?,
    @SerializedName("aplicada_por_username") val aplicadaPorUsername: String?,
    val activa: Boolean,
    @SerializedName("fecha_levantamiento") val fechaLevantamiento: String?, // DateTime ISO
    @SerializedName("levantada_por") val levantadaPor: Int?,
    @SerializedName("levantada_por_username") val levantadaPorUsername: String?
)

data class CommunityMetricsResponse(
    val id: Int,
    val fecha: String, // Date "YYYY-MM-DD"
    @SerializedName("total_reportes") val totalReportes: Int,
    @SerializedName("total_comentarios") val totalComentarios: Int,
    @SerializedName("total_sanciones") val totalSanciones: Int,
    @SerializedName("usuario_mas_activo") val usuarioMasActivo: Int?,
    @SerializedName("usuario_mas_activo_username") val usuarioMasActivoUsername: String?,
    @SerializedName("pico_toxicidad") val picoToxicidad: Int?,
    @SerializedName("generada_en") val generadaEn: String? // DateTime ISO
)

// =============================================================================
// Blog - Editor Endpoints
// POST /api/v1/blog/editor/posts/{id}/reject/
// PATCH /api/v1/blog/editor/posts/{id}/update_notes/
// =============================================================================

data class RejectPostRequest(
    @SerializedName("notas_editor") val notasEditor: String
)

data class UpdateNotesRequest(
    @SerializedName("notas_editor") val notasEditor: String
)

// =============================================================================
// Course Application Endpoints
// POST /api/v1/applications/
// GET  /api/v1/applications/
// POST /api/v1/applications/{id}/cancel/
// =============================================================================

data class CourseApplicationResponse(
    val id: Int,
    val course: Int,
    @SerializedName("course_name") val courseName: String,
    @SerializedName("course_area") val courseArea: String,
    @SerializedName("course_area_display") val courseAreaDisplay: String,
    @SerializedName("course_teacher_name") val courseTeacherName: String?,
    val student: Int,
    @SerializedName("student_username") val studentUsername: String,
    val status: String,
    @SerializedName("status_display") val statusDisplay: String,
    @SerializedName("submission_date") val submissionDate: String?, // DateTime ISO
    @SerializedName("processed_date") val processedDate: String?, // DateTime ISO
    val notes: String?
)

data class CreateApplicationRequest(
    val course: Int
)
