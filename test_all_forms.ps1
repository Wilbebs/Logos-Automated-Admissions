# Multi-Form Detection Test Suite
# Tests all 4 forms to verify detection works

$baseUrl = "https://logos-automated-admissions-production.up.railway.app/webhook/machform"

Write-Host "`n=====================================================" -ForegroundColor Green
Write-Host "LOGOS UCL - Multi-Form Detection Test Suite" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green

# TEST 1: Estados Unidos Form
Write-Host "`n[TEST 1] Testing Estados Unidos Form..." -ForegroundColor Cyan
$body1 = '{"element_1_1":"Rev.","element_1_2":"Dr.","element_1":"Maria","element_2":"Rodriguez","element_14":"maria@test.com","element_5":"Teologia","element_4":"Pregrado","element_32":"Pastor","element_34":"Primera Iglesia","element_35":"10","element_38":"Pentecostal"}'
try {
    $result1 = Invoke-RestMethod -Uri $baseUrl -Method POST -ContentType "application/json" -Body ([System.Text.Encoding]::UTF8.GetBytes($body1))
    Write-Host "✅ Form Detected: $($result1.form_detected)" -ForegroundColor Green
    Write-Host "   Applicant: $($result1.applicant)" -ForegroundColor Yellow
} catch {
    Write-Host "❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

Start-Sleep -Seconds 3

# TEST 2: Latinoamerica Form
Write-Host "`n[TEST 2] Testing Latinoamerica Form..." -ForegroundColor Cyan
$body2 = '{"element_1":"Sr.","element_2":"Juan","element_3":"Perez","element_4":"Masculino","element_16":"juan@test.com","element_39":"Metodista"}'
try {
    $result2 = Invoke-RestMethod -Uri $baseUrl -Method POST -ContentType "application/json" -Body ([System.Text.Encoding]::UTF8.GetBytes($body2))
    Write-Host "✅ Form Detected: $($result2.form_detected)" -ForegroundColor Green
    Write-Host "   Applicant: $($result2.applicant)" -ForegroundColor Yellow
} catch {
    Write-Host "❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

Start-Sleep -Seconds 3

# TEST 3: Experiencia Ministerial Form
Write-Host "`n[TEST 3] Testing Experiencia Ministerial Form..." -ForegroundColor Cyan
$body3 = '{"element_1":"Carlos","element_2":"Garcia","element_9":"carlos@test.com","element_17":"Iglesia Central","element_26":"15 anos","element_33":"Pastor Principal"}'
try {
    $result3 = Invoke-RestMethod -Uri $baseUrl -Method POST -ContentType "application/json" -Body ([System.Text.Encoding]::UTF8.GetBytes($body3))
    Write-Host "✅ Form Detected: $($result3.form_detected)" -ForegroundColor Green
    Write-Host "   Applicant: $($result3.applicant)" -ForegroundColor Yellow
} catch {
    Write-Host "❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

Start-Sleep -Seconds 3

# TEST 4: Recomendacion Pastoral Form
Write-Host "`n[TEST 4] Testing Recomendacion Pastoral Form..." -ForegroundColor Cyan
$body4 = '{"element_1":"Pedro","element_2":"Martinez","element_9":"pedro@test.com","element_18":"Rev. Luis Gomez","element_28":"5 anos","element_41":"Excelente"}'
try {
    $result4 = Invoke-RestMethod -Uri $baseUrl -Method POST -ContentType "application/json" -Body ([System.Text.Encoding]::UTF8.GetBytes($body4))
    Write-Host "✅ Form Detected: $($result4.form_detected)" -ForegroundColor Green
    Write-Host "   Applicant: $($result4.applicant)" -ForegroundColor Yellow
} catch {
    Write-Host "❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=====================================================" -ForegroundColor Green
Write-Host "Test Suite Complete! Check Railway logs for details." -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green