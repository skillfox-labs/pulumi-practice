import pulumi

from pulumi_aws import ec2, s3

# TODO functions and classes (encapsulation, ffs)

# TODO bug? See ~/z/src/github.com/tcondit/idea-foundry/bug-and-doc-fixes/01-pulumi-update-ec2-az.md
#   edit: unsupported feature on the AWS side
#   edit: maybe a Pulumi usability bug? This will cause occasional failures if not explicit

# TODO need a solution here. I'd like to randomly choose a suitable AZ.
# However, once an AZ is chosen, that choice should be stable across `pulumi
# update`s, so that we're not causing what I call "stack churn". For now I'm
# going with a static choice. The original motivation is that in `us-west-2`,
# `t2.micro` is an unsupported instance type. So about one time in four, when
# creating a new stack, Pulumi chooses an AZ and everything fails.

_availability_zone = 'us-west-2b'
_instance_type = 't2.micro'

vpc = ec2.Vpc(resource_name = 'new-vpc',
        cidr_block = '10.0.0.0/16',
        tags = {'Name': 'infra vpc (front-rail-back-rail)', 'Creator': 'timc'})

igw = ec2.InternetGateway(resource_name = 'new-igw',
        vpc_id = vpc.id,
        tags = {'Name': 'infra internet gateway (front-rail-back-rail)', 'Creator': 'timc'})

subnet = ec2.Subnet(resource_name = 'new-subnet',
        vpc_id = vpc.id,
        cidr_block = '10.0.0.0/20',
        availability_zone = _availability_zone,
        tags = {'Name': 'infra subnet (front-rail-back-rail)', 'Creator': 'timc'})

# https://pulumi.io/reference/pkg/nodejs/@pulumi/aws/ec2/#RouteTableArgs-routes
# FIXED! s/destination_cidr_block/cidr_block/g

# the routeID has got the routeTableID embedded in it somehow
#   routeID            r-rtb-0bc47b98495839d0d1080289494
#   routeTableID         rtb-0bc47b98495839d0d

rt = ec2.RouteTable('new-rt',
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

route = ec2.Route('default-route',
        destination_cidr_block = '0.0.0.0/0',
        gateway_id = igw.id,
        route_table_id = rt.id)

# AWS: Maybe I should drop the route definition above, and use a
# MainRouteTableAssociation here. The main route table is sitting idle.

rta = ec2.RouteTableAssociation('new-rta',
        route_table_id = rt.id,
        subnet_id = subnet.id)

sg = ec2.SecurityGroup(resource_name = 'new-sg',
        description = 'HTTP and SSH ingress',
        vpc_id = vpc.id,
        ingress = [
            {'protocol': 'tcp', 'fromPort': 22, 'toPort': 22, 'cidrBlocks': ['0.0.0.0/0']},
            {'protocol': 'tcp', 'fromPort': 80, 'toPort': 80, 'cidrBlocks': ['0.0.0.0/0']},
            ],
        tags = {'Name': 'infra security group (front-rail-back-rail)', 'Creator': 'timc'})

bucket = s3.Bucket(resource_name = 'new-bucket',
        tags = {'Name': 'infra bucket (front-rail-back-rail)', 'Creator': 'timc'})

# TODO add ebs_block_devices
# TODO add volume_tags
# TODO add iam_instance_profile
# TODO add user_data

server = ec2.Instance(
        resource_name = 'new-ec2',
        ami = 'ami-032509850cf9ee54e',  # TypeError if not present
        instance_type = _instance_type, # TypeError if not present
        security_groups = [sg.id],
        availability_zone = _availability_zone,
        subnet_id = subnet.id,
        associate_public_ip_address = False,
        key_name = 'sl-us-west-2',

        # TODO `Quiver`: `Pulumi > Questions > Adding tags forces EC2 replacement?`
        #   edit: I also changed the instance's `resource_name`
        tags = {'Name': 'infra ec2 (front-rail-back-rail)', 'Creator': 'timc'}
        )

# TODO bug? If you include `associate_with_private_ip = server.private_ip` but
# leave off `instance = server.id`, the association is not created
eip = ec2.Eip(resource_name = 'new-eip',
        instance = server.id,
        associate_with_private_ip = server.private_ip,
        tags = {'Name': 'infra eip (front-rail-back-rail)', 'Creator': 'timc'}
        )

# stack exports
pulumi.export('vpcID', vpc.id)
pulumi.export('subnetID', subnet.id)
pulumi.export('internetGatewayID', igw.id)
pulumi.export('routeTableID', rt.id)
pulumi.export('routeID', route.id)
pulumi.export('bucket_name',  bucket.bucket_domain_name)
pulumi.export('securityGroupID', sg.id)
pulumi.export('AMI', server.ami)
pulumi.export('instanceID', server.id)
pulumi.export('elasticIP', eip.public_ip)
pulumi.export('publicIP', server.public_ip)
pulumi.export('privateIP', server.private_ip)

