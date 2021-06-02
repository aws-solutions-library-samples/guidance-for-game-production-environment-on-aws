## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0

from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_autoscaling as autoscaling,
    aws_secretsmanager as secretsmanager,
    core    
)


class PerforceHelixCoreStack(core.Stack):
  def __init__(self, scope: core.Construct, id: str, vpc, **kwargs) -> None:
    
    super().__init__(scope, id, **kwargs)


    # Instance Role and SSM Managed Policy
    role = iam.Role(self, "PerforceHelixCoreInstanceRole", assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),role_name="PerforceHelixCoreInstanceRole")

    
    role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonEC2RoleforSSM"))

     # Create password for Perforce administrative user in EC2 Secrets Manager and grant Perforce Helix Core instance the right to read this password.

    secret_generator = secretsmanager.SecretStringGenerator(exclude_characters="'\"",
    exclude_punctuation=True,
    include_space=False,
    password_length=32)

    secret = secretsmanager.Secret(self, "Perforce Helix Core Password",
    generate_secret_string=secret_generator)
    secret.grant_read(role)

    


    # Security Group for the Perforce instance that allows communication
    securitygroup = ec2.SecurityGroup(self, "PerforceHelixCoreSecurityGroup",
        vpc=vpc,
        security_group_name="Perforce-SecurityGroup",
        description="Allows access to the Perforce server",
        allow_all_outbound=True
    )
    


     # Parameter for the trusted internal network
    perforce_trusted_internal_cidr = self.node.try_get_context("perforce_trusted_internal_cidr")

    # Define default trusted CIDR
    if perforce_trusted_internal_cidr is None:
      perforce_trusted_internal_cidr = "10.0.0.0/16"

    securitygroup.add_ingress_rule(ec2.Peer.ipv4(perforce_trusted_internal_cidr), ec2.Port.tcp(1666), 'Allow access to Perforce Helix Core')


    # Lookup latest Amazon Linux2 AMI
    linux_image = ec2.MachineImage.latest_amazon_linux(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2)

    # Parameter for the instance type of the Perforce Helix Core Instance
    instance_type = self.node.try_get_context("perforce_instance_type")

    # Define default instance type of the Perforce Helix Core Instance
    if instance_type is None:
      instance_type = "g4dn.4xlarge"

    server_hostname = self.node.try_get_context("perforce_server_hostname")
    if server_hostname is None:
      server_hostname = "pvs-aws-01"

  
    # Setup depot volume
    depot_volume_size = self.node.try_get_context("perforce_depot_volume_size")

    if depot_volume_size is None:
      depot_volume_size = 1024

    depot_volume_type = self.node.try_get_context("perforce_depot_volume_type")

    depot_volume_type = self.get_volume_type_from_string(depot_volume_type)
    if depot_volume_type is None:
      depot_volume_type = autoscaling.EbsDeviceVolumeType.ST1

  
    depot_block_device = ec2.BlockDevice(
      device_name='/dev/sdb',
      volume=ec2.BlockDeviceVolume.ebs(
        volume_type= depot_volume_type,
        volume_size=depot_volume_size,
        delete_on_termination=True
        
      ),
    )

  
    # Setup log volume
    log_volume_size = self.node.try_get_context("perforce_log_volume_size")

    if log_volume_size is None:
      log_volume_size = 128

    log_volume_type = self.node.try_get_context("perforce_log_volume_type")

    log_volume_type = self.get_volume_type_from_string(log_volume_type)
    if log_volume_type is None:
      log_volume_type = autoscaling.EbsDeviceVolumeType.gp2

  
    log_block_device = ec2.BlockDevice(
      device_name='/dev/sdc',
      volume=ec2.BlockDeviceVolume.ebs(
        volume_type= log_volume_type,
        volume_size=log_volume_size,
        delete_on_termination=True
      ),
    )
    


    # Setup metadata volume
    metadata_volume_size = self.node.try_get_context("perforce_metadata_volume_size")

    if metadata_volume_size is None:
      metadata_volume_size = 64

    metadata_volume_type = self.node.try_get_context("perforce_metadata_volume_type")

    metadata_volume_type = self.get_volume_type_from_string(metadata_volume_type)
    if metadata_volume_type is None:
      metadata_volume_type = autoscaling.EbsDeviceVolumeType.gp2

  
    metadata_block_device = ec2.BlockDevice(
      device_name='/dev/sdd',
      volume=ec2.BlockDeviceVolume.ebs(
        volume_type= metadata_volume_type,
        volume_size=metadata_volume_size,
        delete_on_termination=True
      ),
    )


    # Read UserData Script an replace placeholders
    with open('assets/setup-perforce-helix-core.sh', 'r') as user_data_file:
      user_data = user_data_file.read()
    
    server_id = self.node.try_get_context("perforce_server_id")

    if server_id is None:
      server_id = "master.1"


    user_data = user_data.replace("SERVER_ID", server_id)      

    user_data = user_data.replace("PERFORCE_PASSWORD_ARN", secret.secret_full_arn)
  
  

    # Launch the Perforce Helix Server
    instance = ec2.Instance(self, server_hostname,
      instance_type=ec2.InstanceType(instance_type),
      machine_image=linux_image,
      vpc = vpc,
      vpc_subnets = ec2.SubnetSelection(subnet_type=ec2.SubnetType('PRIVATE')),
      role = role,
      security_group=securitygroup,
      block_devices=[depot_block_device, log_block_device,metadata_block_device],
      user_data=ec2.UserData.custom(user_data)
    )

    # Output Information of the Perforce Helix Core Server
    core.CfnOutput(self, "PerforceHelixCorePrivateDNS", value=instance.instance_private_dns_name, description="The private DNS name of the Perforce Helix Core Server.")

    core.CfnOutput(self, "PerforceHelixCorePrivateIP",value=instance.instance_private_ip, description="The private IP address of the Perforce Helix Core Server.")

    core.CfnOutput(self, "PerforceHelixCoreSecretName",value=secret.secret_name, description="The name of secret in the AWS Secrets Manager. Please open the AWS Secrets Manager to retrieve the password for the user 'perforce'.")

  # Helper method
  def get_volume_type_from_string(self, volume_string):

    if type(volume_string) != str:
      return None
    
    if volume_string.lower() == "gp2":
      return autoscaling.EbsDeviceVolumeType.GP2
    elif volume_string.lower() == "gp3":
      return autoscaling.EbsDeviceVolumeType.GP3
    elif volume_string.lower() == "io1":
      return autoscaling.EbsDeviceVolumeType.IO1
    elif volume_string.lower() == "st1":
      return autoscaling.EbsDeviceVolumeType.ST1
    elif volume_string.lower() == "sc1":
      return autoscaling.EbsDeviceVolumeType.SC1
    elif volume_string.lower() == "standard":
      return autoscaling.EbsDeviceVolumeType.STANDARD
    elif volume_string.lower() == "io2":
      return autoscaling.EbsDeviceVolumeType.IO2
    else:
       return None

  
    
  

    





        
