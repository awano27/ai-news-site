# PowerPoint COM object to convert PPTX to PDF
param(
    [string]$InputFile = "D:\ai-news-site-main\output\0106_slides.pptx",
    [string]$OutputFile = "D:\ai-news-site-main\workspace\0106_slides.pdf"
)

try {
    $ppt = New-Object -ComObject PowerPoint.Application
    $ppt.Visible = [Microsoft.Office.Core.MsoTriState]::msoTrue

    $presentation = $ppt.Presentations.Open($InputFile, $true, $true, $false)
    $presentation.SaveAs($OutputFile, 32) # 32 = ppSaveAsPDF
    $presentation.Close()
    $ppt.Quit()

    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($presentation) | Out-Null
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()

    Write-Host "PDF conversion successful: $OutputFile"
} catch {
    Write-Host "Error: $_"
    exit 1
}
