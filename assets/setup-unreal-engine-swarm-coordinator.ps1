<powershell>
## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0

# Get Administrator password from AWS Secrets Manager
$admin_password_plaintext = Get-SECSecretValue ADMIN_PASSWORD_SECRET_ARN | % { Echo $_.SecretString} 
$admin_password_secure_string = $admin_password_plaintext | ConvertTo-SecureString -AsPlainText -Force

# Set Administrator password 
Get-LocalUser -Name "Administrator" | Set-LocalUser -Password $admin_password_secure_string

# Define the Swarm Coordinator to start as a Scheduled task at startup
$action = New-ScheduledTaskAction -Execute "C:\ue4-swarm\SwarmCoordinator.exe"
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -Action $action -Trigger $trigger -User "Administrator" -Password $admin_password_plaintext -TaskName "SwarmCoordinator" -Description "UE4 Swarm Coordinator" -RunLevel Highest -AsJob

# Restart the instance to trigger the Schedule task.
Restart-Computer
</powershell>