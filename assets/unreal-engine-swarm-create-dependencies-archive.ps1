## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0

# This PowerShell script creates a Zip archive with all required
# files for creating UE4 Swarm node and Controller

# Your Unreal Engine 4 root folder
# Change this according to your location and version
$ue4root = 'C:\Program Files\Epic Games\UE_4.25'

# Where we are going to store the archive into your Documents folder
$ue4SwarmArchive = "ue4-swarm-archive"
$archivePath = [Environment]::GetFolderPath('MyDocuments')+"\"+$ue4SwarmArchive

# Path to Swarm related files
$ue4swarmpath = $ue4root + "\Engine\Binaries\DotNET"
$swarmPaths = @()
$swarmfiles = "AgentInterface.dll", "SwarmAgent.exe", "SwarmAgent.exe.config"
$swarmfiles +=  "SwarmCommonUtils.dll", "SwarmCoordinator.exe"
$swarmfiles += "SwarmCoordinator.exe.config","SwarmCoordinatorInterface.dll"
$swarmfiles += "SwarmInterface.dll","UnrealControls.dll"
$swarmfiles | Foreach-Object { $swarmPaths += $ue4swarmpath + '\' + $_  }

# Path to UE4PrereqSetup
$ue4prereq = $ue4root + "\Engine\Extras\Redist\en-us\UE4PrereqSetup_x64.exe"
$compressPaths = @()
$compressPaths = $swarmPaths + $ue4prereq
Compress-Archive -LiteralPath $compressPaths -DestinationPath $archivePath -Force