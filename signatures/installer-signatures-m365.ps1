# Installe les signatures INOVA dans les boîtes Microsoft 365, depuis un compte administrateur.
# Elles s'ajoutent ensuite automatiquement aux nouveaux messages et aux réponses
# (Outlook sur le web, nouvel Outlook Windows, Outlook Mac et mobile synchronisés).
#
# Utilisation : placer ce fichier à côté de steven-poirier.htm et stephane-pasquier.htm,
# ouvrir PowerShell dans ce dossier, puis lancer :  .\installer-signatures-m365.ps1

$Signatures = @{
    "stevenpoirier@inova-securite.fr"     = "steven-poirier.htm"
    "stephanepasquier@inova-securite.fr"  = "stephane-pasquier.htm"
}

# 1. Module Exchange Online (installé une seule fois)
if (-not (Get-Module -ListAvailable -Name ExchangeOnlineManagement)) {
    Install-Module ExchangeOnlineManagement -Scope CurrentUser -Force
}
Import-Module ExchangeOnlineManagement

# 2. Connexion avec le compte administrateur (fenêtre de connexion Microsoft)
Connect-ExchangeOnline -ShowBanner:$false

# 3. Permet à l'administrateur de définir les signatures des boîtes
#    (sinon Microsoft ignore les signatures posées par script)
Set-OrganizationConfig -PostponeRoamingSignaturesUntilLater $true

# 4. Dépose et active la signature dans chaque boîte
foreach ($boite in $Signatures.Keys) {
    $fichier = Join-Path $PSScriptRoot $Signatures[$boite]
    $html = Get-Content -Path $fichier -Raw -Encoding UTF8
    # garde seulement le contenu du <body>
    if ($html -match '(?s)<body[^>]*>(.*)</body>') { $html = $Matches[1].Trim() }
    Set-MailboxMessageConfiguration -Identity $boite `
        -SignatureHtml $html `
        -AutoAddSignature $true `
        -AutoAddSignatureOnReply $true
    Write-Host "Signature installée pour $boite" -ForegroundColor Green
}

Disconnect-ExchangeOnline -Confirm:$false
Write-Host "Terminé. Ouvrez un nouveau mail dans Outlook pour vérifier (prévoir jusqu'à une heure de synchronisation)."
