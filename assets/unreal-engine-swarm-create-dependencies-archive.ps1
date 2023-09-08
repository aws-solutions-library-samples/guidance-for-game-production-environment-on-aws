## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0

# This PowerShell script creates a Zip archive with all required
# files for creating UE5 Swarm node and Controller

# Prompt user to enter the location of Unreal Engine executable
$ue5root = 'C:\Program Files\Epic Games\UE_5.2'
while (! (Test-Path -Path "$ue5root")) {
    $ue5root = Read-Host -Prompt 'Input Unreal Engine root directory, for example C:\Program Files\Epic Games\UE_5.2'
} 

# Where we are going to store the archive into your Documents folder
$ue5SwarmArchive = "ue5-swarm-archive"
$archivePath = [Environment]::GetFolderPath('MyDocuments')+"\"+$ue5SwarmArchive

# Path to Swarm related files
$ue5swarmpath = $ue5root + "\Engine\Binaries\DotNET"
$swarmPaths = @()
$swarmfiles = "AgentInterface.dll", "SwarmAgent.exe", "SwarmAgent.exe.config"
$swarmfiles +=  "SwarmCommonUtils.dll", "SwarmCoordinator.exe"
$swarmfiles += "SwarmCoordinator.exe.config","SwarmCoordinatorInterface.dll"
$swarmfiles += "SwarmInterface.dll","UnrealControls.dll"
$swarmfiles | Foreach-Object { $swarmPaths += $ue5swarmpath + '\' + $_  }

# Path to UE5PrereqSetup
$ue5prereq = $ue5root + "\Engine\Extras\Redist\en-us\UEPrereqSetup_x64.exe"
$compressPaths = @()
$compressPaths = $swarmPaths + $ue5prereq
Compress-Archive -LiteralPath $compressPaths -DestinationPath $archivePath -Force

"Dependencies compressed and saved to $archivePath"