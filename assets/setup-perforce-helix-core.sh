#!/bin/bash
## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0

# Create filesystem on each of the block devices and mount them

mkfs -t xfs /dev/sdb && mkdir /hxdepots && mount /dev/sdb /hxdepots
mkfs -t xfs /dev/sdc && mkdir /hxlogs && mount /dev/sdc /hxlogs
mkfs -t xfs /dev/sdd && mkdir /hxmetadata && mount /dev/sdd /hxmetadata

# Modify /etc/fstab to mount device when booting up

blkid /dev/sdb | awk -v OFS="   " '{print $2,"/hxdepots","xfs","defaults,nofail","0","2"}' >> /etc/fstab
blkid /dev/sdc | awk -v OFS="   " '{print $2,"/hxlogs","xfs","defaults,nofail","0","2"}' >> /etc/fstab

blkid /dev/sdd | awk -v OFS="   " '{print $2,"/hxmetadata","xfs","defaults,nofail","0","2"}' >> /etc/fstab

# Add Perforce YUM repository and install Perforce
cat <<'EOF' >> /etc/yum.repos.d/perforce.repo
[perforce]
name=Perforce
baseurl=http://package.perforce.com/yum/rhel/7/x86_64/
enabled=1
gpgcheck=1
EOF

chown root:root /etc/yum.repos.d/perforce.repo
chmod 0644 /etc/yum.repos.d/perforce.repo

rpm --import https://package.perforce.com/perforce.pubkey

yum -y update
yum -y install helix-p4d 

# Remove AWS cli version 1 and install version 2
yum -y remove awscli

curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip" 
unzip /tmp/awscliv2.zip -d /tmp
./tmp/aws/install


# Install mailx - Needed by /p4/common/bin/recreate_offline_db.sh
yum -y install mailx

# Create P4admin user
adduser -g perforce -G adm,wheel p4admin

# Download an untar SDP
wget -O /tmp/sdp.tgz https://swarm.workshop.perforce.com/downloads/guest/perforce_software/sdp/downloads/sdp.Unix.tgz?v=%2314

tar xvfz /tmp/sdp.tgz --directory /hxdepots

# Modify mkdirs.cfg
cp /hxdepots/sdp/Server/Unix/setup/mkdirs.cfg /hxdepots/sdp/Server/Unix/setup/mkdirs.cfg.bak

INSTANCE_PRIVATE_DNS_NAME=$(hostname)

sed -i -e 's/DB1=.*/DB1=hxmetadata/g' /hxdepots/sdp/Server/Unix/setup/mkdirs.cfg
sed -i -e 's/DB2=.*/DB2=hxmetadata/g' /hxdepots/sdp/Server/Unix/setup/mkdirs.cfg
sed -i -e 's/DD=.*/DD=hxdepots/g' /hxdepots/sdp/Server/Unix/setup/mkdirs.cfg
sed -i -e 's/LG=.*/LG=hxlogs/g' /hxdepots/sdp/Server/Unix/setup/mkdirs.cfg
sed -i -e 's/OSUSER=.*/OSUSER=p4admin/g' /hxdepots/sdp/Server/Unix/setup/mkdirs.cfg
sed -i -e 's/OSGROUP=.*/OSGROUP=perforce/g' /hxdepots/sdp/Server/Unix/setup/mkdirs.cfg
sed -i -e 's/CASE_SENSITIVE=.*/CASE_SENSITIVE=0/g' /hxdepots/sdp/Server/Unix/setup/mkdirs.cfg
sed -i -e 's/MAILHOST=.*/MAILHOST=localhost/g' /hxdepots/sdp/Server/Unix/setup/mkdirs.cfg
sed -i -e 's/SSL_PREFIX=.*/SSL_PREFIX=/g' /hxdepots/sdp/Server/Unix/setup/mkdirs.cfg
sed -i -e "s/P4DNSNAME=.*/P4DNSNAME=$INSTANCE_PRIVATE_DNS_NAME/g" /hxdepots/sdp/Server/Unix/setup/mkdirs.cfg
sed -i -e 's/COMPLAINFROM_DOMAIN=.*/COMPLAINFROM_DOMAIN=amazonaws.com/g' /hxdepots/sdp/Server/Unix/setup/mkdirs.cfg

# Create symlinks
ln -s /opt/perforce/bin/p4 /hxdepots/sdp/Server/Unix/p4/common/bin/p4
ln -s /opt/perforce/sbin/p4d /hxdepots/sdp/Server/Unix/p4/common/bin/p4d

# Run SDP
/hxdepots/sdp/Server/Unix/setup/mkdirs.sh 1


# Add systemd configuration file for Perforce Helix Code
cat <<'EOF' >> /etc/systemd/system/p4d_1.service
[Unit]
Description=Helix Server Instance 1
Documentation=http://www.perforce.com/perforce/doc.current/manuals/p4sag/index.html
Requires=network.target network-online.target
After=network.target network-online.target

[Service]
Type=forking
TimeoutStartSec=60s
TimeoutStopSec=60s
ExecStart=/p4/1/bin/p4d_1_init start
ExecStop=/p4/1/bin/p4d_1_init stop
User=p4admin

[Install]
WantedBy=multi-user.target
EOF

chown p4admin:perforce /etc/systemd/system/p4d_1.service
chmod 0400 /etc/systemd/system/p4d_1.service

# Enable and start the Perforce Helix Code daemon
systemctl enable p4d_1
systemctl start p4d_1

# Persist ServerID
echo ${SERVER_ID} > /p4/1/root/server.id

/hxdepots/sdp/Server/setup/configure_new_server.sh 1


# Load Perforce environment variables, set the password persisted in the AWS Secrets Manager and put security measaurements in place
source /p4/common/bin/p4_vars 1

p4 configure set dm.password.minlength=32
p4 configure set dm.user.noautocreate=2
p4 configure set run.users.authorize=1
p4 configure set dm.keys.hide=2
p4 configure set security=3


perforce_default_password=$(/usr/local/bin/aws secretsmanager get-secret-value --secret-id PERFORCE_PASSWORD_ARN --query SecretString --output text)

#
# p4 passwd -P is not supported w/ security level set to 3 (See above)
echo -en "$perforce_default_password\n$perforce_default_password\n" | p4 passwd








