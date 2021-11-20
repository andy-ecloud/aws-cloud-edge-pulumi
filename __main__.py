import pulumi
import pulumi_aws as aws
import pulumi_tls as tls
import json

admin_policy = aws.iam.get_policy(name="AdministratorAccess")
pulumi.export("iam ssm policy", admin_policy.arn)

# create role (cloud watch agent and ssm)
admin_role = aws.iam.Role(
    "ad_profile",
    name="ad_profile",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Sid": "",
                    "Principal": {
                        "Service": "ec2.amazonaws.com",
                    },
                }
            ],
        }
    ),
    managed_policy_arns=[
        admin_policy.arn,
    ],
    tags={
        "Owner": "andy.chuang",
    },
    )

instance_profile = aws.iam.InstanceProfile(
    "instance-profile", role=admin_role.name
)

ami = aws.ec2.get_ami(most_recent=True,
                  owners=["amazon"],
                  filters=[aws.GetAmiFilterArgs(name="name", values=["amzn-ami-hvm-*"])])

group = aws.ec2.SecurityGroup('all-traffic',
    description='Enable HTTP access',
    ingress=[aws.ec2.SecurityGroupIngressArgs(
        protocol='tcp',
        from_port=1,
        to_port=65535,
        cidr_blocks=['0.0.0.0/0'],
    )],
    egress=[aws.ec2.SecurityGroupEgressArgs(
        from_port=0,
        to_port=0,
        protocol="-1",
        cidr_blocks=["0.0.0.0/0"],
        ipv6_cidr_blocks=["::/0"],
    )])

# create key
private_key = tls.PrivateKey('private_key',
              algorithm = 'RSA',
              rsa_bits=2048)
               
pulumi.export('public openssh', private_key.public_key_openssh)
pulumi.export('public pem', private_key.public_key_pem)
pulumi.export('private pem', private_key.private_key_pem)

# create key pair
keypair = aws.ec2.KeyPair("keypair",
    key_name="keypair",
    public_key=private_key.public_key_openssh)

backend = aws.ec2.Instance('backend',
    instance_type='t3.micro',
    iam_instance_profile=instance_profile.name,
    vpc_security_group_ids=[group.id],
    user_data=(lambda path: open(path).read())(
        "./userdata_backend.sh"
    ),
    ami=ami.id,
    key_name=keypair.id,
    tags={
        "Name": "backend"
    })

pulumi.export('backend public_ip', backend.public_ip)


userdata_frontend = pulumi.Output.all([backend.public_ip]).apply(lambda args:
    """#!/bin/bash
    # install 
    sudo yum update -y
    sudo yum install java-11-amazon-corretto -y
    sudo wget https://repos.fedorapeople.org/repos/dchen/apache-maven/epel-apache-maven.repo -O /etc/yum.repos.d/epel-apache-maven.repo
    sudo sed -i s/\$releasever/6/g /etc/yum.repos.d/epel-apache-maven.repo
    sudo yum install -y apache-maven
    sudo yum install java-1.8.0-devel -y
    sudo update-alternatives --set java /usr/lib/jvm/java-11-amazon-corretto.x86_64/bin/java
    sudo yum install -y git
    
    # run
    git clone https://github.com/andy-ecloud/cloud-edge-lab-template.git /cloud-edge-lab-template
    mvn install -f /cloud-edge-lab-template/api-parent/pom.xml
    mvn install -f /cloud-edge-lab-template/api-frontend/pom.xml
    
    sed -i 's/localhost/{}/g' /cloud-edge-lab-template/api-frontend/src/main/resources/application.yml 
    mvn spring-boot:run -f /cloud-edge-lab-template/api-frontend/pom.xml
    """.format(args[0][0])
)

frontend = aws.ec2.Instance('frontend',
    instance_type='t3.micro',
    iam_instance_profile=instance_profile.name,
    vpc_security_group_ids=[group.id],
    user_data=userdata_frontend,
    ami=ami.id,
    key_name=keypair.id,
    tags={
        "Name": "frontend"
    })

pulumi.export('frontend public_ip', frontend.public_ip)