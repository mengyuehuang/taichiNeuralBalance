$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..')).TrimEnd('\')+'\'
$pairs=@(
 @('auto_fc_pipeline_v2/extra_data_pipeline','auto_fc_pipeline_v2/PCD_output'),
 @('auto_fc_pipeline_v2/outputs','auto_fc_pipeline_v2/TCP_output')
)
if(-not(Test-Path -LiteralPath (Join-Path $PSScriptRoot 'move_inventory.json'))){throw 'Inventory incomplete'}
foreach($pair in $pairs){
 foreach($rel in $pair){
  $target=[IO.Path]::GetFullPath((Join-Path $workspace $rel))
  if(-not $target.StartsWith($workspace,[StringComparison]::OrdinalIgnoreCase)){throw "Out of scope: $target"}
 }
 if(-not(Test-Path -LiteralPath (Join-Path $workspace $pair[0]) -PathType Container)){throw 'Source missing'}
 if(Test-Path -LiteralPath (Join-Path $workspace $pair[1])){throw 'Destination already exists'}
}
foreach($pair in $pairs){
 Move-Item -LiteralPath (Join-Path $workspace $pair[0]) -Destination (Join-Path $workspace $pair[1])
 Write-Output "Moved $($pair[0]) to $($pair[1])"
}
