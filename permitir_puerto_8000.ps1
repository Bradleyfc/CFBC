# Script para permitir el puerto 8000 en el Firewall de Windows
# Ejecutar como Administrador

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  Configurando Firewall de Windows" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar si ya existe la regla
$existingRule = Get-NetFirewallRule -DisplayName "Django Development Server" -ErrorAction SilentlyContinue

if ($existingRule) {
    Write-Host "[!] La regla ya existe. Eliminando la regla anterior..." -ForegroundColor Yellow
    Remove-NetFirewallRule -DisplayName "Django Development Server"
}

# Crear nueva regla
Write-Host "[+] Creando regla de firewall para el puerto 8000..." -ForegroundColor Green

New-NetFirewallRule `
    -DisplayName "Django Development Server" `
    -Description "Permite conexiones entrantes al servidor Django en el puerto 8000" `
    -Direction Inbound `
    -LocalPort 8000 `
    -Protocol TCP `
    -Action Allow `
    -Profile Private,Public `
    -Enabled True

if ($?) {
    Write-Host ""
    Write-Host "[OK] Regla de firewall creada exitosamente!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Detalles:" -ForegroundColor Cyan
    Write-Host "  - Puerto: 8000 (TCP)" -ForegroundColor White
    Write-Host "  - Direccion: Entrante (Inbound)" -ForegroundColor White
    Write-Host "  - Perfiles: Privado y Publico" -ForegroundColor White
    Write-Host ""
    Write-Host "[i] Ahora tu telefono deberia poder conectarse a:" -ForegroundColor Yellow
    Write-Host "    http://192.168.1.101:8000" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "[X] Error al crear la regla de firewall" -ForegroundColor Red
    Write-Host "    Asegurate de ejecutar este script como Administrador" -ForegroundColor Red
    Write-Host ""
}

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Presiona cualquier tecla para continuar..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
