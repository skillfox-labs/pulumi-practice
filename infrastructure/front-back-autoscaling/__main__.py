import pulumi

from pulumi_aws import ec2, s3

# TODO bug? See ~/z/src/github.com/tcondit/idea-foundry/bug-and-doc-fixes/01-pulumi-update-ec2-az.md
#   edit: unsupported feature on the AWS side
#   edit: maybe a Pulumi usability bug? This will cause occasional failures if not explicit

# TODO need a solution here. I'd like to randomly choose a suitable AZ.
# However, once an AZ is chosen, that choice should be stable across `pulumi
# update`s, so that we're not causing what I call "stack churn". For now I'm
# going with a static choice. The original motivation is that in `us-west-2`,
# `t2.micro` is an unsupported instance type. So about one time in four, when
# creating a new stack, Pulumi chooses an AZ and everything fails.

# TODO investigate creating modules with functions or classes, and split things
# by type (gateways, subnets, routes+route tables, etc.). Not sure it would
# work, but there's got to be a way to break this up.

# TODO find or create an AMI chooser, given a region and instance type

# TODO create a config file

_ami = 'ami-032509850cf9ee54e'
_az1 = 'us-west-2b'
_az2 = 'us-west-2c'
_instance_type = 't2.micro'
_key_name = 'sl-us-west-2'

vpc = ec2.Vpc(resource_name = 'new-vpc',
        cidr_block = '10.0.0.0/16',
        tags = {'Name': 'infra vpc (front-back-multi-az)', 'Creator': 'timc'})

igw = ec2.InternetGateway(resource_name = 'new-igw',
        vpc_id = vpc.id,
        tags = {'Name': 'infra internet gateway (front-back-multi-az)', 'Creator': 'timc'})

public_subnet_1 = ec2.Subnet(resource_name = 'new-public-subnet-1',
        vpc_id = vpc.id,
        cidr_block = '10.0.0.0/24',
        availability_zone = _az1,
        tags = {'Name': 'infra public subnet (front-back-multi-az)', 'Creator': 'timc'})

public_subnet_2 = ec2.Subnet(resource_name = 'new-public-subnet-2',
        vpc_id = vpc.id,
        cidr_block = '10.0.1.0/24',
        availability_zone = _az2,
        tags = {'Name': 'infra public subnet (front-back-multi-az)', 'Creator': 'timc'})

# https://pulumi.io/reference/pkg/nodejs/@pulumi/aws/ec2/#RouteTableArgs-routes
# FIXED! s/destination_cidr_block/cidr_block/g

# the routeID has got the routeTableID embedded in it somehow
#   routeID            r-rtb-0bc47b98495839d0d1080289494
#   routeTableID         rtb-0bc47b98495839d0d

# TODO does it make sense to have `public_subnet_` in the name of a route
# table? _Maybe_ just `public_rt` but even that seems a bit overspecified.

public_subnet_rt = ec2.RouteTable(resource_name = 'new-public-subnet-rt',
        vpc_id = vpc.id,
        tags = {'Name': 'infra public route table (front-back-multi-az)', 'Creator': 'timc'})

# AWS: source-based routing. To get closer to a specific destination CIDR,
# forward traffic to corresponding target, e.g.,
#
# Destination   Target
# 10.0.0.0/16   Local
# 172.31.0.0/16 pcx-1a2b3c4d
# 0.0.0.0/0     igw-11aa22bb

# AKA 'new-igw-route'
public_route = ec2.Route(resource_name = 'new-public-route',
        destination_cidr_block = '0.0.0.0/0',
        gateway_id = igw.id,
        route_table_id = public_subnet_rt.id)

public_subnet_rta = ec2.RouteTableAssociation(resource_name = 'new-public-subnet-rta',
        route_table_id = public_subnet_rt.id,
        subnet_id = public_subnet_1.id)

private_subnet_1 = ec2.Subnet(resource_name = 'new-private-subnet-1',
        vpc_id = vpc.id,
        cidr_block = '10.0.2.0/24',
        availability_zone = _az1,
        tags = {'Name': 'infra private subnet (front-back-multi-az)', 'Creator': 'timc'})

private_subnet_2 = ec2.Subnet(resource_name = 'new-private-subnet-2',
        vpc_id = vpc.id,
        cidr_block = '10.0.3.0/24',
        availability_zone = _az2,
        tags = {'Name': 'infra private subnet (front-back-multi-az)', 'Creator': 'timc'})

# s/public_sg/bastion_sg/g ? s/public_sg/dmz_sg/g ?

# TODO think about a different network layout: `dmz` (public), `app` (private),
# `db` (even more private) ; a simple public-private partitioning works for
# now, but the bastion host instance should serve in that capacity only.

# TODO add a bastion host in each `AZ`

# NOTE Pulumi-generated security groups have no outbound rules, a departure from usual where it's completely open.
public_sg = ec2.SecurityGroup(resource_name = 'new-public-sg',
        description = 'HTTP and SSH ingress',
        vpc_id = vpc.id,
        ingress = [
            {'protocol': 'tcp', 'fromPort': 22, 'toPort': 22, 'cidrBlocks': ['0.0.0.0/0']},
            {'protocol': 'tcp', 'fromPort': 80, 'toPort': 80, 'cidrBlocks': ['0.0.0.0/0']},
            ],
        egress = [
            {'protocol': '-1', 'fromPort': 0, 'toPort': 0, 'cidrBlocks': ['0.0.0.0/0']}
            ],
        tags = {'Name': 'infra public security group (front-back-multi-az)', 'Creator': 'timc'})

# TODO add ebs_block_devices
# TODO add volume_tags
# TODO add iam_instance_profile
# TODO add user_data

# TODO how to allow access to private instance without copying SSH key to this
# machine? Looks like I need `SSH agent forwarding`.

public_server_1 = ec2.Instance(resource_name = 'new-public-ec2-1',
        ami = _ami,                     # TypeError if not present
        instance_type = _instance_type, # TypeError if not present
        security_groups = [public_sg.id],
        availability_zone = _az1,
        subnet_id = public_subnet_1.id,
        associate_public_ip_address = False,
        key_name = _key_name,

        # TODO `Quiver`: `Pulumi > Questions > Adding tags forces EC2 replacement?`
        #   edit: I also changed the instance's `resource_name`
        tags = {'Name': 'infra public ec2 1 (front-back-multi-az)', 'Creator': 'timc'}
        )

public_server_2 = ec2.Instance(resource_name = 'new-public-ec2-2',
        ami = _ami,                     # TypeError if not present
        instance_type = _instance_type, # TypeError if not present
        security_groups = [public_sg.id],
        availability_zone = _az2,
        subnet_id = public_subnet_2.id,
        associate_public_ip_address = False,
        key_name = _key_name,

        # TODO `Quiver`: `Pulumi > Questions > Adding tags forces EC2 replacement?`
        #   edit: I also changed the instance's `resource_name`
        tags = {'Name': 'infra public ec2 2 (front-back-multi-az)', 'Creator': 'timc'}
        )

# TODO bug? If you include `associate_with_private_ip = server.private_ip` but
# leave off `instance = server.id`, the association is not created

# TODO move this to ALB when the time comes
eip_1 = ec2.Eip(resource_name = 'new-eip-1',
        instance = public_server_1.id,
        associate_with_private_ip = public_server_1.private_ip,
        vpc = True,
        tags = {'Name': 'infra eip 1 (front-back-multi-az)', 'Creator': 'timc'}
        )

# TODO move this to ALB when the time comes
eip_2 = ec2.Eip(resource_name = 'new-eip-2',
        instance = public_server_2.id,
        associate_with_private_ip = public_server_2.private_ip,
        vpc = True,
        tags = {'Name': 'infra eip 2 (front-back-multi-az)', 'Creator': 'timc'}
        )

# AWS: Maybe I should drop the route definition above, and use a
# MainRouteTableAssociation here. The main route table is sitting idle.

# TODO this needs to go out via NAT gateway
private_subnet_rt = ec2.RouteTable(resource_name = 'new-private-subnet-rt',
        vpc_id = vpc.id,
        tags = {'Name': 'infra private route table (front-back-multi-az)', 'Creator': 'timc'})

nat_eip = ec2.Eip(resource_name = 'new-nat-eip',
        # not using `associate_with_private_ip` because I don't have access to the private IP
        vpc = True,
        tags = {'Name': 'infra nat eip (front-back-multi-az)', 'Creator': 'timc'}
        )

nat_gw = ec2.NatGateway(resource_name = 'new-nat-gw',
        allocation_id = nat_eip.id,
        subnet_id = public_subnet_1.id,
        tags = {'Name': 'infra nat gw (front-back-multi-az)', 'Creator': 'timc'}
        )

private_subnet_rta_1 = ec2.RouteTableAssociation(resource_name = 'new-private-subnet-rta-1',
        route_table_id = private_subnet_rt.id,
        subnet_id = private_subnet_1.id)

private_subnet_rta_2 = ec2.RouteTableAssociation(resource_name = 'new-private-subnet-rta-2',
        route_table_id = private_subnet_rt.id,
        subnet_id = private_subnet_2.id)

# TODO remove reference to internet gateway ; can't have two default routes anyway
private_route = ec2.Route(resource_name = 'new-natgw-route',
        destination_cidr_block = '0.0.0.0/0',
        gateway_id = nat_gw.id,
        route_table_id = private_subnet_rt.id)

# TODO I don't see this tag
# TODO add VPC endpoint
bucket = s3.Bucket(resource_name = 'new-bucket',
        tags = {'Name': 'infra bucket front-back-multi-az', 'Creator': 'timc'})

# s/public_sg/bastion_sg/g ?
private_sg = ec2.SecurityGroup(resource_name = 'new-private-sg',
        description = 'bastion host ingress',
        vpc_id = vpc.id,
        egress = [
            {'protocol': '-1', 'fromPort': 0, 'toPort': 0, 'cidrBlocks': ['0.0.0.0/0']}
            ],
        tags = {'Name': 'infra private security group (front-back-multi-az)', 'Creator': 'timc'})

# use an ec2.SecurityGroupRule instead of subnet
private_sg_in_rule_1 = ec2.SecurityGroupRule(resource_name = 'new-private-sg-in-rule-1',
        description = 'accept traffic from bastion host',
        security_group_id = private_sg, # TypeError if not present
        source_security_group_id = public_sg.id,
        type = 'ingress',
        protocol = 'tcp',               # TypeError if not present
        from_port = '22',               # TypeError if not present
        to_port = '22',                 # TypeError if not present
        )

# TODO add ebs_block_devices
# TODO add volume_tags
# TODO add iam_instance_profile
# TODO add user_data

private_server_1 = ec2.Instance(resource_name = 'new-private-ec2-1',
        ami = _ami,                     # TypeError if not present
        instance_type = _instance_type, # TypeError if not present
        security_groups = [private_sg.id],
        availability_zone = _az1,
        subnet_id = private_subnet_1.id,
        associate_public_ip_address = False,
        key_name = _key_name,

        # TODO `Quiver`: `Pulumi > Questions > Adding tags forces EC2 replacement?`
        #   edit: I also changed the instance's `resource_name`
        tags = {'Name': 'infra private ec2 1 (front-back-multi-az)', 'Creator': 'timc'}
        )

private_server_2 = ec2.Instance(resource_name = 'new-private-ec2-2',
        ami = _ami,                     # TypeError if not present
        instance_type = _instance_type, # TypeError if not present
        security_groups = [private_sg.id],
        availability_zone = _az2,
        subnet_id = private_subnet_2.id,
        associate_public_ip_address = False,
        key_name = _key_name,

        # TODO `Quiver`: `Pulumi > Questions > Adding tags forces EC2 replacement?`
        #   edit: I also changed the instance's `resource_name`
        tags = {'Name': 'infra private ec2 2 (front-back-multi-az)', 'Creator': 'timc'}
        )

launch_config = ec2.LaunchConfiguration(resource_name = 'new-launch-configuration',
        image_id = _ami,                # TypeError if not present
        instance_type = _instance_type, # TypeError if not present
        associate_public_ip_address = True, # temporary
        key_name = _key_name,
        security_groups = [public_sg.id],
        tags = {'Name': 'infra launch config (front-back-multi-az)', 'Creator': 'timc'}

        #   enable_monitoring=None,
        #   iam_instance_profile=None,
        #   name=None,
        #   user_data=None,
        )

autoscaling_group_1 = autoscaling.Group(resource_name = 'new-autoscaling-group',
        availability_zones = [_az1, _az2],
        launch_configuration = launch_config,
        max_size = 4,
        tags = {'Name': 'infra autoscaling group 1 (front-back-multi-az)', 'Creator': 'timc'}
        )

launch_template = ec2.LaunchTemplate(resource_name = 'new-launch-template',
        image_id = _ami,                # TypeError if not present
        instance_type = _instance_type, # TypeError if not present
        key_name = _key_name,
        vpc_security_group_ids = [public_sg.id],
        tags = {'Name': 'infra launch template (front-back-multi-az)', 'Creator': 'timc'}

        #   security_group_names=None,
        #   iam_instance_profile=None,
        #   monitoring=None,
        #   tag_specifications=None,
        #   tags=None,
        #   user_data=None,
        #   vpc_security_group_ids=None,
        )

autoscaling_group_2 = autoscaling.Group(resource_name = 'new-autoscaling-group',
        availability_zones = [_az1, _az2],
        launch_template = launch_template,
        max_size = 4,
        tags = {'Name': 'infra autoscaling group 2 (front-back-multi-az)', 'Creator': 'timc'}
        )

# stack exports: shared
pulumi.export('vpcID', vpc.id)
pulumi.export('internetGatewayID', igw.id)
pulumi.export('bucket_name',  bucket.bucket_domain_name)
pulumi.export('elasticIP 1', eip_1.public_ip)
pulumi.export('elasticIP 2', eip_2.public_ip)
pulumi.export('[public] AMI', _ami)
pulumi.export('[public ] nat gw ID', nat_gw.id)
pulumi.export('[public] nat eip public IP', nat_eip.public_ip)
pulumi.export('launch config', launch_config),
pulumi.export('launch template', launch_template),

# stack exports: public
pulumi.export('[public] securityGroupID', public_sg.id)
pulumi.export('[public] subnetID 1', public_subnet_1.id)
pulumi.export('[public] subnetID 2', public_subnet_2.id)
pulumi.export('[public] subnet CIDR block', public_subnet_1.cidr_block)
pulumi.export('[public] routeTableID', public_subnet_rt.id)
pulumi.export('[public] routeID', public_route.id)
pulumi.export('[public] AMI', _ami)
pulumi.export('[public] instanceID', public_server_1.id)
pulumi.export('[public] instanceID', public_server_2.id)
pulumi.export('[public] ec2 privateIP 2', public_server_2.private_ip)
pulumi.export('[public] ec2 publicIP 1', public_server_1.public_ip)
pulumi.export('[public] ec2 privateIP 2', public_server_2.private_ip)

# stack exports: private
pulumi.export('[private] securityGroupID', private_sg.id)
pulumi.export('[private] subnetID 1', private_subnet_1.id)
pulumi.export('[private] subnetID 2', private_subnet_2.id)
pulumi.export('[private] subnet CIDR block', private_subnet_1.cidr_block)
pulumi.export('[private] routeTableID', private_subnet_rt.id)
pulumi.export('[private] routeID', private_route.id)
pulumi.export('[private] instanceID', private_server_1.id)
pulumi.export('[private] instanceID', private_server_2.id)
pulumi.export('[private] ec2 publicIP 1', private_server_1.public_ip)
pulumi.export('[private] ec2 privateIP 2', private_server_2.private_ip)
pulumi.export('[private] ec2 privateIP 2', private_server_2.private_ip)

