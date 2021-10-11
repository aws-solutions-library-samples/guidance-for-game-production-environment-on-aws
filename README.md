# Game Production in the Cloud pipeline

- [Game Production in the Cloud pipeline](#game-production-in-the-cloud-pipeline)
- [Description](#description)
- [Contents](#contents)
- [Architecture Diagram](#architecture-diagram)
- [Deployment steps](#deployment-steps)
  - [Initiate CDK](#initiate-cdk)
  - [Deployment of the Foundations Stack](#deployment-of-the-foundations-stack)
  - [Deployment of the Perforce Helix Core Stack](#deployment-of-the-perforce-helix-core-stack)
  - [Deployment & Setup of the Virtual Workstation Stack](#deployment--setup-of-the-virtual-workstation-stack)
    - [Deployment of the Virtual Workstaticn](#deployment-of-the-virtual-workstaticn)
    - [Setup of the Virtual Workstation](#setup-of-the-virtual-workstation)
    - [Deployment of the Unreal Engine 4 Swarm Cluster](#deployment-of-the-unreal-engine-4-swarm-cluster)
      - [Collecting dependencies](#collecting-dependencies)
      - [Deployment](#deployment)
      - [A look behind the curtains](#a-look-behind-the-curtains)
        - [Baking custom Windows AMI for UE4 Swarm](#baking-custom-windows-ami-for-ue4-swarm)
        - [Deploying UE4 Swarm Coordinator](#deploying-ue4-swarm-coordinator)
        - [Deploying UE4 Swarm Agent Auto Scaling Group](#deploying-ue4-swarm-agent-auto-scaling-group)
- [Finish](#finish)
- [Cleaning Up Resources](#cleaning-up-resources)
- [Extra Tips](#extra-tips)
  - [How to access the EC2 instances in the private subnets](#how-to-access-the-ec2-instances-in-the-private-subnets)
  - [How to acess the Unreal Engine 4 Swarm Agent logs?](#how-to-acess-the-unreal-engine-4-swarm-agent-logs)
  - [Updating CloudFormation templates after code changes](#updating-cloudformation-templates-after-code-changes)
- [Security](#security)
- [License](#license)

# Description

This example allows you to quickly evaluate some typical solution areas of a Game Production in the Cloud pipeline (GPIC). Remote workstation, version control and acceleration of computationally expensive process.

The CDK (or CloudFormation templates) creates a new AWS Virtual Private Cloud (VPC), a Virtual Workstation, a Perforce Helix Core server and an Unreal Engine 4 Swarm Cluster. The latter can be used to accelerate Unreal Engine 4 lighting builds using the vast compute resources available in AWS.

You can also connect your existing local workstation to the HelixCore Perforce Server and the Unreal Engine 4 Swarm Cluster via Site to Site VPN or Client VPN.

# Contents

This project repository contains:

- **Infrastructure deployment automation** that deploys required infrastructure resources using AWS CDK or AWS CloudFormation.
- **PowerShell Scripts** that are used to:
- - Collect dependencies from your Unreal Engine 4 installation
- - Setup the Unreal Engine 4 Swarm- coordinator and agents.
- - Setup the Virtual Workstation
- **Bash Scripts** to setup a secure Perforce Helix Core Server

# Architecture Diagram

![Architecture](architecture.png "Architecture")

# Deployment steps

On a high level the deployment is split into four (4) parts.

The first step is to deploy the _gpic-pipeline-foundation_ stack. This will setup a VPC, private- and public -subnets, the network routing and a S3 bucket which is needed in subsequent steps.

The second step is to deploy the _gpic-pipeline-perforce-helix-core_ stack. This will deploy a secure Perforce Helix Core Server into one of the private subnets and configure it according to best-practices. Once this machine is up and running you can connect to it as user `perforce` using P4V/P4/P4Admin. The password for the user `perforce` can be retrieved via [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/).

The third step is to deploy the _gpic-pipeline-virtual-workstation_ stack. Once this machine is up and running you can connect to it as user `Administrator` via RDP using the public IP address (or the public DNS name). The password for the user `Administrator` can be retrieved via the [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/).

The last step is the deployment of the _gpic-pipeline-swarm-cluster_ stack, which will deploy a Unreal Engine 4 Swarm Coordinator into one of the private subnets as well as an Amazon EC2 AutoScaling consisting of Unreal Engine 4 Swarm agents.

For the best possible experience, we recommend to deploy this example in the AWS region closest to you.

## Initiate CDK

> This step is optional if you decide to use the CloudFormation templates in the `cloudformation` -directory.

This project uses a standard Python CDK project to deploy this example. If you don't have CDK installed, please follow the instructions at [AWS Cloud Development Kit](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html#getting_started_install) documentation.

When you have CDK and Python installed you can use following steps to initiate this project:

Create a python virtualenv

MacOS and Linux:

```
 python3 -m venv .venv
```

Windows

```
python -m venv .venv
```

After the virtualenv is created, you can use the following step to activate your virtualenv.

MacOS and Linux:

```
source .venv/bin/activate
```

Windows:

```
source.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
pip install -r requirements.txt
```

> If you run on a MacOS or Linux, you potentialy need to modify the file `cdk.json` to use the correct python version. This CDK application expects that `python` is a symlink to python3 or the binary for python verions 3.

## Deployment of the Foundations Stack

The Foundation stacks deploys an AWS Virtual Private Cloud (VPC) with two public subnets, two private subnets and a NAT Gateway. It also deploys a S3 bucket, which is utilized by the other stacks of this example.

You can deploy this stack with CDK or by using CloudFormation template. By default we will create a VPC with a CIDR prefix of `10.0.0.0/16` and allow traffic to the Virtual Workstation, the Perforce Helix Core Server and the Unreal Engine 4 Swarm coordinator and agents from CIDR Prefix `10.0.0.0/8`. In addition we will allow traffic from the CIDR prefix `0.0.0.0/0.` to the Virtual Workstation for ease of use. These values can be changed by editing the `cdk.json`-file and giving new values for `foundation_vpc_cidr`, `virtual_workstation_trusted_internal_cidr`, `virtual_workstation_trusted_remote_cidr', `unreal_engine_swarm_cluster_trusted_internal_cidr`and`perforce_trusted_internal_cidr`.

To deploy the foundation stack please run the following command:

```
cdk deploy gpic-pipeline-foundation
```

Alternatively you can use the `cloudformation/gpic-pipeline-foundation.yaml` template to create a CloudFormation stack called `gpic-pipeline-foundation` using the AWS Console and AWS CLI. If you want to customize the VPC CIDR you will need to edit the CloudFormation template or use the CDK to synthesize new one with the CDK context variable (see the [Tips](#extra-tips) section).

CLI example:

```
aws cloudformation create-stack --stack-name gpic-pipeline-foundation --template-body file://cloudformation/gpic-pipeline-foundation.yaml
```

Once the creation of resources is ready you can move to [next step](#deployment-of-the-perforce-helix-core-stack).

## Deployment of the Perforce Helix Core Stack

The Perforce Helix Core stack deploys an EC2 instance based on the latest Amazon Linux 2 AMI into one of the private subnets and setup the Perfore Helix Core daemon using [Perforce Helix Server Deployment Package (SDP)](https://swarm.workshop.perforce.com/projects/perforce-software-sdp/view/main/doc/SDP_Guide.Unix.pdf). In the default configuration access to this machine is only allowed by the CIDR prefix `10.0.0.0/8` on port 1666. These CIDR prefix can be changed by editing the `cdk.json` and mofifying the value of `perforce_trusted_internal_cidr`.

To deploy the Perforce Helix Core stack please run the following command:

```
cdk deploy gpic-pipeline-perforce-helix-core
```

Alternatively you can use the `cloudformation/gpic-pipeline-perforce-helix-core.yaml` template to create a CloudFormation stack called `gpic-pipeline-perforce-helix-core` using the AWS Console and AWS CLI. If you want to customize the VPC CIDR you will need to edit the CloudFormation template or use the CDK to synthesize new one with the CDK context variable (see the [Tips](#extra-tips) section).

CLI example:

```
aws cloudformation create-stack --stack-name gpic-pipeline-perforce-helix-core --template-body file://cloudformation/gpic-pipeline-perforce-helix-core.yaml --capabilities CAPABILITY_NAMED_IAM
```

To access the Perforce Helix Core server with the P4/P4V/P4Admin please use the user `perforce`. The password for this user can be obtained via the AWS Secrets Manager. To accees the server via Secure Shell (SSH), please use the AWS Systems Manager Session Manager.

Once the creation of resources is ready you can move to [next step](#deployment--setup-of-the-virtual-workstation-stack).

## Deployment & Setup of the Virtual Workstation Stack

### Deployment of the Virtual Workstation

The Virtual Workstation stack deploys an EC2 Instance based on the latest Microsoft Windows Server 2019 Base AMI in one of the public subnets. In this process we also:

- Set the password for the user "Administrator"
- Install the latest [NVIDIA Grid driver](https://docs.aws.amazon.com/AWSEC2/latest/WindowsGuide/install-nvidia-driver.html#nvidia-GRID-driver)
- Setup Windows 2019 Server firewall and allow ingress traffic for the following applications/protocols:
  - ICMP
  - PCoIP
  - Parsec
  - NICE-DCV
  - Unreal Engine 4 Swarm

Access to this virtual workstation is controlled by the variables `virtual_workstation_trusted_internal_cidr` and
`virtual_workstation_trusted_remote_cidr` in `cdk.json`.

To deploy the Virtual Workstation stack please run the following command:

```
cdk deploy gpic-pipeline-virtual-workstation
```

Alternatively you can use the `cloudformation/gpic-pipeline-virtual-workstation.yaml` template to create a CloudFormation stack called `gpic-pipeline-virtual-workstation` using the AWS Console and AWS CLI. If you want to customize the trusted CIDR's you will need to edit the CloudFormation template or use the CDK to synthesize new one with the CDK context variable (see the [Tips](#extra-tips) section).

CLI example:

```
aws cloudformation create-stack --stack-name gpic-pipeline-virtual-workstation --template-body file://cloudformation/gpic-pipeline-virtual-workstation.yaml --capabilities CAPABILITY_IAM
```

Once the creation of resources is finished you can move to [next step](#setup).

### Setup of the Virtual Workstation

To access the Virtual Workstation please use the public IP/DNS, which can be obtained via the Ouput values from CDK/CloudFormation stack or alternatively via the AWS Management Console.

Once you are connected via RDP, please download & install the following software:

- [Parsec](https://parsec.app/)
  - Steps:
    - Open a PowerShell and run the [script](https://github.com/parsec-cloud/Parsec-Cloud-Preparation-Tool#copy-this-code-into-powershell-you-may-need-to-press-enter-at-the-end), which is provided by Parsec in their GitHub repository
      - Question: Do you want this computer to log on to Windows automatically? Yes
    - Once the installation is finished, the script will open up an additional Powershell session to update the GPU driver. Please close this Powershell session and don't provide a ACCESS_KEY & SECRET_ACCESS_KEY. We have already-installed the latest NVIDIA Grid driver on the virtual workstation.
    - Close all remaining Powershell sessions
    - Sign-Up for a Parsec account or use an existing Parsec account to login
- [Perforce Helix](https://www.perforce.com/)
  - Steps:
    - Download and Install the Helix Visual Client (P4V) from [here](https://www.perforce.com/downloads/helix-visual-client-p4v)
    - Steps in the Installation Wizard:
      - Keep all application selected and hit _Next_
      - For the Server please enter the private IP/DNS name of the Perforce Helix Core server we deployed earlier. You can find the private IP/DNS name in the CDK/CloudFormation Outputs or via the AWS Management Console. Example: `ip-10-0-XXX-XXX.eu-central-1.compute.internal:1666`
      - The User Name is `perforce`
      - Hit _Next_
      - Hit _Next_
      - Hit _Install_
      - Uncheck "Start P4V" and hit _Exit_
- [Unreal Engine 4](https://www.unrealengine.com/en-US/download)
  - Hints:
    - You need to Sign-Up for an EPIC account or use your existing one. Alternatively you can clone the Unreal Engine 4 source from Github if you have connected your EPIC Account with your Github account.

We have chosen Parsec in this example, but feel to install a different remote desktop protocol based on your preference. Other options would be for example [PCoIP from teradici](https://docs.teradici.com/find/product/cloud-access-software/current?subscriptionName=cloud-access) or [NICE DCV](https://download.nice-dcv.com/). We already included the necessary EC2 security group and Windows firewall exceptions for these protocols, so please feel free to use the protocol of your choice.

Once you have finished the installations, please disconnect from the RDP session and connect to the instance using Parsec (or the remote desktop protocol of your choice). Now, start the PV4 application and connect to the Peforce Helix Core server. The password of the user `perforce` can be found in the AWS Secrets Manager.

Once you are done please continue to the [next step](#deployment-of-the-unreal-engine-4-swarm-cluster)

### Deployment of the Unreal Engine 4 Swarm Cluster

#### Collecting dependencies

Each Windows instance that will act as a Swarm Coordinator or as a Swarm Agent will need a set of prerequisites installed.
We can collect these prerequisites from the Unreal Engine 4 version you installed on the Virtual Workstation with the provided `assets/unreal-engine-swarm-create-dependencies-archive.ps1` script in this repository.

- If you are no longer logged into the Virtual Workstation, please login again.
- Please download the script `unreal-engine-swarm-create-dependencies-archive.ps1` from the `assests` folder to the virtual workstation
- This PowerShell script will copy all the components that are needed to customize a fresh Window installation
- The script assumes that your Unreal Engine is installed to `C:\Program Files\Epic Games\UE_4.27` directory but you can customize the script to match your location
- Script will create a compressed archive called `ue4-swarm-archive.zip` under your `My Documents` directory
- You can find more details about these prerequisites at:
  - [Unreal Engines 4's Hardware and Software requirements](https://docs.unrealengine.com/en-US/GettingStarted/RecommendedSpecifications/index.html) -page
  - [Setting up Swarm Coordinator and Swarm Agents instructions](https://docs.unrealengine.com/en-US/Engine/Rendering/LightingAndShadows/Lightmass/UnrealSwarmOverview/index.html) -page

After you have created the `ue4-swarm-archive.zip` -archive you need to upload it into the root directory of the newly created S3 bucket. It will be downloaded from that location and used during the EC2 Image Builder process. The name of the bucket is available as an output called `BucketName` from the `gpic-pipeline-foundation` stack.

With [AWS Tools for PowerShell](https://docs.aws.amazon.com/powershell/latest/reference/index.html) you can use following command to first list buckets and fetch the name of the bucket created by the foundation stack:

```
Get-S3Bucket
```

Then write the local file to the specified bucket and key:

```
Write-S3Object -BucketName <NAME OF THE S3 BUCKET> -Key ue4-swarm-archive.zip -File ue4-swarm-archive.zip
```

#### Deployment

To deploy the Swarm Cluster you can run following command:

```
cdk deploy gpic-pipeline-swarm-cluster
```

Alternatively you can use the `cloudformation/gpic-pipeline-swarm-cluster.yaml` -template to create a CloudFormation stack called `gpic-pipeline-swarm-cluster` using the AWS Console and AWS CLI.

CLI example:

```
aws cloudformation create-stack --stack-name gpic-pipeline-swarm-cluster --capabilities CAPABILITY_NAMED_IAM --template-body file://cloudformation/gpic-pipeline-swarm-cluster.yaml --capabilities CAPABILITY_IAM
```

This step will take **30 minutes** on average as it's baking the Window AMI for Swarm. The steps to install all dependencies does take some time to complete. While the deployment is running you can read [below](#a-look-behind-the-curtains) for details on what's happening during stack creation.

Once this stack is deployed, please proceed to the [final step](#finish)

#### A look behind the curtains

##### Baking custom Windows AMI for UE4 Swarm

The `gpic-pipeline-swarm-cluster` -stack will first configure EC2 Image Builder to use latest "Microsoft Windows Server 2019 Base" image as the base image. It also creates a EC2 Image Builder component defining the build steps. These steps will download the Zip -arcive from S3, install .Net runtime, run the `UE4PrereqSetup_x64.exe` -intaller and then open Windows Firewall for the Swarm ports. You can view the `assets/component.yaml` -file for details.

Once the EC2 Image Builder completes it will create a private AMI under your account. This AMI contains all the required Unreal Engine 4 Swarm build dependencies and can be used to quickly launch the Swarm Coordinator and Swarm Agents.

##### Deploying UE4 Swarm Coordinator

The Swarm Coordinator will be launched as a single EC2 Instance. The launch will use `User Data` to configure the Windows to start `SwarmCoordinator.exe` on bootup. You can view the contents of the `User Data` in `assets/start-coordinator.ps1` - Powershell script.

##### Deploying UE4 Swarm Agent Auto Scaling Group

The Swarm Agents are going to be launched as Auto Scaling Group. Enabling us to quickly scale the number of nodes up and down. As the Swarm Agents need to be already online and registered when you submit a UE4 build, we can't use any metrics to scale the cluster on demand.
Instead you can use for example Schedule or some script to scale the cluster before submit a job. With a schedule you could for example configure the cluster to scale up to certain number of nodes in the morning and then after office hours scale the cluster back to zero.

The Swarm Agent will also use `User Data` to configure the Windows to start `SwarmAgent.exe` on bootup and injects a Swarm configuration file into the Instance. This configuration file will set number of threads to equal amount of CPU Core and also will set the Coordinator IP address. You can view the contents of the `User Data` in `assets/start-agent.ps1` - Powershell script.

# Finish

Now that the `gpic-pipeline-swarm-cluster.yaml` stack has completed deployment you should see two additional EC2 Instances running in your new VPC. Also the CDK/CloudFormation stack should have outputed the private IP address of the Unreal Engine 4 Swarm Coordinator.

On your Virtual Workstation you have to configure the local Swarm Agent. You can launch it from `C:\Program Files\Epic Games\UE_4.25\Engine\Binaries\DotNET` directory. The Swarm agent can be accessed via the Taskbar (System Tray). After this you will need to configure the following settings:

- `AgentGroupName`: `ue4-swarm-aws`
- `AllowedRemoteAgentGroup`: `ue4-swarm-aws`
- `AllowedRemoteAgentNames`: `*`
- `CoordinatorRemotingHost`: `<Add Coordinator private IP>`

Once this is done start experimenting with your environment. Here are some example tasks that you might want to test:

- Create a streaming depot
- Create a mainline stream
- Create additional Perforce user and grant him access to the newly created streaming depot
- Create a new workspace
- Create a `.p4ignore` file for your Unreal project, markt it for add and submit it to the mainline stream
- Set the correct typemap for an Unreal project
- Start Unreal Engine 4
- Create a new Unreal project
- Close Unreal Engine 4
- Move your Unreal project into your Perforce Workspace
- Mark your Unreal project folder for add and submit it to the mainline stream
- Open the Unreal project and setup Perforce integration
- Reconfigure the EC2 Autoscaling Group to use more instances
- Submit a lightning build and see your Unreal Engine 4 Swarm agents in action

If you have any questions regarding the steps outlined above feel free to reach out to us.

_Please, don't forget stop the resources if you are not working with them, otherwise you will incur unnecessary cost. You can simply stop the Virtual Workstation, the Perforce Helix Core server and the Unreal Engine 4 Swarm Coordinator if you are taking a break and restart these instances when you want to continue to work with them. The same applies to the Unreal Engine 4 Swarm agents, with the only caveat that the start and termination of these instances is managed by an EC2 Auto Scaling group. To change the amount of running EC2 instances you need to modify the EC2 Auto Scaling group, see [here](https://docs.aws.amazon.com/autoscaling/ec2/userguide/asg-capacity-limits.html)._

# Cleaning Up Resources

To clean up this example you need to delete the CloudFormation stacks. Start by deleting the `gpic-pipeline-virutal-workstation`, followed by the `gpic-pipeline-perforce-helix-core` and `gpic-pipeline-swarm-cluster` stacks. Once all of these stacks are completely removed you can delete the `gpic-pipeline-foundation` stack.

With CDK you can delete the stacks with:
Example commands:

```
 $  cdk destroy gpic-pipeline-virutal-workstation
```

After you have removed all stacks, two resources need to be deleted manually. First the S3 bucket will need to be deleted manually and second the AMI that was created in context of the Unreal Engine 4 Swarm stack needs to be deleted.

Example commands:

```
 $  aws s3 rb s3://<bucket-name> --force
 $
 $  aws ec2 deregister-image --image-id <AMI ID>
```

# Extra Tips

## How to access the EC2 instances in the private subnets

The Perforce Helix Core Server can be accessed via the AWS Systems Manager - Session Manager.

The Unreal Engine 4 Coordinator and agents can be accesed via RDP utilizing the Virtual Workstation. Alternatively you can use the AWS Systems Manager - Session Manager to open a Powershell session to these instances.

## How to acess the Unreal Engine 4 Swarm Agent logs?

The Swarm Agent writes logs to: `C:\ue4-swarm\SwarmCache\Logs`. See the section [above](#how-to-access-the-ec2-instances-in-the-private-subnets) on how to connect to these EC2 instances.

## Updating CloudFormation templates after code changes

If you do changes to the CDK code and want to generate new CloudFormation templates you will need to use following commands to keep the stack references in sync:

```
cdk synth gpic-pipeline-foundation -e > cloudformation/gpic-pipeline-foundation.yaml
cdk synth gpic-pipeline-perforce-helix-core -e > cloudformation/gpic-pipeline-perforce-helix-core.yaml
cdk synth gpic-pipeline-swarm-cluster -e > cloudformation/gpic-pipeline-swarm-cluster.yaml
cdk synth gpic-pipeline-virtual-workstation -e > cloudformation/gpic-pipeline-virtual-workstation.yaml
```

# Security

See [CONTRIBUTING](CONTRIBUTING.md) for more information.

# License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.

The AWS CloudFormation template downloads and installs Perforce Helix Core on EC2 instances during the process. Helix Core is a proprietary software and is subject to the terms and conditions of Perforce. Please refer to EULA in the following page for details. Perforce Terms of Use : https://www.perforce.com/terms-use
