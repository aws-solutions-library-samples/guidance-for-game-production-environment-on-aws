<powershell>
## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0

# Set Windows Administrator password

$admin_password = Get-SECSecretValue ADMIN_PASSWORD_SECRET_ARN | % { Echo $_.SecretString} | ConvertTo-SecureString -AsPlainText -Force

Get-LocalUser -Name "Administrator" | Set-LocalUser -Password $admin_password

# Setup Windows Firewall rules

#Parsec
New-NetFirewallRule -DisplayName 'Allow Parsec' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 1666

#PCoIP
New-NetFirewallRule -DisplayName 'Allow PCoIP' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 4172

New-NetFirewallRule -DisplayName 'Allow PCoIP' -Direction Inbound -Action Allow -Protocol UDP -LocalPort 4172

New-NetFirewallRule -DisplayName 'Allow PCoIP' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 443

# NICE DCV
New-NetFirewallRule -DisplayName 'Allow PCoIP' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8443

# Allow Unreal Engine Swarm coomunication
New-NetFirewallRule -DisplayName 'Allow UE4 Swarm TCP' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8008-8009
New-NetFirewallRule -DisplayName 'Allow UE4 Swarm UDP' -Direction Inbound -Action Allow -Protocol UDP -LocalPort 8008-8009
New-NetFirewallRule -DisplayName 'Allow ICMP' -Direction Inbound -Action Allow -Protocol ICMPv4

# Install NVIDIA Grid driver

$Bucket = "ec2-windows-nvidia-drivers"
$KeyPrefix = "latest"
$LocalPath = "c:\nvidia-temp"
$Objects = Get-S3Object -BucketName $Bucket -KeyPrefix $KeyPrefix -Region us-east-1
foreach ($Object in $Objects) {
    $LocalFileName = $Object.Key
    if ($LocalFileName -ne '' -and $Object.Size -ne 0) {
        $LocalFilePath = Join-Path $LocalPath $LocalFileName
        Copy-S3Object -BucketName $Bucket -Key $Object.Key -LocalFile $LocalFilePath -Region us-east-1
    }
}


$nvidia_setup = Get-ChildItem -Path $LocalPath -Filter *server2019*.exe -Recurse -ErrorAction SilentlyContinue -Force | %{$_.FullName} 


& $nvidia_setup -s | Out-Null

New-ItemProperty -Path "HKLM:\SOFTWARE\NVIDIA Corporation\Global\GridLicensing" -Name "NvCplDisableManageLicensePage" -PropertyType "DWord" -Value "1"

Remove-Item $LocalPath -Recurse


# Install .NET Core Framework
Install-WindowsFeature Net-Framework-Core

</powershell>