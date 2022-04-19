Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

choco install vcredist2015 -y
	
New-Item -ItemType Directory -Force -Path 'c:\ic_init_temp'
$icInitFolder = 'c:\ic_init_temp'
$setupLogFile = $icInitFolder + '\ic_log.txt'
$installerPath = $icInitFolder + "\IBSetupConsole.exe"
$licenseApi = "https://f65xom4rf9.execute-api.eu-central-1.amazonaws.com/default/license_generator?machine_id="
$licensePath = $icInitFolder + "\IbLicense.IB_lic"

#start downloading ib installaer
$date = Get-Date
Add-Content $setupLogFile ("$date - downloading installer")

$installerName = "https://ib-installers-prod.s3.eu-central-1.amazonaws.com/ibsetup/ibsetup_lts_console.exe"
(New-Object System.Net.WebClient).DownloadFile($installerName, $installerPath)
$date = Get-Date
Add-Content $setupLogFile ("$date - download finished")
#start IB installation
& $installerPath /Install /Components=Coordinator
$date = Get-Date
Add-Content $setupLogFile ("$date - silent installer installed")

#get machine id
$machineid = & "C:\Program Files (x86)\IncrediBuild\machineid.exe"
#get license for ib
(New-Object System.Net.WebClient).DownloadFile($licenseApi+$machineid, $licensePath)

$data = Get-Content $licensePath
$bytes = [Convert]::FromBase64String($data)
[IO.File]::WriteAllBytes($licensePath, $bytes)


#load license
$licproc = "C:\Program Files (x86)\IncrediBuild\XLicProc.exe"
& $licproc /LICENSEFILE=$licensePath