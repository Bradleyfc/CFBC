# Script para configurar Port Forwarding de WSL2 a Windows
# Esto permite que dispositivos en tu red accedan al servidor Django corriendo en WSL
# EJECUTAR COMO ADMINISTRADOR

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  Configurando Port Forwarding WSL2" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Obtener la IP de WSL2
Write-Host "[*] Obteniendo IP de WSL2..." -ForegroundColor Yellow
$wslIp = (wsl hostname -I).Trim()

if ([string]::IsNullOrEmpty($wslIp)) {
    Write-Host "[X] Error: No se pudo obtener la IP de WSL2" -ForegroundColor Red
    Write-Host "    Asegurate de que WSL este corriendo" -ForegroundColor Red
    exit 1
}

Write-Host "[+] IP de WSL2: $wslIp" -ForegroundColor Green
Write-Host ""

# Obtener la IP de Windows (WiFi)
Write-Host "[*] Obteniendo IP de Windows..." -ForegroundColor Yellow
$windowsIp = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Wi-Fi" | Select-Object -First 1).IPAddress

if ([string]::IsNullOrEmpty($windowsIp)) {
    Write-Host "[!] No se encontro adaptador Wi-Fi, intentando con Ethernet..." -ForegroundColor Yellow
    $windowsIp = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*"} | Select-Object -First 1).IPAddress
}

Write-Host "[+] IP de Windows: $windowsIp" -ForegroundColor Green
Write-Host ""

# Puerto a reenviar
$port = 8000

# Eliminar reglas existentes (si existen)
Write-Host "[*] Limpiando reglas antiguas..." -ForegroundColor Yellow
netsh interface portproxy delete v4tov4 listenport=$port listenaddress=0.0.0.0 2>$null
netsh interface portproxy delete v4tov4 listenport=$port listenaddress=$windowsIp 2>$null
Remove-NetFirewallRule -DisplayName "WSL Django Server" -ErrorAction SilentlyContinue
Write-Host "[+] Limpieza completada" -ForegroundColor Green
Write-Host ""

# Crear regla de port forwarding
Write-Host "[*] Creando regla de port forwarding..." -ForegroundColor Yellow
netsh interface portproxy add v4tov4 listenport=$port listenaddress=0.0.0.0 connectport=$port connectaddress=$wslIp

if ($LASTEXITCODE -eq 0) {
    Write-Host "[+] Port forwarding configurado exitosamente!" -ForegroundColor Green
} else {
    Write-Host "[X] Error al configurar port forwarding" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Crear regla de firewall
Write-Host "[*] Creando regla de firewall..." -ForegroundColor Yellow
New-NetFirewallRule -DisplayName "WSL Django Server" -Direction Inbound -LocalPort $port -Protocol TCP -Action Allow -Profile Private,Public | Out-Null

if ($?) {
    Write-Host "[+] Regla de firewall creada exitosamente!" -ForegroundColor Green
} else {
    Write-Host "[X] Error al crear regla de firewall" -ForegroundColor Red
}
Write-Host ""

# Mostrar configuracion actual
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  CONFIGURACION COMPLETADA" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Detalles de la configuracion:" -ForegroundColor Cyan
Write-Host "  - WSL IP: $wslIp" -ForegroundColor White
Write-Host "  - Windows IP: $windowsIp" -ForegroundColor White
Write-Host "  - Puerto: $port" -ForegroundColor White
Write-Host ""
Write-Host "Ahora puedes acceder al servidor Django desde:" -ForegroundColor Yellow
Write-Host "  - Local (Windows): http://localhost:$port" -ForegroundColor White
Write-Host "  - Local (Windows): http://$windowsIp`:$port" -ForegroundColor White
Write-Host "  - Telefono: http://$windowsIp`:$port" -ForegroundColor White
Write-Host ""
Write-Host "Configuracion actual de port forwarding:" -ForegroundColor Cyan
netsh interface portproxy show v4tov4
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[i] IMPORTANTE: Esta configuracion se pierde al reiniciar Windows" -ForegroundColor Yellow
Write-Host "    Ejecuta este script de nuevo despues de reiniciar" -ForegroundColor Yellow
Write-Host ""
Write-Host "Presiona cualquier tecla para continuar..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
