
$explicitNames = @() # find these from our config DSC or something
Show-NetFirewallRule | where { $explicitNames -Contains $_.DisplayName }  | Select 
# $_.Enable -eq True
# $_.Action -eq Allow
# $_.Direction -eq Inbound ?

$statuses = Show-NetFirewallRule | Select -ExpandProperty EnforcementStatus