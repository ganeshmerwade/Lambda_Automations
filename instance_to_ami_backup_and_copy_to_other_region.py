import json
import boto3

def main():
    ec2 = boto3.resource('ec2', region_name='us-east-1')
    image_ids = []
    
    instances = ec2.instances.filter(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running','stopped']}])
    
    for i,instance in enumerate(instances):
        print(f'Instance ID: {instance.id},Instance Placement: {instance.placement}')
        image = instance.create_image(Name='AMI Copy For '+instance.id+'_'+str(i))
        image_ids.append(image.id)
    
    print("Images to be copied are ", image_ids)
    
    # Waiting For Images Using Paginators
    
    ec2_client = boto3.client('ec2', region_name='us-east-1')
    waiter = ec2_client.get_waiter('image_available')
    waiter.wait(Filters=[{
     'Name': 'image-id',
     'Values': image_ids
    }])
    
    # Copy Images To Other Regions
    
    ec2_client = boto3.client('ec2', region_name='ap-south-1')
    for image_id in image_ids:
        ec2_client.copy_image(Name='AMI Copy From US-EAST-1'+image_id, SourceImageId=image_id, SourceRegion='us-east-1')



def lambda_handler(event, context):
    # TODO implement
    main()
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
