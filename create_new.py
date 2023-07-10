import boto3
import config

def __create_ec2_instance(ec2_resource):
    def create_ec2_instance(ec2_resource):
        # Launch a new instance
        instance = ec2_resource.create_instances(
            ImageId='ami-002843b0a9e09324a',  # Specify the AMI ID for the desired instance image
            InstanceType='t2.micro',  # Specify the instance type
            MinCount=1,
            MaxCount=1,
        )[0]

        # Wait for the instance to be running
        instance.wait_until_running()

        # Return the instance ID
        return instance.id

    def run_commands_on_instance(instance_id, commands):
        # Create an SSM client
        ssm_client = boto3.client('ssm')

        # Send the commands to the instance
        response = ssm_client.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',
            Parameters={'commands': commands},
        )

        # Get the command ID
        command_id = response['Command']['CommandId']

        # Wait for the command to complete
        waiter = ssm_client.get_waiter('command_executed')
        waiter.wait(
            CommandId=command_id,
            InstanceId=instance_id,
        )

        # Get the command invocation details
        output = ssm_client.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id,
        )

        # Print the command output
        print('Command Output:')
        print(output['StandardOutput'])
        print('Command Error:')
        print(output['StandardError'])

    # Create a new EC2 instance
    instance_id = create_ec2_instance(ec2_resource)

    # Define the commands to run on the instance
    with open("new_starting_script.txt", "r") as f:
        commands = [f.replace("\n", "") for f in f.readlines()]

    # Run the commands on the instance
    run_commands_on_instance(instance_id, commands)
    # open port 46642 
    ec2_resource.SecurityGroup(instance_id).authorize_ingress(
        IpProtocol="tcp",
        FromPort=46642,
        ToPort=46642,
        CidrIp="0.0.0.0/0"
    )
    
    return instance_id


if __name__ == "__main__":
    instance_id = __create_ec2_instance(ec2_resource=boto3.resource(
        'ec2',
        region_name=config.Credentials.region,
        aws_access_key_id=config.Credentials.key,
        aws_secret_access_key=config.Credentials.secret
        )
    )
    print(instance_id)

