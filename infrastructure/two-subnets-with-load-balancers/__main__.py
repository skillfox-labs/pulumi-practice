import configparser
import pulumi

from pulumi_aws import autoscaling, ec2, elasticloadbalancingv2, s3

# TODO figure out how to use the 'get_*' Pulumi methods, e.g.,
#   pulumi_aws.elasticloadbalancingv2.get_load_balancer()
# Could this help with the launch_template issue below?

# TODO investigate and probably use `black`

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
#
# import infra_network
# >> infra_network.py
#
#from pulumi_aws import ec2
#
#def vpc():
#    return ec2.Vpc(resource_name = 'new-vpc',
#        cidr_block = '10.0.0.0/16',
#        tags = {'Name': 'infra vpc (two-subnets-with-load-balancers)', 'Creator': 'timc'})

# TODO find or create an AMI chooser, given a region and instance type

config = configparser.ConfigParser()
config.read('config.ini')
#print(f"from config: {config['default']['instance_type']}")

_ami = config['default']['ami']
_az1 = config['default']['az1']
_az2 = config['default']['az2']
_instance_type = config['default']['instance_type']
_key_name = config['default']['key_name']

#vpc = infra_network.vpc()

vpc = ec2.Vpc(resource_name = 'new-vpc',
        cidr_block = '10.0.0.0/16',
        tags = {'Name': 'infra vpc (two-subnets-with-load-balancers)', 'Creator': 'timc'})

igw = ec2.InternetGateway(resource_name = 'new-igw',
        vpc_id = vpc.id,
        tags = {'Name': 'infra internet gateway (two-subnets-with-load-balancers)', 'Creator': 'timc'})

public_subnet_1 = ec2.Subnet(resource_name = 'new-public-subnet-1',
        vpc_id = vpc.id,
        cidr_block = '10.0.0.0/24',
        availability_zone = _az1,
        tags = {'Name': 'infra public subnet (two-subnets-with-load-balancers)', 'Creator': 'timc'})

public_subnet_2 = ec2.Subnet(resource_name = 'new-public-subnet-2',
        vpc_id = vpc.id,
        cidr_block = '10.0.1.0/24',
        availability_zone = _az2,
        tags = {'Name': 'infra public subnet (two-subnets-with-load-balancers)', 'Creator': 'timc'})

# https://pulumi.io/reference/pkg/nodejs/@pulumi/aws/ec2/#RouteTableArgs-routes
# FIXED! s/destination_cidr_block/cidr_block/g

# the routeID has got the routeTableID embedded in it somehow
#   routeID            r-rtb-0bc47b98495839d0d1080289494
#   routeTableID         rtb-0bc47b98495839d0d

# TODO does it make sense to have `public_subnet_` in the name of a route
# table? _Maybe_ just `public_rt` but even that seems a bit overspecified.

public_subnet_rt = ec2.RouteTable(resource_name = 'new-public-subnet-rt',
        vpc_id = vpc.id,
        tags = {'Name': 'infra public route table (two-subnets-with-load-balancers)', 'Creator': 'timc'})

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
        tags = {'Name': 'infra private subnet (two-subnets-with-load-balancers)', 'Creator': 'timc'})

#private_subnet_2 = infra_network.private_subnet_2()

private_subnet_2 = ec2.Subnet(resource_name = 'new-private-subnet-2',
        vpc_id = vpc.id,
        cidr_block = '10.0.3.0/24',
        availability_zone = _az2,
        tags = {'Name': 'infra private subnet (two-subnets-with-load-balancers)', 'Creator': 'timc'})

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
        tags = {'Name': 'infra public security group (two-subnets-with-load-balancers)', 'Creator': 'timc'})

# TODO add ebs_block_devices
# TODO add volume_tags
# TODO add iam_instance_profile
# TODO add user_data

# TODO how to allow access to private instance without copying SSH key to this
# machine? Looks like I need `SSH agent forwarding`.

public_alb = elasticloadbalancingv2.LoadBalancer(resource_name = 'new-alb',
        internal = False,
        load_balancer_type = 'application',
        subnets = [public_subnet_1, public_subnet_2],
        )

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
        tags = {'Name': 'infra public ec2 1 (two-subnets-with-load-balancers)', 'Creator': 'timc'}
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
        tags = {'Name': 'infra public ec2 2 (two-subnets-with-load-balancers)', 'Creator': 'timc'}
        )

# TODO bug? If you include `associate_with_private_ip = server.private_ip` but
# leave off `instance = server.id`, the association is not created

# TODO move this to ALB when the time comes
eip_1 = ec2.Eip(resource_name = 'new-eip-1',
        instance = public_server_1.id,
        associate_with_private_ip = public_server_1.private_ip,
        vpc = True,
        tags = {'Name': 'infra eip 1 (two-subnets-with-load-balancers)', 'Creator': 'timc'}
        )

# TODO move this to ALB when the time comes
eip_2 = ec2.Eip(resource_name = 'new-eip-2',
        instance = public_server_2.id,
        associate_with_private_ip = public_server_2.private_ip,
        vpc = True,
        tags = {'Name': 'infra eip 2 (two-subnets-with-load-balancers)', 'Creator': 'timc'}
        )

# AWS: Maybe I should drop the route definition above, and use a
# MainRouteTableAssociation here. The main route table is sitting idle.

# TODO this needs to go out via NAT gateway
private_subnet_rt = ec2.RouteTable(resource_name = 'new-private-subnet-rt',
        vpc_id = vpc.id,
        tags = {'Name': 'infra private route table (two-subnets-with-load-balancers)', 'Creator': 'timc'})

nat_eip = ec2.Eip(resource_name = 'new-nat-eip',
        # not using `associate_with_private_ip` because I don't have access to the private IP
        vpc = True,
        tags = {'Name': 'infra nat eip (two-subnets-with-load-balancers)', 'Creator': 'timc'}
        )

nat_gw = ec2.NatGateway(resource_name = 'new-nat-gw',
        allocation_id = nat_eip.id,
        subnet_id = public_subnet_1.id,
        tags = {'Name': 'infra nat gw (two-subnets-with-load-balancers)', 'Creator': 'timc'}
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
        tags = {'Name': 'infra bucket two-subnets-with-load-balancers', 'Creator': 'timc'})

# s/public_sg/bastion_sg/g ?
private_sg = ec2.SecurityGroup(resource_name = 'new-private-sg',
        description = 'bastion host ingress',
        vpc_id = vpc.id,
        egress = [
            {'protocol': '-1', 'fromPort': 0, 'toPort': 0, 'cidrBlocks': ['0.0.0.0/0']}
            ],
        tags = {'Name': 'infra private security group (two-subnets-with-load-balancers)', 'Creator': 'timc'})

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
        tags = {'Name': 'infra private ec2 1 (two-subnets-with-load-balancers)', 'Creator': 'timc'}
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
        tags = {'Name': 'infra private ec2 2 (two-subnets-with-load-balancers)', 'Creator': 'timc'}
        )

launch_config = ec2.LaunchConfiguration(resource_name = 'new-launch-configuration',
        image_id = _ami,                # TypeError if not present
        instance_type = _instance_type, # TypeError if not present
        associate_public_ip_address = True, # temporary
        key_name = _key_name,
        security_groups = [public_sg.id],

        #   enable_monitoring=None,
        #   iam_instance_profile=None,
        #   name=None,
        #   user_data=None,
        )

autoscaling_group_1 = autoscaling.Group(resource_name = 'new-autoscaling-group-1',
        availability_zones = [_az1, _az2],
        launch_configuration = launch_config,
        min_size = 1,
        max_size = 4,
        desired_capacity = 1,
        vpc_zone_identifiers = [public_subnet_1, public_subnet_2],
        tags = [{
            'key': 'Name',
            'value': 'infra autoscaling group 1 (two-subnets-with-load-balancers)',
            'propagate_at_launch': True,
            }],
        )

# https://github.com/pulumi/terraform-provider-aws/blob/d832bde0f617e0666cf932807a29cb5111baee78/website/docs/r/autoscaling_group.html.markdown#launch_template

launch_template = ec2.LaunchTemplate('new-launch-template',
        image_id = _ami,                # TypeError if not present
        instance_type = _instance_type, # TypeError if not present
        key_name = _key_name,
        vpc_security_group_ids = [public_sg.id],
        tags = [{
            'Name': 'infra launch template (two-subnets-with-load-balancers)',
            'Creator': 'timc',
            }],
        )

#autoscaling_group_2 = autoscaling.Group('new-autoscaling-group-2',
#        launch_template = {'name': launch_template},
#        #launch_template = lt.id,
#        availability_zones = [_az1, _az2],
#        min_size = 1,
#        max_size = 4,
#        desired_capacity = 1,
#        vpc_zone_identifiers = [public_subnet_1, public_subnet_2],
#        tags = [{
#            'key': 'Name',
#            'value': 'infra autoscaling group 2 (two-subnets-with-load-balancers)',
#            'propagate_at_launch': True,
#            }]
#        )

# stack exports: shared
pulumi.export('vpc-id', vpc.id)
pulumi.export('internet-gateway-id', igw.id)
pulumi.export('bucket-name', bucket.bucket_domain_name)
pulumi.export('elastic-ip-1', eip_1.public_ip)
pulumi.export('elastic-ip-2', eip_2.public_ip)
pulumi.export('ami-id', _ami)
pulumi.export('nat-gw-id', nat_gw.id)
pulumi.export('nat-eip-public-ip', nat_eip.public_ip)
pulumi.export('launch-config', launch_config),
pulumi.export('launch-template', launch_template.id),
#pulumi.export('autoscaling-group-2', autoscaling_group_2.id),

# stack exports: public
pulumi.export('public-security-group-id', public_sg.id)
pulumi.export('public-subnet-1-id', public_subnet_1.id)
pulumi.export('public-subnet-2-id', public_subnet_2.id)
pulumi.export('public-subnet-1-cidr-block', public_subnet_1.cidr_block)
pulumi.export('public-route-table-id', public_subnet_rt.id)
pulumi.export('public-route-id', public_route.id)
pulumi.export('public-ec2-1-instance-id', public_server_1.id)
pulumi.export('public-ec2-1-public-ip', public_server_1.public_ip)
pulumi.export('public-ec2-2-instance-id', public_server_2.id)
pulumi.export('public-ec2-2-private-ip', public_server_2.private_ip)
pulumi.export('public-alb', public_alb.id)

# stack exports: private
pulumi.export('private-security-group-id', private_sg.id)
pulumi.export('private-subnet-1-id', private_subnet_1.id)
pulumi.export('private-subnet-2-id', private_subnet_2.id)
pulumi.export('private-subnet-1-cidr-block', private_subnet_1.cidr_block)
pulumi.export('private-route-table-id', private_subnet_rt.id)
pulumi.export('private-route-id', private_route.id)
pulumi.export('private-ec2-1-instance-id', private_server_1.id)
pulumi.export('private-ec2-1-public-ip', private_server_1.public_ip)
pulumi.export('private-ec2-2-instance-id', private_server_2.id)
pulumi.export('private-ec2-2-private-ip', private_server_2.private_ip)

