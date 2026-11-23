$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..')).TrimEnd('\')+'\'
$pairs=@(
    @('auto_fc_pipeline_v1/extra_review','auto_fc_pipeline_v1/outputs/PCD_output'),
    @('auto_fc_pipeline_v1/outputs/v1_preica_test','auto_fc_pipeline_v1/outputs/TCP_output')
)
if(-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'move_inventory.json'))){throw 'Missing completed inventory'}
foreach($pair in $pairs){
    $source=[IO.Path]::GetFullPath((Join-Path $workspace $pair[0]))
    $destination=[IO.Path]::GetFullPath((Join-Path $workspace $pair[1]))
    foreach($path in @($source,$destination)){
        if(-not $path.StartsWith($workspace,[StringComparison]::OrdinalIgnoreCase)){throw "Out of workspace: $path"}
    }
    if(-not (Test-Path -LiteralPath $source -PathType Container)){throw "Source missing: $source"}
    if(Test-Path -LiteralPath $destination){throw "Destination already exists: $destination"}
}
foreach($pair in $pairs){
    Move-Item -LiteralPath (Join-Path $workspace $pair[0]) -Destination (Join-Path $workspace $pair[1])
    Write-Output "Moved $($pair[0]) -> $($pair[1])"
}
