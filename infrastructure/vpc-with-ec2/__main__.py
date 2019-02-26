import pulumi
from pulumi_aws import ec2, s3

_az = 'us-west-2b'  # t2.micro not supported in us-west-2

vpc = ec2.Vpc(resource_name = 'new-vpc',
        cidr_block = '10.0.0.0/16',
        tags = {'Name': 'infra vpc', 'Creator': 'timc'})

subnet = ec2.Subnet(resource_name = 'new-subnet',
        vpc_id = vpc.id,
        cidr_block = '10.0.0.0/20',
        availability_zone = _az,
        tags = {'Name': 'infra subnet', 'Creator': 'timc'})

ig = ec2.InternetGateway(resource_name = 'new-ig',
        vpc_id = vpc.id,
        tags = {'Name': 'infra internet gateway', 'Creator': 'timc'})

sg = ec2.SecurityGroup(resource_name = 'new-sg',
        description = 'HTTP and SSH ingress',
        vpc_id = vpc.id,
        ingress = [
            {'protocol': 'tcp', 'fromPort': 22, 'toPort': 22, 'cidrBlocks': ['0.0.0.0/0']},
            {'protocol': 'tcp', 'fromPort': 80, 'toPort': 80, 'cidrBlocks': ['0.0.0.0/0']},
            ],
        tags = {'Name': 'infra security group', 'Creator': 'timc'})

bucket = s3.Bucket(resource_name = 'new-bucket',
        tags = {'Name': 'infra bucket', 'Creator': 'timc'})

# TODO add instance to new VPC
#   seems like that's by association w/ subnet
#
# TODO bug? `associate_public_ip_address = False` doesn't seem to do anything
#   edit: after `pulumi destroy` and `pulumi update`, seems to be working
#
# TODO bug? See ~/z/src/github.com/tcondit/idea-foundry/bug-and-doc-fixes/01-pulumi-update-ec2-az.md
#   edit: unsupported feature on the AWS side
#   edit: maybe a Pulumi usability bug? This will cause occasional failures if not explicit

# TODO tags
server = ec2.Instance(
        resource_name = 'new-ec2',
        ami = 'ami-032509850cf9ee54e',  # TypeError if not present
        instance_type = 't2.micro',     # TypeError if not present
        security_groups = [sg.id],
        availability_zone = _az, 
        subnet_id = subnet.id,
        associate_public_ip_address = False,

        # TODO `Quiver`: `Pulumi > Questions > Adding tags forces EC2 replacement?`
        #   edit: I also changed the instance's `resource_name`
        tags = {'Name': 'infra ec2', 'Creator': 'timc'}
        )

# TODO bug? If you include `associate_with_private_ip=server.private_ip` but
# leave off `instance=server.id`, the association is not created
eip = ec2.Eip(resource_name='new-eip',
        instance=server.id,
        associate_with_private_ip=server.private_ip)

# Export the DNS name of the bucket
pulumi.export('vpcID', vpc.id)
pulumi.export('internetGatewayID', ig.id)
pulumi.export('subnetID', subnet.id)
pulumi.export('securityGroupID', sg.id)
pulumi.export('AMI', server.ami)
pulumi.export('instanceID', server.id)
pulumi.export('elasticIP', eip.public_ip)
pulumi.export('publicIP', server.public_ip)
pulumi.export('privateIP', server.private_ip)
pulumi.export('bucket_name',  bucket.bucket_domain_name)

