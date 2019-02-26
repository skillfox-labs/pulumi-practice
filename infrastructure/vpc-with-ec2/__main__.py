import pulumi
from pulumi_aws import ec2, s3

vpc = ec2.Vpc(resource_name = 'new-vpc', cidr_block = "10.0.0.0/16")
subnet = ec2.Subnet(resource_name = 'new-subnet', vpc_id = vpc.id, cidr_block = "10.0.0.0/20")
sg = ec2.SecurityGroup(resource_name = 'new-sg', vpc_id = vpc.id)
ig = ec2.InternetGateway(resource_name = 'new-ig', vpc_id = vpc.id)
bucket = s3.Bucket('my-bucket')

# TODO add instance to new VPC
#   seems like that's by association w/ subnet
#
# TODO bug? `associate_public_ip_address = False` doesn't seem to do anything
#   edit: after `pulumi destroy` and `pulumi update`, seems to be working
#
# TODO bug? See ~/z/src/github.com/tcondit/idea-foundry/bug-and-doc-fixes/01-pulumi-update-ec2-az.md
#   edit: unsupported feature on the AWS side
#   edit: maybe a Pulumi usability bug? This will cause occasional failures if not explicit

server = ec2.Instance(
        resource_name = 'webserver-www',
        ami = 'ami-032509850cf9ee54e',  # TypeError if not present
        instance_type = 't2.micro',     # TypeError if not present
        associate_public_ip_address = False,
        security_groups = [sg.id],
        subnet_id = subnet.id,
        )

# TODO bug? If you include `associate_with_private_ip=server.private_ip` but
# leave off `instance=server.id`, the association is not created
eip = ec2.Eip(resource_name='new-eip', instance=server.id, associate_with_private_ip=server.private_ip)

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

