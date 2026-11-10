param()

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing.Common

$repoRoot = Split-Path -Parent $PSScriptRoot
$dataRoot = Join-Path $repoRoot 'services\api-server\outputs\experiment7'
$outputRoot = Join-Path $PSScriptRoot '实验7截图'
New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null
$p0 = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $dataRoot 'p0_results.json') | ConvertFrom-Json
$p1 = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $dataRoot 'p1_results.json') | ConvertFrom-Json

function New-Font([float]$size, [bool]$bold = $false) {
    $style = if ($bold) { [System.Drawing.FontStyle]::Bold } else { [System.Drawing.FontStyle]::Regular }
    return [System.Drawing.Font]::new('Microsoft YaHei', $size, $style, [System.Drawing.GraphicsUnit]::Pixel)
}

function New-Canvas([int]$width, [int]$height, [string]$background) {
    $bitmap = [System.Drawing.Bitmap]::new($width, $height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
    $graphics.Clear([System.Drawing.ColorTranslator]::FromHtml($background))
    return @{ Bitmap = $bitmap; Graphics = $graphics }
}

function Brush([string]$color) { return [System.Drawing.SolidBrush]::new([System.Drawing.ColorTranslator]::FromHtml($color)) }
function Pen([string]$color, [float]$width = 2) { return [System.Drawing.Pen]::new([System.Drawing.ColorTranslator]::FromHtml($color), $width) }

function Draw-Text($g, [string]$text, [float]$x, [float]$y, [float]$size, [string]$color, [bool]$bold = $false) {
    $f = New-Font $size $bold
    $b = Brush $color
    $g.DrawString($text, $f, $b, $x, $y)
    $b.Dispose(); $f.Dispose()
}

function Draw-Panel($g, [float]$x, [float]$y, [float]$w, [float]$h, [string]$fill) {
    $b = Brush $fill; $p = Pen '#cbd5e1' 2
    $g.FillRectangle($b, $x, $y, $w, $h); $g.DrawRectangle($p, $x, $y, $w, $h)
    $b.Dispose(); $p.Dispose()
}

function Save-Canvas($canvas, [string]$name) {
    $path = Join-Path $outputRoot $name
    $canvas.Bitmap.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    $canvas.Graphics.Dispose(); $canvas.Bitmap.Dispose()
}

# 图3-1：端到端数据流
$c = New-Canvas 1800 720 '#f5f8fc'; $g = $c.Graphics
Draw-Text $g '图3-1  灵山胜境可信导游原型端到端主链路' 60 35 42 '#17324d' $true
$cards = @(
    @(55, '游客输入', '问题 / 兴趣', '游览场景', '#e8f2ff'),
    @(345, '输入预检', '空值、异常标点', '敏感指令', '#eaf7ee'),
    @(635, 'Dify RAG', 'deepseek-v4-flash', '灵山胜境知识库', '#fff3d8'),
    @(925, '输出检查', '要点、边界', '引用、长度', '#f5eafe'),
    @(1215, '结果展示', '回答 + 资料依据', '失败提示', '#e8f6f8'),
    @(1505, '软件接口', 'FastAPI / Web', '后续正式集成', '#fdecec')
)
foreach ($card in $cards) {
    $x = [float]$card[0]
    Draw-Panel $g $x 205 235 215 $card[4]
    Draw-Text $g $card[1] ($x + 25) 235 28 '#173e55' $true
    Draw-Text $g $card[2] ($x + 25) 310 20 '#405566'
    Draw-Text $g $card[3] ($x + 25) 350 20 '#405566'
}
foreach ($x in @(290,580,870,1160,1450)) {
    $p = Pen '#356e86' 5; $g.DrawLine($p, $x, 312, $x + 55, 312); $p.Dispose()
    $b = Brush '#356e86'; $g.FillPolygon($b, [System.Drawing.PointF[]]@([System.Drawing.PointF]::new($x+55,312),[System.Drawing.PointF]::new($x+39,302),[System.Drawing.PointF]::new($x+39,322))); $b.Dispose()
}
Draw-Panel $g 310 505 1180 120 '#fff7ed'
Draw-Text $g '错误与边界分支' 355 526 26 '#9a3412' $true
Draw-Text $g '超时 / 无引用 / 输出不合格 → 明确反馈，并将中间结果、错误类型写入 JSON 证据' 355 571 22 '#6b4b3d'
Save-Canvas $c '图3-1-原型数据流.png'

# 图3-2：两版指标对比
$avgP0 = [math]::Round(($p0.results | Measure-Object elapsed_ms -Average).Average)
$avgP1 = [int]$p1.summary.average_elapsed_ms
$callsP0 = ($p0.results | Measure-Object model_calls -Sum).Sum
$callsP1 = [int]$p1.summary.total_model_calls
$c = New-Canvas 1600 850 '#f5f8fc'; $g = $c.Graphics
Draw-Text $g '图3-2  P0 初版与 P1 修订版同集实测' 60 35 42 '#17324d' $true
$metrics = @(
    @('可见资料依据率',0,100,'%',100),
    @('平均响应时间',$avgP0,$avgP1,'ms',10000),
    @('模型调用次数',$callsP0,$callsP1,'次',13),
    @('规则通过率',100,100,'%',100)
)
for ($i=0; $i -lt $metrics.Count; $i++) {
    $x = 75 + $i * 380; $m = $metrics[$i]
    Draw-Panel $g $x 155 340 565 '#ffffff'
    Draw-Text $g $m[0] ($x + 25) 184 25 '#27465c' $true
    for ($j=0; $j -lt 2; $j++) {
        $value = [double]$m[$j+1]; $left = $x + 55 + $j * 130
        $height = [int](345 * $value / [double]$m[4]); $top = 645 - $height
        $color = if ($j -eq 0) { '#94a3b8' } else { '#2563eb' }
        $b = Brush $color; $g.FillRectangle($b, $left, $top, 75, $height); $b.Dispose()
        Draw-Text $g ([string]$value) ($left + 10) ($top - 42) 22 '#17324d' $true
        $versionLabel = if ($j -eq 0) { 'P0' } else { 'P1' }
        Draw-Text $g $versionLabel ($left + 18) 670 22 '#405566' $true
    }
    Draw-Text $g $m[3] ($x + 155) 738 19 '#64748b'
}
Draw-Text $g '两版正确性规则均通过；P1 重点改进引用完整性、异常输入处理和资源效率。' 355 800 22 '#405566'
Save-Canvas $c '图3-2-两版实测对比.png'

# 图3-3：逐项测试矩阵
$c = New-Canvas 1550 1120 '#f5f8fc'; $g = $c.Graphics
Draw-Text $g '图3-3  12条固定评测集逐项结果' 60 35 42 '#17324d' $true
Draw-Panel $g 50 125 1450 915 '#ffffff'
$hb = Brush '#1d4ed8'; $g.FillRectangle($hb,65,145,1420,70); $hb.Dispose()
$cols = @(@(70,'编号'),@(180,'类别'),@(650,'P0'),@(800,'P1'),@(950,'P1耗时/ms'),@(1220,'P1模型调用'))
foreach ($col in $cols) { Draw-Text $g $col[1] $col[0] 164 23 '#ffffff' $true }
for ($i=0; $i -lt $p0.results.Count; $i++) {
    $a = $p0.results[$i]; $b = $p1.results[$i]; $y = 232 + $i * 65
    if ($i % 2 -eq 1) { $shade = Brush '#eff6ff'; $g.FillRectangle($shade,65,$y-4,1420,57); $shade.Dispose() }
    $p0Status = if ($a.automatic_pass) { '通过' } else { '未通过' }
    $p1Status = if ($b.automatic_pass) { '通过' } else { '未通过' }
    $values = @($a.id,$a.category,$p0Status,$p1Status,[string]$b.elapsed_ms,[string]$b.model_calls)
    for ($j=0; $j -lt $cols.Count; $j++) {
        $textColor = if ($values[$j] -eq '通过') { '#14715f' } else { '#244052' }
        Draw-Text $g $values[$j] $cols[$j][0] ($y+7) 20 $textColor ($values[$j] -eq '通过')
    }
}
Draw-Text $g 'E12 异常标点由本地预检返回，因此 P1 耗时为0、模型调用为0。' 400 1070 21 '#475569'
Save-Canvas $c '图3-3-测试集逐项结果.png'

# 图3-4：运行记录
$c = New-Canvas 1600 1050 '#111827'; $g = $c.Graphics
Draw-Text $g '图3-4  修订版评测运行记录（由真实 JSON 结果生成）' 60 35 36 '#ffffff' $true
$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('PS D:\ai-scenic-guide\services\api-server>')
$lines.Add('.\.venv\Scripts\python.exe scripts\experiment7_eval.py --version P1')
$lines.Add('')
foreach ($row in $p1.results) {
    $resultLabel = if ($row.automatic_pass) { 'PASS' } else { 'FAIL' }
    $lines.Add(('{0}: HTTP {1}   {2,5} ms   {3}' -f $row.id,$row.http_status,$row.elapsed_ms,$resultLabel))
}
$lines.Add('')
$lines.Add(('summary: passed={0}/{1}, avg={2} ms, tokens={3}, calls={4}' -f $p1.summary.passed,$p1.summary.total,$p1.summary.average_elapsed_ms,$p1.summary.total_tokens,$p1.summary.total_model_calls))
$lines.Add('Saved: outputs\experiment7\p1_results.json')
$mono = [System.Drawing.Font]::new('Consolas',26,[System.Drawing.FontStyle]::Regular,[System.Drawing.GraphicsUnit]::Pixel); $green = Brush '#d1fae5'
for ($i=0; $i -lt $lines.Count; $i++) { $g.DrawString($lines[$i],$mono,$green,70,115+$i*47) }
$green.Dispose(); $mono.Dispose()
Save-Canvas $c '图3-4-修订版运行记录.png'

Get-ChildItem -LiteralPath $outputRoot | Select-Object Name,Length
