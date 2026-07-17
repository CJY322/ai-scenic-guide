param(
  [string]$Text,

  [string]$TextFile,

  [Parameter(Mandatory = $true)]
  [string]$OutputWav
)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Speech

if ($TextFile) {
  $Text = Get-Content -Raw -Encoding UTF8 -LiteralPath $TextFile
}

if ([string]::IsNullOrWhiteSpace($Text)) {
  throw "Text or TextFile must provide non-empty speech text."
}

$outputDir = Split-Path -Parent $OutputWav
if ($outputDir -and -not (Test-Path -LiteralPath $outputDir)) {
  New-Item -ItemType Directory -Path $outputDir | Out-Null
}

$synthesizer = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
  try {
    $culture = [System.Globalization.CultureInfo]::GetCultureInfo("zh-CN")
    $synthesizer.SelectVoiceByHints(
      [System.Speech.Synthesis.VoiceGender]::Female,
      [System.Speech.Synthesis.VoiceAge]::Adult,
      0,
      $culture
    )
  } catch {
    # Fall back to the default Windows voice when no Chinese voice is installed.
  }

  $synthesizer.Rate = 0
  $synthesizer.Volume = 100
  $synthesizer.SetOutputToWaveFile($OutputWav)
  $synthesizer.Speak($Text)
  $synthesizer.SetOutputToNull()
} finally {
  $synthesizer.Dispose()
}
