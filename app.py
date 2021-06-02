#!/usr/bin/env python3
## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0


from aws_cdk import core
import os

from gpic_pipeline.foundation import FoundationStack
from gpic_pipeline.virtualworkstation import VirtualWorkstationStack
from gpic_pipeline.unrealengineswarmcluster import UnrealEngineSwarmClusterStack
from gpic_pipeline.perforcehelixcore import PerforceHelixCoreStack

app = core.App()

foundation_stack = FoundationStack(app, "gpic-pipeline-foundation" , env={'region': os.environ['CDK_DEFAULT_REGION']})

perforce_stack = PerforceHelixCoreStack(app, "gpic-pipeline-perforce-helix-core", foundation_stack .vpc, env={'region': os.environ['CDK_DEFAULT_REGION']})

virtual_desktop_stack = VirtualWorkstationStack(app, "gpic-pipeline-virtual-workstation", foundation_stack .vpc, env={'region': os.environ['CDK_DEFAULT_REGION']})

unreal_engine_swarm_cluster_stack = UnrealEngineSwarmClusterStack (app, "gpic-pipeline-swarm-cluster", foundation_stack.bucket, foundation_stack.vpc,env={'region': os.environ['CDK_DEFAULT_REGION']})


app.synth()
