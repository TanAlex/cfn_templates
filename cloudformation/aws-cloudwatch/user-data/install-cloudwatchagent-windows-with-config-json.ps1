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

# Create CWAgent config file



$config_file = "C:\Program Files\Amazon\AmazonCloudWatchAgent\config.json"
$config = @'
{
    "metrics": {
        "append_dimensions": {
            "AutoScalingGroupName": "${aws:AutoScalingGroupName}",
            "ImageId": "${aws:ImageId}",
            "InstanceId": "${aws:InstanceId}",
            "InstanceType": "${aws:InstanceType}"
        },
        "aggregation_dimensions": [
            [
              "InstanceId"
            ],
            [
              "AutoScalingGroupName"
            ],
            [
              "InstanceId",
              "instance",
              "objectname"
            ],
            [
              "InstanceId",
              "instance"
            ]
        ],
        "metrics_collected": {
            "LogicalDisk": {
                "measurement": [
                    "% Free Space"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "Memory": {
                "measurement": [
                    "% Committed Bytes In Use"
                ],
                "metrics_collection_interval": 60
            },
            "Paging File": {
                "measurement": [
                    "% Usage"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "PhysicalDisk": {
                "measurement": [
                    "% Disk Time"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "Processor": {
                "measurement": [
                    "% User Time"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            }
        }
    }
}
'@

$config | Out-File -FilePath $config_file -Encoding ASCII

cd "C:\Program Files\Amazon\AmazonCloudWatchAgent"
.\amazon-cloudwatch-agent-ctl.ps1 -a fetch-config -m ec2 -c file:config.json -s



# Reboot
# Restart-Computer –delay 15
</powershell>