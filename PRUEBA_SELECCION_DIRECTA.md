# Prueba de Selección Directa - Botón Docencia

## 🔧 Último Cambio Implementado

He cambiado completamente el enfoque de selección para evitar conflictos:

### ❌ Problema Anterior
- Usaba `checkbox.click()` que disparaba eventos
- Los eventos causaban conflictos entre sí
- Solo quedaba una tabla seleccionada al final

### ✅ Solución Actual
- Selección directa con `checkbox.checked = true`
- Sin delays entre selecciones
- Sin usar `click()` que causa conflictos
- Actualización manual del contador
- Actualización directa de clases CSS

## 🧪 Cómo Probar

### Paso 1: Refrescar
```
Ctrl+F5 (forzar recarga completa)
```

### Paso 2: Abrir Consola
```
F12 → Pestaña Console
```

### Paso 3: Ir a Tablas Archivadas
1. Navega a la pantalla de Tablas Archivadas
2. Haz clic en "Seleccionar Tablas"

### Paso 4: Hacer Clic en el Botón
1. Haz clic en "Auto-seleccionar Docencia"
2. Observa la consola

### Paso 5: Verificar en Consola

Deberías ver estos mensajes:

```
🎓 Botón Auto-seleccionar Docencia clickeado
📊 Total checkboxes encontrados: X
📋 Tablas Docencia actualmente seleccionadas: 0
🎯 Acción a realizar: SELECCIONAR
🔄 Procesando 11 checkboxes...
✅ Docencia_area: checked = true
✅ Docencia_coursecategory: checked = true
✅ Docencia_courseinformation_adminteachers: checked = true
✅ Docencia_courseinformation: checked = true
✅ Docencia_enrollmentapplication: checked = true
✅ Docencia_enrollmentpay: checked = true
✅ Docencia_accountnumber: checked = true
✅ Docencia_enrollment: checked = true
✅ Docencia_subjectinformation: checked = true
✅ Docencia_edition: checked = true
✅ Docencia_application: checked = true
🔄 Contador actualizado: 11 tablas seleccionadas
📚 Tablas Docencia seleccionadas: 11/11
```

### Paso 6: Verificar Visualmente

Deberías ver:
- ✅ 11 checkboxes marcados
- ✅ Contador muestra "11"
- ✅ Botón cambia a "Deseleccionar Docencia"
- ✅ Botón "Eliminar" se activa

### Paso 7: Probar Combinación

1. Haz clic en "Seleccionar y Combinar"
2. Verifica que el modal muestre las 11 tablas
3. Todas deben tener checkbox marcado

## 🔍 Si Aún No Funciona

### Verificación 1: Checkboxes en HTML
Abre la consola y ejecuta:

```javascript
// Ver todos los checkboxes
document.querySelectorAll('.tabla-checkbox').forEach(cb => {
    console.log(cb.getAttribute('data-tabla'), 'checked:', cb.checked);
});
```

### Verificación 2: Tablas de Docencia Disponibles
```javascript
// Ver qué tablas de Docencia existen
const tablasDocencia = [
    'Docencia_area', 'Docencia_coursecategory', 
    'Docencia_courseinformation_adminteachers',
    'Docencia_courseinformation', 'Docencia_enrollmentapplication',
    'Docencia_enrollmentpay', 'Docencia_accountnumber',
    'Docencia_enrollment', 'Docencia_subjectinformation',
    'Docencia_edition', 'Docencia_application'
];

let encontradas = 0;
document.querySelectorAll('.tabla-checkbox').forEach(cb => {
    const tableName = cb.getAttribute('data-tabla');
    if (tablasDocencia.includes(tableName)) {
        encontradas++;
        console.log('✅ Encontrada:', tableName);
    }
});
console.log(`Total encontradas: ${encontradas}/11`);
```

### Verificación 3: Forzar Selección Manual
Si el botón no funciona, prueba esto en la consola:

```javascript
// Seleccionar manualmente todas las tablas de Docencia
const tablasDocencia = [
    'Docencia_area', 'Docencia_coursecategory', 
    'Docencia_courseinformation_adminteachers',
    'Docencia_courseinformation', 'Docencia_enrollmentapplication',
    'Docencia_enrollmentpay', 'Docencia_accountnumber',
    'Docencia_enrollment', 'Docencia_subjectinformation',
    'Docencia_edition', 'Docencia_application'
];

document.querySelectorAll('.tabla-checkbox').forEach(cb => {
    const tableName = cb.getAttribute('data-tabla');
    if (tablasDocencia.includes(tableName)) {
        cb.checked = true;
        const card = cb.closest('.tabla-card');
        if (card) card.classList.add('seleccionada');
    }
});

// Actualizar contador
document.getElementById('contadorSeleccionadas').textContent = 
    document.querySelectorAll('.tabla-checkbox:checked').length;

console.log('✅ Selección manual completada');
```

## 🐛 Posibles Problemas

### Problema 1: Los nombres de las tablas no coinciden
**Solución**: Verifica los nombres exactos en la base de datos

```javascript
// Ver todos los nombres de tablas disponibles
document.querySelectorAll('.tabla-checkbox').forEach(cb => {
    console.log(cb.getAttribute('data-tabla'));
});
```

### Problema 2: Los checkboxes no tienen data-tabla
**Solución**: Verifica que los checkboxes tengan el atributo correcto

```javascript
// Verificar atributos
document.querySelectorAll('.tabla-checkbox').forEach(cb => {
    console.log('Checkbox:', cb.id, 'data-tabla:', cb.getAttribute('data-tabla'));
});
```

### Problema 3: Hay event listeners que interfieren
**Solución**: Los event listeners existentes pueden estar revirtiendo la selección

## 📊 Cambios Técnicos

### Antes (con click)
```javascript
checkbox.click(); // Dispara eventos que causan conflictos
```

### Ahora (directo)
```javascript
checkbox.checked = debeSeleccionar; // Cambio directo sin eventos
card.classList.add('seleccionada'); // Actualización visual directa
```

## ✅ Resultado Esperado

Después de hacer clic en "Auto-seleccionar Docencia":

1. ✅ 11 checkboxes marcados visualmente
2. ✅ Contador muestra "11"
3. ✅ Botón cambia a "Deseleccionar Docencia"
4. ✅ Tarjetas tienen clase "seleccionada"
5. ✅ Botón "Eliminar" se activa
6. ✅ Modal de combinación muestra las 11 tablas

---

**Última actualización**: 2 de marzo de 2026  
**Versión**: 1.3 (selección directa sin click)  
**Estado**: En prueba
