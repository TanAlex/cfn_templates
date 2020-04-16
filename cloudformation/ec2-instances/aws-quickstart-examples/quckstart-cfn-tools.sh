#!/usr/bin/bash -e
# AWS Reference Common Linux Tools
# authors: tonynv@amazon.com, andglenn@amazon.com
#

# Supported only while bootstrapping Amazon ec2:
#
# -Amazon Linux2        
# -Red Hat Enterprise Linux 7   
# -Ubuntu 18.04         
# -SUSE Linux Enterprise 12     
#
# -Centos 7  (no ci tests)                   
# -Fedora 25 (no ci tests)            
#  Deprecated 14.04 (no future support)
#

# Configuration
#
PROGRAM='AWS Reference Linux Common Tools'

# Usage
#
# To use the functions defined here (source this file):
# Example:
#   load script into scripts
#   source quickstart-cfn-tools.source
#   # To print os type to std out
#   get_os-type
#   # to assign the os type to a variable OS
#   get_os-type OS
#


# Detects operating system type and return value
# If no variable is passed in function will print to std-out
#

function qs_int_set_svc_executable(){
    if [[ $(which systemctl) ]]; then
        export qs_svc_executable="systemd"
    else
        export qs_svc_executable="sysvinit"
    fi
}

function qs_int_is_svc_active(){
    case ${qs_svc_executable} in
        systemd)
            systemctl is-active --quiet ${1}.service
            ;;
        sysvinit)
            service ${1} status
            ;;
    esac
}

function qs_int_service_restart() {
    case ${qs_svc_executable} in
        systemd)
            systemctl restart ${1}.service
            ;;
        sysvinit)
            service ${1} restart
            ;;
    esac
}

function qs_get-ostype() {
    local __return=$1
    DETECTION_STRING="/etc/*-release"
    if [[ $(ls ${DETECTION_STRING}) ]]; then
	OS=$( cat /etc/*-release \
	| grep ^ID= |awk -F= '{print $2}'\
	| tr -cd [:alpha:])
        if [ "${OS}" == "ol" ];then
            OS="rhel"
        fi
        if [ $? -eq 0 ] && [ "$__return" ];then
            eval $__return="${OS}"
            return 0
        elif [ $OS ]; then
            echo $OS
            return 0;
        else
             echo "Unknown"
        fi
    else
        if [ "$__return" ]; then
                __return="Unknown"
                return 1
        else
                echo "Unknown"
                return 1;
        fi
    fi
}

# Returns operating system version or return 1
# If no variable is passed in function will print to std-out
#
function qs_get-osversion () {
    local __return=$1
    DETECTION_STRING="/etc/*-release"
    if [[ $(ls ${DETECTION_STRING})  ]]; then
        OSLEVEL=$(cat ${DETECTION_STRING} \
        | grep VERSION_ID \
        | tr -d \" \
        | awk -F= '{print $2}')

        if [ $? -eq 0 ] && [ "$__return" ];then
            eval $__return="${OSLEVEL}"
            return 0
        elif [ $OS ]; then
            echo $OSLEVEL
            return 0;
        else
            echo "Unknown"
        fi
    else
        if [ "$__return" ]; then
            __return="Unknown"
            return 1
        else
            echo "Unknown"
            return 1;
        fi
    fi
}

# If python is install returns default python path
# If no variable is passed in function will print to std-out
#
function qs_get-python-path() {
    local __return=$1
    # Set PYTHON_EXECUTEABLE to default python version
    if command -v python > /dev/null 2>&1; then
       PYTHON_EXECUTEABLE=$(which python)
    else
       PYTHON_EXECUTEABLE=$(which python3)
    fi

    #Return python path or return code (1)
    if [ $PYTHON_EXECUTEABLE ] && [ "$__return" ]; then
        eval $__return="${PYTHON_EXECUTEABLE}"
        return 0
    elif [ $PYTHON_EXECUTEABLE ]; then
        echo $PYTHON_EXECUTEABLE
        return 0;
    else
        echo "Python Not installed"
        return 1
    fi

}

# Relax require tty
#
function  qs_notty() {
    qs_get-ostype INSTANCE_OSTYPE
    qs_get-osversion INSTANCE_OSVERSION
    echo "[INFO] Relax tty requirement"
    if [ "$INSTANCE_OSTYPE" == "rhel" ]; then
       sed -i -e "s/Defaults    requiretty/Defaults    \!requiretty/" /etc/sudoers
    elif [ "$INSTANCE_OSTYPE" == "centos" ]; then
       sed -i -e "s/Defaults    requiretty/Defaults    \!requiretty/" /etc/sudoers
    fi
}


# Installs pip from bootstrap.pypa
#
function  qs_bootstrap_pip() {
    qs_notty
    echo "[INFO] Check for python/pip"
    qs_get-python-path PYTHON_EXECUTEABLE
    if  [ $? -eq 0 ] ;then
        command -v pip > /dev/null 2&>1
        if [ $? -eq 1 ]; then
            curl --silent \
             --show-error \
            --retry 5 \
            https://bootstrap.pypa.io/get-pip.py | sudo $PYTHON_EXECUTEABLE
        fi
    else
        echo $PYTHON_EXECUTEABLE
        exit 1
    fi
}

# Installs and configures cloudwatch
# Then adds /var/log/syslog to log collection
function  qs_cloudwatch_tracklog() {
    local -r __log="$@"
    cat cloudwatch_logs.stub | sed s,__LOG__,$__log,g >> /var/awslogs/etc/awslogs.conf
    qs_int_service_restart awslogs
}

function  qs_cloudwatch_install() {
    echo "[INFO] Install AWS CloudWatch Agent"
    REGION=`curl http://169.254.169.254/latest/dynamic/instance-identity/document|grep region|awk -F\" '{print $4}'`
    sudo echo $'[general]\nstate_file = /var/awslogs/state/agent-state' >awslogs.conf
    cat cloudwatch_logs.stub | sed s,__LOG__,/var/log/syslog,g >> awslogs.conf
    qs_get-python-path PYTHON_EXECUTEABLE
    if  [ $? -eq 0 ] ;then
    curl --silent \
     --show-error \
    --retry 5 \
    https://s3.amazonaws.com/aws-cloudwatch/downloads/latest/awslogs-agent-setup.py -O
    sudo $PYTHON_EXECUTEABLE ./awslogs-agent-setup.py --region $REGION -c awslogs.conf -n
    else
      qs_int_is_svc_active awslogs && echo "[INFO] Cloudwatch Service is running"
        exit 1
    fi
}


# Added EPEL enabler
#
function  qs_enable_epel() {
    qs_get-ostype INSTANCE_OSTYPE
    qs_get-osversion INSTANCE_OSVERSION
    echo "[INFO] Enable epel-release-latest-7"
    if [ "$INSTANCE_OSTYPE" == "rhel" ]; then
        yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
    elif [ "$INSTANCE_OSTYPE" == "centos" ]; then
        yum install -y epel-release
    elif [ "$INSTANCE_OSTYPE" == "fedora" ]; then
        echo "Enabled!"
    else
        exit 1
    fi

}

# Updates supported operating systems to latest
# or
# exit with code (1)
#
# If no variable is passed in function will print to std-out
#
function qs_update-os() {
    # Assigns values to INSTANCE_OSTYPE
    qs_get-ostype INSTANCE_OSTYPE
    qs_get-osversion INSTANCE_OSVERSION

    echo "[INFO] Start OS Updates"
    if [ "$INSTANCE_OSTYPE" == "amzn" ]; then
        yum update -y
    elif [ "$INSTANCE_OSTYPE" == "ubuntu" ]; then
        apt update -y
    elif [ "$INSTANCE_OSTYPE" == "rhel" ]; then
        yum update -y
    elif [ "$INSTANCE_OSTYPE" == "centos" ]; then
        yum update -y
    elif [ "$INSTANCE_OSTYPE" == "fedora" ]; then
        dnf update -y
    elif [ "$INSTANCE_OSTYPE" == "sles" ]; then
        zypper -n refresh && zypper -n update
    else
        exit 1
    fi
    echo "[INFO] Finished OS Updates"
}

# Install aws-cfn-bootstrap tools
function qs_aws-cfn-bootstrap() {
    # Assigns values to INSTANCE_OSTYPE
    qs_get-ostype INSTANCE_OSTYPE
    qs_get-osversion INSTANCE_OSVERSION

    echo "[INSTALL aws-cfn-bootstrap tools]"
    if [ "$INSTANCE_OSTYPE" == "amzn" ] && [ "$INSTANCE_OSVERSION" == "2" ]; then
            sudo cp scripts/opt-aws.sh /etc/profile.d/
            sudo ln -s /opt/aws/bin/cfn-* /usr/bin/
            export PATH=$PATH:/opt/aws/bin
            sudo  yum install python3-pip
            sudo yum install python3-pip
            sudo alternatives --set python /usr/bin/python3
    elif [ "$INSTANCE_OSTYPE" == "amzn" ]; then
            echo "Warning: Consider upgrading to Amazon Linux 2"
            sudo cp scripts/opt-aws.sh /etc/profile.d/
            sudo ln -s /opt/aws/bin/cfn-* /usr/bin/
            export PATH=$PATH:/opt/aws/bin
            sudo  yum install python3-pip
            sudo yum install python36-pip
            sudo alternatives --set python /usr/bin/python3.6
    elif [ "$INSTANCE_OSTYPE" == "ubuntu" ] && [ "$INSTANCE_OSVERSION" == "16.04" ]; then
        sudo apt-get update -y
        sudo apt-get install python2.7 python-pip -y
        sudo pip2 install https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-latest.tar.gz
    elif [ "$INSTANCE_OSTYPE" == "ubuntu" ] && [ "$INSTANCE_OSVERSION" == "18.04" ]; then
        sudo apt-get update -y
        sudo apt-get install python-pip -y
        sudo pip2 install https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-latest.tar.gz
    elif [ "$INSTANCE_OSTYPE" == "ubuntu" ] && [ "$INSTANCE_OSVERSION" == "14.04" ]; then
        echo "Warning: ubuntu 14.04 will be deprecated in the next release"
        sudo apt-get update -y
        sudo apt-get install python2.7 python-pip -y
        sudo pip2 install https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-latest.tar.gz
    elif [ "$INSTANCE_OSTYPE" == "rhel" ]; then
        yum update -y
        pip install https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-latest.tar.gz
    elif [ "$INSTANCE_OSTYPE" == "centos" ]; then
        yum update -y
        qs_bootstrap_pip
        pip install https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-latest.tar.gz
    elif [ "$INSTANCE_OSTYPE" == "fedora" ]; then
        pip install https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-latest.tar.gz
    elif [ "$INSTANCE_OSTYPE" == "sles" ]; then
        zypper -n refresh && zypper -n update
        zypper -n install python2-pip
        pip2.7 install https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-latest.tar.gz
        echo "[WARNING] not implemeneted"
    else
        exit 1
    fi

    if [ $(which cfn-signal) ];then
      echo "[FOUND] (cfn-signal)"
    else
      echo "[ERROR] (cfn-signal) not installed!!"
      exit 1
    fi
}


function qs_err() {
        touch /var/tmp/stack_failed
        echo "[FAILED] @ $1" >>/var/tmp/stack_failed
        echo "[FAILED] @ $1"
}

function qs_status() {
    if [ -f /var/tmp/stack_failed ]; then
        printf 1;
        return 1
    else
        printf 0
        return 0;
    fi
}

function qs_status.clean() {
    if [ -f /var/tmp/stack_failed ]; then
        echo "clean failed state"
        rm /var/tmp/stack_failed
    else
        echo "failed state not active"
    fi
}

function available_functions() {
echo "--------------------------------"
echo "Available quickstart_functions:
    #qs_err
    #qs_status
    #qs_get-ostype
    #qs_get-osversion
    #qs_get-python-path
    #qs_bootstrap_pip
    #qs_update-os
    #qs_enable_epel
    #qs_notty
    #qs_aws-cfn-bootstrap
    #qs_cloudwatch_tracklog
    #qs_cloudwatch_install
    #qs_retry_command"
echo "--------------------------------"
}

function install_dependancies() {
# Install dependencies
# Assigns values to INSTANCE_
#
qs_get-ostype INSTANCE_OSTYPE
qs_get-osversion INSTANCE_OSVERSION


check_cmd() {
    if hash $1 &>/dev/null; then
        echo "[INFO] Dependencies Met!"
        return 0
    else
        echo "[INFO] Installing Dependencies"
        return 1
    fi
}

if [ "$INSTANCE_OSTYPE" == "amzn" ]; then
    check_cmd curl 'yum clean all && yum install curl -y'
elif [ "$INSTANCE_OSTYPE" == "ubuntu" ]; then
    check_cmd curl;[[ $? -eq 1 ]] && apt update && apt install curl -y || return 0

elif [ "$INSTANCE_OSTYPE" == "rhel" ]; then
    check_cmd curl;[[ $? -eq 1 ]] && yum clean && yum install curl -y || return 0

elif [ "$INSTANCE_OSTYPE" == "centos" ]; then
    check_cmd curl;[[ $? -eq 1 ]] && yum clean && yum install curl -y || return 0

elif [ "$INSTANCE_OSTYPE" == "fedora" ]; then
    check_cmd curl;[[ $? -eq 1 ]] && dnf clean && dnf install curl -y || return 0

elif [ "$INSTANCE_OSTYPE" == "sles" ]; then
    check_cmd curl;[[ $? -eq 1 ]] && zypper -n refresh && zypper -n install curl || return 0
else
    echo "[FAIL] : Dependencies not satisfied!"
    exit 1
fi

}

# $1 = NumberOfRetries $2 = Command
# qs_retry_command 10 some_command.sh
# Command will retry with linear back-off
function qs_retry_command() {
    local -r __tries="$1"; shift
    local -r __run="$@"
    local -i __backoff_delay=2

    until $__run
        do
                if (( __current_try == __tries ))
                then
                        echo "Tried $__current_try times and failed!"
                        return 1
                else
                        echo "Retrying ...."
                        sleep $((((__backoff_delay++)) + ((__current_try++))))
                fi
        done

}

# start exec
available_functions
install_dependancies
# end exec