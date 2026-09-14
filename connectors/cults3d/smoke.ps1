param([string]$Query = 'dragon')
$ErrorActionPreference = 'Stop'
$baseUrl = 'https://ntybsaywkdmqcjhslehw.supabase.co/functions/v1/cults-search'
$secret = Read-Host 'Token do conector (nao a chave Cults)' -AsSecureString
$credential = [System.Net.NetworkCredential]::new('', $secret)
$headers = @{ Authorization = 'Bearer ' + $credential.Password }
try {
    $uri = $baseUrl + '/search?q=' + [uri]::EscapeDataString($Query) + '&limit=1'
    $rejected = $false
    try { $null = Invoke-RestMethod -Uri $uri }
    catch { if ([int]$_.Exception.Response.StatusCode -eq 401) { $rejected = $true } else { throw 'Endpoint sem token nao retornou 401. Verifique implantacao e segredos.' } }
    if (-not $rejected) { throw 'FALHA: endpoint aceitou acesso sem token.' }
    $search = Invoke-RestMethod -Uri $uri -Headers $headers
    if (-not $search.models -or -not $search.models[0].slug) { throw 'Sem modelos. Repita com outro termo.' }
    $details = Invoke-RestMethod -Uri ($baseUrl + '/details?slug=' + [uri]::EscapeDataString($search.models[0].slug)) -Headers $headers
    if (-not $details.model.title -or -not $details.model.url) { throw 'Detalhes invalidos.' }
    Write-Output ('OK: autenticacao, pesquisa e detalhes. Modelo: ' + $details.model.title)
} finally {
    $headers.Clear()
    $credential = $null
    $secret.Dispose()
}
