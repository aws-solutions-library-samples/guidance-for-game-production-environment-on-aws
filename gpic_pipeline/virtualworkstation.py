## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0

from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    core    
)


class VirtualWorkstationStack(core.Stack):

  def __init__(self, scope: core.Construct, id: str, bucket, vpc, **kwargs) -> None:
    super().__init__(scope,id,**kwargs)

    
    # Create Virtual Workstation Instance Role

    
    policy_statement_drivers = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["s3:GetObject",],
            resources=["arn:aws:s3:::ec2-windows-nvidia-drivers/*"]
        )

    policy_statement_bucket_list = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["s3:ListAllMyBuckets","s3:ListBucket"],
            resources=["arn:aws:s3:::*"]
        )
      
    policy_statement_bucket_object_actions = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["s3:*Object*",],
            resources=[bucket.bucket_arn+ "/*"]
        )

    policy_document = iam.PolicyDocument()
    policy_document.add_statements(policy_statement_drivers)
    policy_document.add_statements(policy_statement_bucket_list)
    policy_document.add_statements(policy_statement_bucket_object_actions)

    # Instance Role and SSM Managed Policy
    role = iam.Role(self, "VirutalWorkstationInstanceRole", assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"), inline_policies={"GPICDemo_VirtualWorkStationAccess" : policy_document})

    role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonEC2RoleforSSM"))
    


    # Create password for user Administrator in EC2 Secrets Manager and grant Virtual workstation instance the right to read this password.
    secret = secretsmanager.Secret(self, "Virtual Workstation Password")
    secret.grant_read(role)
    


    # Security Group for the Virtual Workstation
    securitygroup = ec2.SecurityGroup(self, "Virtual-Workstation-SecurityGroup",
      vpc=vpc,
      security_group_name="Virtual-Workstation-SecurityGroup",
      description="Allows remote access to the Virtual Workstation via RDP & Parsec, HP Anyware, and NICE DCV. In addition allows UE5 Swarm communication",
      allow_all_outbound=True
      )
    
    # Parameter for the trusted internal network
    
    virtual_workstation_trusted_internal_cidr = self.node.try_get_context("virtual_workstation_trusted_internal_cidr")

    # Define default trusted CIDR
    if virtual_workstation_trusted_internal_cidr is None:
      virtual_workstation_trusted_internal_cidr = "10.0.0.0/16"

    # Parameter for the trusted remote network
    virtual_workstation_trusted_remote_cidr = self.node.try_get_context("virtual_workstation_trusted_remote_cidr")

    if virtual_workstation_trusted_remote_cidr is None:
      virtual_workstation_trusted_remote_cidr = "0.0.0.0/0"



    # Allow Swarm and ICMP ping from trusted interal CIDR prefix
    securitygroup.add_ingress_rule(ec2.Peer.ipv4(virtual_workstation_trusted_internal_cidr), ec2.Port.tcp_range(8008,8009), 'Allow Trusted IP Swarm TCP')
    securitygroup.add_ingress_rule(ec2.Peer.ipv4(virtual_workstation_trusted_internal_cidr), ec2.Port.icmp_ping(), 'Allow Trusted IP Swarm ICMP Ping')

    # Allow RDP from trusted remote CIDR prefix
    securitygroup.add_ingress_rule(ec2.Peer.ipv4(virtual_workstation_trusted_remote_cidr),ec2.Port.tcp(3389), "Allow Trusted Remote CIDR to access Virtual Workstation via RDP")

    # Allow Parsec from trusted remote CIDR prefix
    securitygroup.add_ingress_rule(ec2.Peer.ipv4(virtual_workstation_trusted_remote_cidr),ec2.Port.tcp(1666), "Allow Trusted Remote CIDR to access Virtual Workstation via Parsec")

    # Allow PCoIP from trusted remote CIDR prefix
    securitygroup.add_ingress_rule(ec2.Peer.ipv4(virtual_workstation_trusted_remote_cidr),ec2.Port.tcp(4172), "Allow Trusted Remote CIDR to access Virtual Workstation via PCoIP (Session Establishment)")
    securitygroup.add_ingress_rule(ec2.Peer.ipv4(virtual_workstation_trusted_remote_cidr),ec2.Port.tcp(443), "Allow Trusted Remote CIDR to access Virtual Workstation via PCoIP (Client Authentication)")
    securitygroup.add_ingress_rule(ec2.Peer.ipv4(virtual_workstation_trusted_remote_cidr),ec2.Port.udp(4172), "Allow Trusted Remote CIDR to access Virtual Workstation via PCoIP (PCoIP Session Data)")

    # Allow NICE DCV from trusted remote CIDR prefix
    securitygroup.add_ingress_rule(ec2.Peer.ipv4(virtual_workstation_trusted_remote_cidr),ec2.Port.tcp(8443), "Allow Trusted Remote CIDR to access Virtual Workstation via NICE DCV")



    # Lookup latest Windows Server 2019
    basewindows = ec2.MachineImage.latest_windows(ec2.WindowsVersion.WINDOWS_SERVER_2019_ENGLISH_FULL_BASE);
        
    # Parameter for the instance type of the Virtual Workstation
    instance_type = self.node.try_get_context("virtual_workstation_instance_type")

    # Define default instance type of the Virtual Workstation
    if instance_type is None:
      instance_type = "g4dn.4xlarge"

    root_volume_size = self.node.try_get_context("virtual_workstation_root_volume_size")

    if root_volume_size is None:
      root_volume_size = 200

    # Define C: -drives size for Virtual Workstation
    root_device = ec2.BlockDevice(
      device_name='/dev/sda1',
      volume=ec2.BlockDeviceVolume.ebs(
        volume_size=root_volume_size,
        delete_on_termination=True
      ),
    )

   
    with open('assets/setup-virtual-workstation.ps1', 'r') as user_file:
            user_data = user_file.read()

    user_data = user_data.replace("ADMIN_PASSWORD_SECRET_ARN", secret.secret_full_arn)

    
    # Launch the Virtual Workstation instance
    virtual_workstation = ec2.Instance(self, "Virtual Workstation",
      instance_type=ec2.InstanceType(instance_type),
      machine_image=basewindows,
      vpc = vpc,
      vpc_subnets = ec2.SubnetSelection(subnet_type=ec2.SubnetType('PUBLIC')),
      role = role,
      security_group=securitygroup,
      block_devices=[root_device],
      user_data=ec2.UserData.custom(user_data)
    )
    

    # Create and associate static public IP adress
    ec2.CfnEIP(self, "VirtualWorkstationEIP",
      instance_id=virtual_workstation.instance_id
      
    )
    
    # Output the Public IP adress of the Virtual Workstation
    core.CfnOutput(self, "VirtualWorkstationPublicIp",
                                value=virtual_workstation.instance_public_ip,
                                description="The public IP of the virtual Workstation")
    core.CfnOutput(self, "VirtualWorkstationSecretName",
                                value=secret.secret_name,
                                description="The name of secret in the AWS Secrets Manager. Please open the AWS Secrets Manager to retrieve the password for the user 'Administrator'.")

    


    
    




