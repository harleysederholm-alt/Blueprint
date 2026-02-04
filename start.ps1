Write-Host "💎 UUSINTAYRITYS: DIAMOND-PÄIVITYS..." -ForegroundColor Cyan

# 1. Haetaan repot (NYT KOKO NIMELLÄ)
Write-Host "📡 Haetaan repoja (nameWithOwner)..." -ForegroundColor Yellow

# TÄSSÄ OLI VIRHE: Haetaan nyt 'nameWithOwner' eikä pelkkä 'name'
$json = gh repo list --limit 50 --json nameWithOwner
if (-not $json) {
    Write-Host "❌ Ei repoja. Kirjaudu: gh auth login" -ForegroundColor Red
    exit
}
$repos = $json | ConvertFrom-Json

# 2. Käydään repot läpi
foreach ($repo in $repos) {
    # TÄRKEÄ MUUTOS: Käytetään muotoa "kayttaja/repo"
    $fullName = $repo.nameWithOwner
    Write-Host "🚀 Työn alla: $fullName" -ForegroundColor Green
    
    $title = "Sweep: Operation Diamond Polish"
    $body = "We are moving to Enterprise Diamond Standards. @sweep please: 1. Add Strict Typing. 2. Add JSDoc to everything. 3. Fix error handling. 4. Generate Unit Tests."
    
    # Luodaan Issue (ilman virheiden piilotusta)
    gh issue create --repo $fullName --title $title --body $body --label "refactor"
}

Write-Host "`n✅ NYT SE ON OIKEASTI VALMIS." -ForegroundColor Cyan