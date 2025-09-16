# Stop on error
$ErrorActionPreference = "Stop"

Write-Host "=== Starting environment setup for Axiomatic MCP Servers ==="

# --- Ensure winget is available ---
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Host "[LOG] winget not found. Installing App Installer (which includes winget)..."
    $installer = "$env:TEMP\AppInstaller.msixbundle"
    Invoke-WebRequest -Uri "https://aka.ms/getwinget" -OutFile $installer
    Add-AppxPackage -Path $installer
    Remove-Item $installer
} else {
    Write-Host "[LOG] winget is available."
}

# --- Function to resolve real Python binary ---
function Resolve-Python {
    Write-Host "[LOG] Searching for Python..."

    # Ignore WindowsApps alias
    $pythonPaths = @(where.exe python 2>$null)
    foreach ($p in $pythonPaths) {
        if ($p -and (-not $p.Contains("WindowsApps"))) {
            Write-Host "[LOG] Found valid python in PATH: $p"
            return $p
        }
    }

    # Scan LocalAppData Programs
    if (Test-Path "$env:LocalAppData\Programs\Python") {
        $dirs = Get-ChildItem "$env:LocalAppData\Programs\Python" -Directory -ErrorAction SilentlyContinue
        foreach ($d in $dirs) {
            foreach ($exe in @("python.exe","python3.exe")) {
                $candidate = Join-Path $d.FullName $exe
                if (Test-Path $candidate) {
                    Write-Host "[LOG] Found python candidate: $candidate"
                    return $candidate
                }
            }
        }
    }

    # Scan Program Files
    if (Test-Path "C:\Program Files") {
        $dirs = Get-ChildItem "C:\Program Files" -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "Python*" }
        foreach ($d in $dirs) {
            foreach ($exe in @("python.exe","python3.exe")) {
                $candidate = Join-Path $d.FullName $exe
                if (Test-Path $candidate) {
                    Write-Host "[LOG] Found python candidate: $candidate"
                    return $candidate
                }
            }
        }
    }

    # Registry lookup
    foreach ($hive in "HKLM","HKCU") {
        try {
            $keys = Get-ChildItem "${hive}:\SOFTWARE\Python\PythonCore" -ErrorAction SilentlyContinue
            foreach ($k in $keys) {
                try {
                    $installPath = (Get-ItemProperty "$($k.PSPath)\InstallPath")."(default)"
                    foreach ($exe in @("python.exe","python3.exe")) {
                        $candidate = Join-Path $installPath $exe
                        if ($installPath -and (Test-Path $candidate)) {
                            Write-Host "[LOG] Found python via registry: $candidate"
                            return $candidate
                        }
                    }
                } catch {}
            }
        } catch {}
    }

    return $null
}

# --- Detect Python ---
$PYTHON_BIN = Resolve-Python

if (-not $PYTHON_BIN) {
    Write-Host "[LOG] No valid Python detected. Installing Python 3.12 x64 with winget..."
    winget install -e --id Python.Python.3.12 --architecture x64 -h

    Write-Host "[LOG] Checking again after install..."
    $PYTHON_BIN = Resolve-Python
    if (-not $PYTHON_BIN) {
        Write-Host "[ERROR] Python installation failed or executable not found."
        exit 1
    }
}

Write-Host "[LOG] Using PYTHON_BIN = $PYTHON_BIN"

# --- Validate Python version ---
try {
    Write-Host "[LOG] Running version check..."
    $pyVersion = & $PYTHON_BIN -c "import sys; print(sys.version_info.major*10+sys.version_info.minor)"
    Write-Host "[LOG] pyVersion raw result: $pyVersion"
} catch {
    Write-Host "[ERROR] Could not run Python at $PYTHON_BIN."
    exit 1
}

if (-not $pyVersion) {
    Write-Host "[ERROR] Python returned no version output."
    exit 1
}

if ([int]$pyVersion -lt 38) {
    Write-Host "Python version must be >= 3.8. Found: $(& $PYTHON_BIN --version)"
    exit 1
}
Write-Host "Using $(& $PYTHON_BIN --version)"

# --- Install pipx ---
if (-not (Get-Command pipx -ErrorAction SilentlyContinue)) {
    Write-Host "[LOG] Installing pipx..."
    & $PYTHON_BIN -m pip install --user pipx
    & $PYTHON_BIN -m pipx ensurepath
} else {
    Write-Host "[LOG] pipx already installed."
}

# --- Install uv ---
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "[LOG] Installing uv..."
    irm https://astral.sh/uv/install.ps1 | iex
} else {
    Write-Host "[LOG] uv already installed."
}

# --- Ensure local bin in PATH ---
$localBin = "$HOME\.local\bin"
if (-not ($env:Path -split ";" | ForEach-Object { $_.Trim() } | Where-Object { $_ -eq $localBin })) {
    Write-Host "[LOG] Adding $localBin to PATH..."
    $env:Path += ";$localBin"
} else {
    Write-Host "[LOG] $localBin already in PATH."
}

Write-Host ""
Write-Host "=== Setup complete! ==="
Write-Host ""

# --- Prompt user to start MCP server now ---
$RUN_NOW = Read-Host "Installation successful. Do you want to start the Axiomatic MCP server now? (y/N)"
$RUN_NOW = $RUN_NOW.ToLower()

if ($RUN_NOW -eq "y" -or $RUN_NOW -eq "yes") {
    Write-Host "[LOG] Starting Axiomatic MCP server..."
    uvx --from axiomatic-mcp all
} else {
    Write-Host "[LOG] Skipping MCP server start. To run later, execute:"
    Write-Host ""
    Write-Host "    uvx --from axiomatic-mcp all"
    Write-Host ""
}
