<powershell>
mkdir "c:\cwagent"
wget "https://s3.amazonaws.com/amazoncloudwatch-agent/windows/amd64/latest/AmazonCloudWatchAgent.zip" -OutFile "C:\cwagent\cwagent.zip"
Add-Type -AssemblyName System.IO.Compression.FileSystem
function Unzip
{
    param([string]$zipfile, [string]$outpath)
    [System.IO.Compression.ZipFile]::ExtractToDirectory($zipfile, $outpath)
}
Unzip "C:\cwagent\cwagent.zip" "C:\cwagent"
cd "C:\cwagent"
.\install.ps1
wget https://YOUR-PUBLIC-URL-HERE-WITH-CONFIG-FILE -OutFile "C:\Program Files\Amazon\AmazonCloudWatchAgent\config.json"
cd “C:\Program Files\Amazon\AmazonCloudWatchAgent”
.\amazon-cloudwatch-agent-ctl.ps1 -a fetch-config -m ec2 -c file:config.json -s
</powershell>