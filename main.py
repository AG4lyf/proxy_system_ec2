from ec2_proxy import TProxy
import boto3
import config
import threading
import time
from create_new import __create_ec2_instance

class Manager:
    def __init__(self) -> None:
        ec2_resource = boto3.resource('ec2', 
                                      region_name=config.Credentials.region, 
                                      aws_access_key_id=config.Credentials.key, 
                                      aws_secret_access_key=config.Credentials.secret
                                      )
        ec2 = boto3.client('ec2', 
                           region_name=config.Credentials.region, 
                           aws_access_key_id=config.Credentials.key, 
                           aws_secret_access_key=config.Credentials.secret
                           )    
        nodes = []
        response = ec2.describe_instances()
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                if instance['InstanceId'] not in config.Exclusions.ids:
                    nodes.append(instance['InstanceId'])
        # start the nodes if they are not running
        for node in nodes:
            TProxy(instance_id=node, ec2=ec2).start()
        self.ec2_reserouce = ec2_resource
        self.nodes = nodes
        self.ec2 = ec2
        self.in_use = []
        self.to_restart = []
        self.__start_auto_method()

    def make_new_proxy(self):
        new_instance_id = __create_ec2_instance(self.ec2_reserouce)
        self.nodes.append(new_instance_id)
        return new_instance_id
        
    def serve(self, old_instance_id):
        if old_instance_id in self.in_use:
            self.in_use.remove(old_instance_id)
        if len(self.nodes) == 0:
            return None
        new_instance_id = self.nodes.pop()
        self.in_use.append(new_instance_id)
        self.to_restart.append(old_instance_id)
        # return the public ip of the new instance
        response = self.ec2.describe_instances(InstanceIds=[new_instance_id])
        return response['Reservations'][0]['Instances'][0]['PublicIpAddress']
    
    def cleanup(self):
        print("Cleaning up")
        for instance_id in self.to_restart:
            TProxy(instance_id=instance_id, ec2=self.ec2).restart()
        self.to_restart = []
        threading.Timer(60, self.cleanup).start()

    def __start_auto_method(self):
        threading.Timer(0, self.cleanup).start()

my_object = Manager()

# Keep the program running
while True:
    time.sleep(1)
