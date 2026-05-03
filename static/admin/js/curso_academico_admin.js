'use strict';
(function () {
    document.addEventListener('DOMContentLoaded', function () {
        var cbArchivado = document.getElementById('id_archivado');
        var cbActivo    = document.getElementById('id_activo');

        if (!cbArchivado || !cbActivo) return;

        // ── Detectar contexto ────────────────────────────────────────────────
        var esNuevo     = window.location.pathname.indexOf('/add/') !== -1;
        // En edición, el curso estaba archivado si la casilla arranca marcada al cargar
        var eraArchivado = cbArchivado.checked;

        // ── Casilla "Archivado" cambia (solo en edición) ─────────────────────
        cbArchivado.addEventListener('change', function () {
            if (cbArchivado.checked) {
                cbActivo.checked = false;

                var ok = window.confirm(
                    '⚠️ Se archivará este curso académico junto con todos sus cursos, ' +
                    'matrículas, calificaciones y asistencias.\n\n' +
                    'Los datos quedarán guardados en "Datos Archivados" y podrán ' +
                    'restaurarse activando el curso nuevamente.\n\n' +
                    '¿Desea continuar?'
                );

                if (!ok) {
                    cbArchivado.checked = false;
                }
            }
        });

        // ── Casilla "Activo" cambia: desmarcar "Archivado" ───────────────────
        cbActivo.addEventListener('change', function () {
            if (cbActivo.checked) {
                cbArchivado.checked = false;
            }
        });

        // ── Interceptar submit al crear un curso nuevo con activo=True ───────
        if (esNuevo) {
            var form = document.querySelector('#content-main form');
            if (!form) return;

            var confirmadoNuevo = false;

            form.addEventListener('submit', function (e) {
                if (!cbActivo.checked || confirmadoNuevo) return;

                e.preventDefault();

                var ok = window.confirm(
                    '⚠️ Se creará un nuevo curso académico.\n\n' +
                    'El curso académico que está activo actualmente será archivado ' +
                    'junto con todos sus cursos, matrículas, calificaciones y asistencias.\n\n' +
                    'Los datos quedarán guardados en "Datos Archivados".\n\n' +
                    '¿Desea continuar?'
                );

                if (ok) {
                    confirmadoNuevo = true;
                    form.submit();
                }
            });
        }

        // ── Interceptar submit al activar un curso que estaba archivado ──────
        if (!esNuevo && eraArchivado) {
            var form = document.querySelector('#content-main form');
            if (!form) return;

            var confirmadoRestauro = false;

            form.addEventListener('submit', function (e) {
                // Solo actuar si se está marcando "activo" en un curso que era archivado
                if (!cbActivo.checked || confirmadoRestauro) return;

                e.preventDefault();

                // Consultar al servidor si hay un curso activo actualmente
                fetch('/admin/api/hay-curso-activo/', {
                    method: 'GET',
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                })
                .then(function (response) { return response.json(); })
                .then(function (data) {
                    if (data.hay_activo) {
                        // Hay un curso activo: bloquear y avisar
                        alert(
                            '🚫 No se puede restaurar este curso académico.\n\n' +
                            'Actualmente hay un curso académico activo: "' + data.nombre + '".\n\n' +
                            'Debe archivar el curso activo antes de restaurar este.'
                        );
                        // Desmarcar "activo" para que el usuario no guarde por error
                        cbActivo.checked = false;
                    } else {
                        // No hay curso activo: pedir confirmación para restaurar
                        var ok = window.confirm(
                            '✅ Se activará y restaurará este curso académico.\n\n' +
                            'Todos sus cursos, matrículas, calificaciones y asistencias ' +
                            'serán restaurados desde los datos archivados.\n\n' +
                            '¿Desea continuar?'
                        );

                        if (ok) {
                            confirmadoRestauro = true;
                            form.submit();
                        } else {
                            cbActivo.checked = false;
                        }
                    }
                })
                .catch(function () {
                    // Si falla la consulta, dejar que el servidor decida
                    confirmadoRestauro = true;
                    form.submit();
                });
            });
        }
    });
})();
