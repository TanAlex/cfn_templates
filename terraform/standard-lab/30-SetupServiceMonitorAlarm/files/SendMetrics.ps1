Import-Module AWSPowerShell
#Set the region of your cloudwatch
$region = (Invoke-WebRequest -UseBasicParsing -Uri http://169.254.169.254/latest/dynamic/instance-identity/document | ConvertFrom-Json | Select region).region
#Set-AWSDefaultRegion -Region $region
$AWS_DEFAULT_REGION = $region

#Feel free to change this to match any existing namespaces you might have.
$Namespace = 'service-monitor'

#The service Name to Monitor
#$serviceName = "Windows Update"
#This ${xx} is replaced by the hook:upload_s3.py by it's variable value
$ServiceName = "{{service_name}}"

#Update the log path, use this for troubleshooting. 
$logpath = "C:\OnicaTools\SendMetrics.log.txt"
if (!(Test-Path -Path $logpath)){
    New-Item -ItemType "file" -Path $logpath -Force
}
Get-Date -format "yyyy-MM-dd HH:mm"  | Out-File -FilePath $logpath -Force

#Use an AWS Service to get this systems Instance ID
$instanceId = (New-Object System.Net.WebClient).DownloadString("http://169.254.169.254/latest/meta-data/instance-id")

#$instanceId | Out-File -FilePath $logpath -Append -Force

# Associate current EC2 instance with your custom cloudwatch metric
$instanceDimension = New-Object -TypeName Amazon.CloudWatch.Model.Dimension;
$instanceDimension.Name = "instanceid";
$instanceDimension.Value = $instanceId;

$ServiceNames -split "," | %{
    $metrics = @();
    $serviceName = $_
    #Adjust this to  pick up your service or services, this will work fine with multiple services. 
    #$runningServices = Get-Service -Name MSSQLSERVER | ? { $_.Status -eq 'Running' }
    $runningServices = Get-Service -Name $serviceName
    $runningServices | Out-File -FilePath $logpath -Append

    # For each running service, add a metric to metrics collection that adds a data point to a CloudWatch Metric named 'Status' with dimensions: instanceid, servicename
    $runningServices | % { 
        $dimensions = @();
        $dimensions += $instanceDimension;

        $serviceDimension = New-Object -TypeName Amazon.CloudWatch.Model.Dimension;
        $serviceDimension.Name = "ServiceName"
        #$serviceDimension.Value = $_.Name;
        $serviceDimension.Value = $_.DisplayName;
        $dimensions += $serviceDimension;


        Write-Output "SD = $($serviceDimension.Value)" | Out-File -FilePath $logpath -Append  

        $metric = New-Object -TypeName Amazon.CloudWatch.Model.MetricDatum;
        $metric.Timestamp = [DateTime]::UtcNow;
        $metric.MetricName = 'ServiceStatus';
        $metric.Value = $(IF($_.Status -like "Running"){1}else{0}) ;
        $metric.Dimensions = $dimensions;


        $metrics += $metric;    
        
        #Write-Output "$metrics" | Out-File -FilePath $logpath -Append   
        #Write-Output "Service: $($_.Name) is running" | Out-File -FilePath $logpath -Append
    }

    # This cmdlet doesn't fail gracefully so we will run it in a try / catch. 
    try {
        Write-CWMetricData -Namespace $Namespace -MetricData $metrics -Verbose
    } catch {
        Write-Output "CWMetric Failed" | Out-File -FilePath $logpath -Append 
    }
}
