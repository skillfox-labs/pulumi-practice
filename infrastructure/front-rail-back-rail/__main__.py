import pulumi

from pulumi_aws import ec2, s3

# TODO
# next indicated actions:
# * `NAT gateway` to allow the private `EC2` instances to reach outside the VPC

# TODO bug? See ~/z/src/github.com/tcondit/idea-foundry/bug-and-doc-fixes/01-pulumi-update-ec2-az.md
#   edit: unsupported feature on the AWS side
#   edit: maybe a Pulumi usability bug? This will cause occasional failures if not explicit

# TODO need a solution here. I'd like to randomly choose a suitable AZ.
# However, once an AZ is chosen, that choice should be stable across `pulumi
# update`s, so that we're not causing what I call "stack churn". For now I'm
# going with a static choice. The original motivation is that in `us-west-2`,
# `t2.micro` is an unsupported instance type. So about one time in four, when
# creating a new stack, Pulumi chooses an AZ and everything fails.

_availability_zone_1 = 'us-west-2b'
#_availability_zone_2 = 'us-west-2c'
_instance_type = 't2.micro'

vpc = ec2.Vpc(resource_name = 'new-vpc',
        cidr_block = '10.0.0.0/16',
        tags = {'Name': 'infra vpc (front-rail-back-rail)', 'Creator': 'timc'})

igw = ec2.InternetGateway(resource_name = 'new-igw',
        vpc_id = vpc.id,
        tags = {'Name': 'infra internet gateway (front-rail-back-rail)', 'Creator': 'timc'})

public_subnet_1 = ec2.Subnet(resource_name = 'new-public-subnet-1',
        vpc_id = vpc.id,
        cidr_block = '10.0.0.0/24',
        availability_zone = _availability_zone_1,
        tags = {'Name': 'infra public subnet (front-rail-back-rail)', 'Creator': 'timc'})

# public_subnet_2 = ec2.Subnet(resource_name = 'new-public-subnet-2',
# [...]

# https://pulumi.io/reference/pkg/nodejs/@pulumi/aws/ec2/#RouteTableArgs-routes
# FIXED! s/destination_cidr_block/cidr_block/g

# the routeID has got the routeTableID embedded in it somehow
#   routeID            r-rtb-0bc47b98495839d0d1080289494
#   routeTableID         rtb-0bc47b98495839d0d

# TODO does it make sense to have `public_subnet_` in the name of a route
# table? _Maybe_ just `public_rt` but even that seems a bit overspecified.
public_subnet_rt = ec2.RouteTable('new-public-subnet-rt',
        vpc_id = vpc.id,
        routes = [{'gateway_id': igw.id, 'cidr_block': '0.0.0.0/0'}],
        tags = {'Name': 'infra route table (front-rail-back-rail)', 'Creator': 'timc'})

# AWS: source-based routing. To get closer to a specific destination CIDR,
# forward traffic to corresponding target, e.g.,
#
# Destination   Target
# 10.0.0.0/16   Local
# 172.31.0.0/16 pcx-1a2b3c4d
# 0.0.0.0/0     igw-11aa22bb

# AKA 'new-igw-route'
public_route = ec2.Route('new-public-route',
        destination_cidr_block = '0.0.0.0/0',
        gateway_id = igw.id,
        route_table_id = public_subnet_rt.id)

public_subnet_rta = ec2.RouteTableAssociation('new-public-subnet-rta',
        route_table_id = public_subnet_rt.id,
        subnet_id = public_subnet_1.id)

private_subnet_1 = ec2.Subnet(resource_name = 'new-private-subnet',
        vpc_id = vpc.id,
        cidr_block = '10.0.1.0/24',
        availability_zone = _availability_zone_1,
        tags = {'Name': 'infra private subnet (front-rail-back-rail)', 'Creator': 'timc'})

# TODO think about this ; come back to it later ; should I split the SGs into
# public and private too? Why not?
#
# Late note: can't ping private IP behind a NAT gateway ; probably need at a
# minimum to add both instances to a default security group ; may also need to
# update one or both route tables

# s/public_sg/bastion_sg/g ? s/public_sg/dmz_sg/g ?

# TODO think about a different network layout: `dmz` (public), `app` (private),
# `db` (even more private) ; a simple public-private partitioning works for
# now, but the bastion host instance should serve in that capacity only.

# TODO add a bastion host in each `AZ`

public_sg = ec2.SecurityGroup(resource_name = 'new-public-sg',
        description = 'HTTP and SSH ingress',
        vpc_id = vpc.id,
        ingress = [
            {'protocol': 'tcp', 'fromPort': 22, 'toPort': 22, 'cidrBlocks': ['0.0.0.0/0']},
            {'protocol': 'tcp', 'fromPort': 80, 'toPort': 80, 'cidrBlocks': ['0.0.0.0/0']},
            ],
        egress = [
            {'protocol': 'tcp', 'fromPort': 22, 'toPort': 22, 'cidrBlocks': [private_subnet_1.cidr_block]},
            ],
        tags = {'Name': 'infra public security group (front-rail-back-rail)', 'Creator': 'timc'})

# TODO add ebs_block_devices
# TODO add volume_tags
# TODO add iam_instance_profile
# TODO add user_data

# TODO how to allow access to private instance without copying SSH key to this
# machine? Looks like I need `SSH agent forwarding`.
public_server = ec2.Instance(
        resource_name = 'new-public-ec2',
        ami = 'ami-032509850cf9ee54e',  # TypeError if not present
        instance_type = _instance_type, # TypeError if not present
        security_groups = [public_sg.id],
        availability_zone = _availability_zone_1,
        subnet_id = public_subnet_1.id,
        associate_public_ip_address = False,
        key_name = 'sl-us-west-2',

        # TODO `Quiver`: `Pulumi > Questions > Adding tags forces EC2 replacement?`
        #   edit: I also changed the instance's `resource_name`
        tags = {'Name': 'infra public ec2 (front-rail-back-rail)', 'Creator': 'timc'}
        )

# TODO bug? If you include `associate_with_private_ip = server.private_ip` but
# leave off `instance = server.id`, the association is not created
eip = ec2.Eip(resource_name = 'new-eip',
        instance = public_server.id,
        associate_with_private_ip = public_server.private_ip,
        tags = {'Name': 'infra eip (front-rail-back-rail)', 'Creator': 'timc'}
        )

# AWS: Maybe I should drop the route definition above, and use a
# MainRouteTableAssociation here. The main route table is sitting idle.

# TODO this needs to go out via NAT gateway
private_subnet_rt = ec2.RouteTable('new-private-subnet-rt',
        vpc_id = vpc.id,
        routes = [{'gateway_id': igw.id, 'cidr_block': '0.0.0.0/0'}],
        tags = {'Name': 'infra route table (front-rail-back-rail)', 'Creator': 'timc'})

private_subnet_rta = ec2.RouteTableAssociation('new-private-subnet-rta',
        route_table_id = private_subnet_rt.id,
        subnet_id = private_subnet_1.id)

private_route = ec2.Route('new-natgw-route',
        destination_cidr_block = '0.0.0.0/0',
        gateway_id = igw.id,
        route_table_id = private_subnet_rt.id)

# TODO I don't see this tag
# TODO add VPC endpoint
bucket = s3.Bucket(resource_name = 'new-bucket',
        tags = {'Name': 'infra bucket (front-rail-back-rail)', 'Creator': 'timc'})

# s/public_sg/bastion_sg/g ?
private_sg = ec2.SecurityGroup(resource_name = 'new-private-sg',
        description = 'bastion host ingress',
        vpc_id = vpc.id,
        ingress = [
            # TODO how to get CIDR block from bastion subnet?
            {'protocol': 'tcp', 'fromPort': 22, 'toPort': 22, 'cidrBlocks': [public_subnet_1.cidr_block]},
            ],
        tags = {'Name': 'infra private security group (front-rail-back-rail)', 'Creator': 'timc'})

# TODO add ebs_block_devices
# TODO add volume_tags
# TODO add iam_instance_profile
# TODO add user_data

private_server = ec2.Instance(
        resource_name = 'new-private-ec2',
        ami = 'ami-032509850cf9ee54e',  # TypeError if not present
        instance_type = _instance_type, # TypeError if not present
        security_groups = [private_sg.id],
        availability_zone = _availability_zone_1,
        subnet_id = private_subnet_1.id,
        associate_public_ip_address = False,
        key_name = 'sl-us-west-2',

        # TODO `Quiver`: `Pulumi > Questions > Adding tags forces EC2 replacement?`
        #   edit: I also changed the instance's `resource_name`
        tags = {'Name': 'infra private ec2 (front-rail-back-rail)', 'Creator': 'timc'}
        )

# stack exports: shared
pulumi.export('vpcID', vpc.id)
pulumi.export('internetGatewayID', igw.id)
pulumi.export('bucket_name',  bucket.bucket_domain_name)
pulumi.export('elasticIP', eip.public_ip)

# stack exports: public
pulumi.export('[public] securityGroupID', public_sg.id)
pulumi.export('[public] subnetID', public_subnet_1.id)
pulumi.export('[public] subnet CIDR block', public_subnet_1.cidr_block)
pulumi.export('[public] routeTableID', public_subnet_rt.id)
pulumi.export('[public] routeID', public_route.id)
pulumi.export('[public] AMI', public_server.ami)
pulumi.export('[public] instanceID', public_server.id)
pulumi.export('[public] publicIP', public_server.public_ip)
pulumi.export('[public] privateIP', public_server.private_ip)

# stack exports: private
pulumi.export('[private] securityGroupID', private_sg.id)
pulumi.export('[private] subnetID', private_subnet_1.id)
pulumi.export('[private] subnet CIDR block', private_subnet_1.cidr_block)
pulumi.export('[private] routeTableID', private_subnet_rt.id)
pulumi.export('[private] routeID', private_route.id)
pulumi.export('[private] AMI', private_server.ami)
pulumi.export('[private] instanceID', private_server.id)
pulumi.export('[private] publicIP', private_server.public_ip)
pulumi.export('[private] privateIP', private_server.private_ip)

