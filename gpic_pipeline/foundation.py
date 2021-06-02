## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0

from aws_cdk import (
    aws_ec2 as ec2,
    aws_s3 as s3,
    core    
)

class FoundationStack(core.Stack):
    
    bucket = s3.IBucket
    vpc = ec2.IVpc
    
    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Create S3 Bucket for other Game Production in the Cloud modules
        self.bucket = s3.Bucket(self, "gpic-pipeline-bucket")

        # Retrieve CIDR from CDK Context
        foundation_vpc_cidr = self.node.try_get_context("foundation_vpc_cidr")

        # Set default CIDR 
        if foundation_vpc_cidr is None:
            foundation_vpc_cidr = "10.0.0.0/16"

        # Create new VPC with one two private- and public subnet 
        self.vpc = ec2.Vpc(self, "VPC",
            cidr=foundation_vpc_cidr,
            nat_gateways=1,
            max_azs=2,
            subnet_configuration=[ec2.SubnetConfiguration(name="Public",subnet_type=ec2.SubnetType.PUBLIC),
            ec2.SubnetConfiguration(name="Private",subnet_type=ec2.SubnetType.PRIVATE)]
            )
        
        


        # Output the S3 Bucket name that can be used by other stacks in this application
        output = core.CfnOutput(self, "BucketName",
                                value=self.bucket.bucket_name,
                                description="Game Production in the Cloud pipeline bucket. This bucket will be used by other stacks in this application.")




