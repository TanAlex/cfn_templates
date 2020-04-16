# To complete the info dump and provide a trail for auditors. 
# https://docs.aws.amazon.com/AWSEC2/latest/WindowsGuide/ec2launch-download.html gives you a link to the latest EC2Launch 
# which has several ps1 scripts, there is one in the path Module/Scripts/New-RandomPassword.ps1 which contains the above referenced function.

function New-RandomPassword
{
    $password = ""

    do
    {
        # 1024 bytes are randomly generated.
        $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
        $randomBytes = New-Object Byte[] 1024
        $rng.GetBytes($randomBytes)

        # Special character contains the following: ()!@$%-=.?*;& 
        $specialChars = @(40, 41, 33, 64, 36, 37, 45, 61, 46, 63, 42, 59, 38) 

        # First 32 characters that meet the given conditions are picked from the random bytes.
        $password = [System.Text.Encoding]::ASCII.GetString(($randomBytes | where { `
                                                            ($_ -ge 97 -and $_ -le 122) -or ` # a - z
                                                            ($_ -ge 65 -and $_ -le 90) -or  ` # A - Z
                                                            ($_ -ge 50 -and $_ -le 57) -or  ` # 2 - 9
                                                            ($specialChars -contains $_) }) ` # ()!@$%-=.?*;& 
                                                            )

        # Passwords must contain characters from three of the four categories and longer than 32
    } while (-not (Confirm-Password -Password $password) -or $password.Length -lt 32) 

    return $password.Substring(0, 32)
}