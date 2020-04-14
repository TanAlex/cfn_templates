# Run the followin to deploy
cd stacker/modules/customer_servers/templates/nagios-server/
stacker build -r us-east-1 ./us-east-1-nagios.env ./nagios-server-deploy.yaml


# Login to the just created ec2 instance
# ssh -i ssh/sturdy_hubble_id_rsa.pem ec2-user@10.30.4.147

# the following can be added to user-data, but we are going to create AMI anyway

# overwrite /etc/resolv.conf, the current one use DHCP option to use local windows AD server 
cp /etc/resolv.conf /etc/resolv.conf.save
echo "nameserver 8.8.8.8" > /etc/resolv.conf

# Update the packages on your instance
yum update -y

# Install Docker
yum install docker -y

# Add the ec2-user to the docker group so you can execute Docker commands without using sudo.
usermod -a -G docker ec2-user

# Start the Docker Service
service docker start

# Backup htpasswd.users and generate new one
# cp /opt/nagios/etc/htpasswd.users /opt/nagios/etc/htpasswd.users.save

mkdir /opt/nagios
mkdir /opt/nagios/etc
mkdir /opt/nagios/var
mkdir /opt/nagiosgraph
mkdir /opt/nagiosgraph/etc
mkdir /opt/nagiosgraph/var
mkdir /opt/Custom-Nagios-Plugins

# Download nagios/etc from S3
cd /opt/nagios
aws s3 cp s3://hubble-config-naprod1/configs-nagios-server/nagios.config.zip nagios.config.zip
unzip nagios.config.zip

cd /
docker run --name nagios4 -d\
  -v /opt/nagios/etc/:/opt/nagios/etc/ \
  -v /opt/nagios/var:/opt/nagios/var/ \
  -v /opt/Custom-Nagios-Plugins:/opt/Custom-Nagios-Plugins \
  -v /opt/nagiosgraph/var:/opt/nagiosgraph/var \
  -v /opt/nagiosgraph/etc:/opt/nagiosgraph/etc \
  --restart unless-stopped
  -p 0.0.0.0:80:80 jasonrivers/nagios:latest

# login to the container
docker exec -it nagios4 bash

use `htpasswd -c htpasswd nagiosadmin` to generate passwd

$ pip install awscli