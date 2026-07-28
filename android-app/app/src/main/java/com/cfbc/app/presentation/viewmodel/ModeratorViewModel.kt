package com.cfbc.app.presentation.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.cfbc.app.data.model.Result
import com.cfbc.app.data.repository.ModeratorRepository
import com.cfbc.app.presentation.model.CommunityMetricsUiModel
import com.cfbc.app.presentation.model.ModeratorDashboardUiState
import com.cfbc.app.presentation.model.ReportUiModel
import com.cfbc.app.presentation.model.SanctionUiModel
import com.cfbc.app.presentation.model.UiEvent
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.receiveAsFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * ViewModel for the Blog Moderator dashboard.
 *
 * Manages:
 * - Pending comment reports
 * - Active user sanctions
 * - Community metrics
 * - Approve/reject reports
 *
 * Requirements: 8.1-8.12, 10.12, 10.21, 10.22
 */
@HiltViewModel
class ModeratorViewModel @Inject constructor(
    private val moderatorRepository: ModeratorRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(ModeratorDashboardUiState())
    val uiState: StateFlow<ModeratorDashboardUiState> = _uiState.asStateFlow()

    private val _events = Channel<UiEvent>(Channel.BUFFERED)
    val events = _events.receiveAsFlow()

    /** Load all moderator data: reports, sanctions, metrics. */
    fun loadAll() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            loadReports()
            loadSanctions()
            loadMetrics()
            _uiState.value = _uiState.value.copy(isLoading = false)
        }
    }

    /** Refresh all data (pull-to-refresh). */
    fun refresh() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isRefreshing = true)
            loadReports()
            loadSanctions()
            loadMetrics()
            _uiState.value = _uiState.value.copy(isRefreshing = false)
        }
    }

    private suspend fun loadReports() {
        when (val result = moderatorRepository.getReports()) {
            is Result.Success -> {
                _uiState.value = _uiState.value.copy(
                    reports = result.data.map { it.toUiModel() }
                )
            }
            is Result.Error -> {
                _uiState.value = _uiState.value.copy(error = result.displayMessage)
            }
            is Result.Loading -> {}
        }
    }

    private suspend fun loadSanctions() {
        when (val result = moderatorRepository.getSanctions()) {
            is Result.Success -> {
                _uiState.value = _uiState.value.copy(
                    sanctions = result.data.map { it.toUiModel() }
                )
            }
            is Result.Error -> {
                _uiState.value = _uiState.value.copy(error = result.displayMessage)
            }
            is Result.Loading -> {}
        }
    }

    private suspend fun loadMetrics() {
        when (val result = moderatorRepository.getCommunityMetrics()) {
            is Result.Success -> {
                _uiState.value = _uiState.value.copy(
                    metrics = CommunityMetricsUiModel(
                        totalReportes = result.data.totalReportes,
                        totalComentarios = result.data.totalComentarios,
                        totalSanciones = result.data.totalSanciones,
                        usuarioMasActivoUsername = result.data.usuarioMasActivoUsername
                    )
                )
            }
            is Result.Error -> {
                _uiState.value = _uiState.value.copy(error = result.displayMessage)
            }
            is Result.Loading -> {}
        }
    }

    /** Approve a report (hide the comment). */
    fun approveReport(reportId: Int) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(processingReportId = reportId)
            when (val result = moderatorRepository.approveReport(reportId)) {
                is Result.Success -> {
                    _events.send(UiEvent.ShowSnackbar("Reporte aprobado — comentario oculto"))
                    loadReports()
                    loadMetrics()
                }
                is Result.Error -> {
                    _events.send(UiEvent.ShowErrorSnackbar(result.displayMessage))
                }
                is Result.Loading -> {}
            }
            _uiState.value = _uiState.value.copy(processingReportId = null)
        }
    }

    /** Reject a report (keep the comment visible). */
    fun rejectReport(reportId: Int) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(processingReportId = reportId)
            when (val result = moderatorRepository.rejectReport(reportId)) {
                is Result.Success -> {
                    _events.send(UiEvent.ShowSnackbar("Reporte rechazado — comentario visible"))
                    loadReports()
                    loadMetrics()
                }
                is Result.Error -> {
                    _events.send(UiEvent.ShowErrorSnackbar(result.displayMessage))
                }
                is Result.Loading -> {}
            }
            _uiState.value = _uiState.value.copy(processingReportId = null)
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }
}

/** Maps a CommentReportResponse to ReportUiModel. */
private fun com.cfbc.app.infrastructure.network.dto.CommentReportResponse.toUiModel() = ReportUiModel(
    id = id,
    comentarioContenido = comentarioContenido,
    comentarioAutor = comentarioAutor,
    reportadoPorUsername = reportadoPorUsername,
    motivo = motivo,
    fechaReporte = fechaReporte
)

/** Maps a SanctionResponse to SanctionUiModel. */
private fun com.cfbc.app.infrastructure.network.dto.SanctionResponse.toUiModel() = SanctionUiModel(
    id = id,
    usuarioUsername = usuarioUsername,
    tipoSancion = tipoSancion,
    motivo = motivo,
    fechaInicio = fechaInicio,
    fechaFin = fechaFin,
    activa = activa
)
