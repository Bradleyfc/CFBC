// JavaScript para barra de desplazamiento nativa fija en viewport

(function() {
    'use strict';
    
    let scrollbarContainer = null;
    let scrollbarContent = null;
    let tableContainer = null;
    let isUpdating = false;
    
    function createNativeScrollbar() {
        // Crear contenedor para la barra nativa
        scrollbarContainer = document.createElement('div');
        scrollbarContainer.className = 'viewport-scrollbar-container';
        
        // Crear contenido interno que genera el scroll
        scrollbarContent = document.createElement('div');
        scrollbarContent.className = 'viewport-scrollbar-content';
        
        scrollbarContainer.appendChild(scrollbarContent);
        document.body.appendChild(scrollbarContainer);
        
        console.log('Barra nativa fija en viewport creada');
    }
    
    function updateScrollbarPosition() {
        if (!tableContainer || !scrollbarContainer) return;
        
        // Obtener la posición y dimensiones de la tabla
        const tableRect = tableContainer.getBoundingClientRect();
        
        // Posicionar la barra exactamente donde está la tabla horizontalmente
        scrollbarContainer.style.left = tableRect.left + 'px';
        scrollbarContainer.style.width = tableRect.width + 'px';
    }
    
    function updateScrollbar() {
        if (!tableContainer || !scrollbarContainer || !scrollbarContent || isUpdating) return;
        
        const scrollWidth = tableContainer.scrollWidth;
        const clientWidth = tableContainer.clientWidth;
        const scrollLeft = tableContainer.scrollLeft;
        
        // Verificar si la tabla está visible en el viewport
        const tableRect = tableContainer.getBoundingClientRect();
        const isTableVisible = tableRect.top < window.innerHeight && tableRect.bottom > 0;
        
        if (scrollWidth > clientWidth && isTableVisible) {
            // Mostrar barra
            scrollbarContainer.classList.add('show');
            
            // Actualizar posición y tamaño de la barra
            updateScrollbarPosition();
            
            // Ajustar el ancho del contenido para que coincida exactamente con la tabla
            scrollbarContent.style.width = scrollWidth + 'px';
            
            // Sincronizar la posición del scroll
            isUpdating = true;
            scrollbarContainer.scrollLeft = scrollLeft;
            isUpdating = false;
            
            console.log('Barra visible - ScrollWidth:', scrollWidth, 'ClientWidth:', clientWidth, 'ScrollLeft:', scrollLeft);
        } else {
            // Ocultar barra
            scrollbarContainer.classList.remove('show');
        }
    }
    
    function setupEventListeners() {
        if (!tableContainer || !scrollbarContainer) return;
        
        // Sincronizar scroll de tabla -> barra fija
        tableContainer.addEventListener('scroll', function() {
            if (!isUpdating) {
                updateScrollbar();
            }
        });
        
        // Sincronizar scroll de barra fija -> tabla
        scrollbarContainer.addEventListener('scroll', function() {
            if (!isUpdating) {
                isUpdating = true;
                tableContainer.scrollLeft = scrollbarContainer.scrollLeft;
                isUpdating = false;
                console.log('Scroll desde barra fija:', scrollbarContainer.scrollLeft);
            }
        });
        
        // Detectar cuando la tabla entra/sale del viewport
        window.addEventListener('scroll', function() {
            updateScrollbar();
            updateScrollbarPosition();
        });
        
        document.addEventListener('scroll', function() {
            updateScrollbar();
            updateScrollbarPosition();
        });
        
        // Redimensionar ventana - actualizar posición y tamaño
        window.addEventListener('resize', function() {
            setTimeout(function() {
                updateScrollbarPosition();
                updateScrollbar();
            }, 100);
        });
        
        // Detectar cambios en el DOM que puedan afectar la posición de la tabla
        const observer = new MutationObserver(function() {
            setTimeout(function() {
                updateScrollbarPosition();
                updateScrollbar();
            }, 100);
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['style', 'class']
        });
        
        console.log('Event listeners para barra nativa configurados');
    }
    
    function init() {
        // Buscar el contenedor de la tabla
        tableContainer = document.querySelector('.results');
        
        if (!tableContainer) {
            console.log('No se encontró el contenedor .results');
            return;
        }
        
        console.log('Contenedor encontrado:', tableContainer);
        
        // Crear barra nativa fija
        createNativeScrollbar();
        
        // Configurar eventos
        setupEventListeners();
        
        // Actualizar inicialmente
        setTimeout(function() {
            updateScrollbarPosition();
            updateScrollbar();
        }, 500);
        
        // Verificar periódicamente
        setInterval(function() {
            if (scrollbarContainer && !document.body.contains(scrollbarContainer)) {
                console.log('Barra perdida, recreando...');
                createNativeScrollbar();
                setupEventListeners();
            }
            updateScrollbarPosition();
            updateScrollbar();
        }, 2000);
    }
    
    function cleanup() {
        if (scrollbarContainer && scrollbarContainer.parentNode) {
            scrollbarContainer.parentNode.removeChild(scrollbarContainer);
        }
        console.log('Limpieza de barra nativa realizada');
    }
    
    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Limpiar al salir
    window.addEventListener('beforeunload', cleanup);
    window.addEventListener('pagehide', cleanup);
    
})();