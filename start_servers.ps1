# EventPass 360 — Iniciar los 5 servicios Flask (PowerShell)
$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$services = @(
  @('02_API_Compras',    5000),
  @('03_API_Usuarios',   5001),
  @('04_API_Eventos',    5002),
  @('05_API_Promociones',5003),
  @('06_API_Facturacion',5004),
  @('10_API_Entradas',   5005)
)
foreach ($s in $services) {
  $dir = Join-Path $root $s[0]
  if (-not (Test-Path (Join-Path $dir '.env'))) {
    Write-Warning "Falta .env en $($s[0]). Copialo desde .env.example y completa DATABASE_URL y JWT_SECRET_KEY."
    continue
  }
  Start-Process powershell -ArgumentList '-NoExit','-Command',"Set-Location '$dir'; python app.py"
  Write-Host "Iniciado $($s[0]) en puerto $($s[1])"
}
