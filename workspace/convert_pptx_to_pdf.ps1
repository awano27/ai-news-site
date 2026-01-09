# PowerPoint COM object to convert PPTX to PDF
param(
    [string]$InputFile = "D:\ai-news-site-main\input\day\0106-2.pptx",
    [string]$OutputFile = "D:\ai-news-site-main\workspace\0106.pdf"
)

try {
    $ErrorActionPreference = "Stop"

    # Check if PowerPoint is available
    $ppt = New-Object -ComObject PowerPoint.Application
    $ppt.Visible = [Microsoft.Office.Core.MsoTriState]::msoFalse

    Write-Host "Opening presentation: $InputFile"
    $presentation = $ppt.Presentations.Open($InputFile, $false, $false, $false)

    Write-Host "Converting to PDF: $OutputFile"
    $presentation.SaveAs($OutputFile, 32) # 32 = ppSaveAsPDF

    Write-Host "Closing presentation..."
    $presentation.Close()
    $ppt.Quit()

    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($presentation) | Out-Null
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()

    Write-Host "Success: PDF created at $OutputFile"
    exit 0
} catch {
    Write-Host "Error: $_"
    Write-Host "PowerPoint may not be installed or COM automation is not available."
    exit 1
}
