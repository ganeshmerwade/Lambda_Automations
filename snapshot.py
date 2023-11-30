# Backup all in-use volumes in all regions
# Detailed instructions available on https://medium.com/nerd-for-tech/ebs-snapshot-management-using-aws-lambda-and-cloudwatch-d961fdbe3772
import boto3
def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    
    # Get all in-use volumes in all regions 
    result = ec2.describe_volumes( Filters=[{'Name': 'status', 'Values': ['in-use']}])
    report = {}
    for volume in result['Volumes']:
        try:
            print(f"Backing up {volume['VolumeId']} in {volume['AvailabilityZone']}")
            
            # Create snapshot
            result = ec2.create_snapshot(VolumeId=volume['VolumeId'],Description='Created by Lambda backup function ebs-snapshots')
            
            # Get snapshot resource
            ec2resource = boto3.resource('ec2')
            snapshot = ec2resource.Snapshot(result['SnapshotId'])
            
            # Find name tag for volume
            if 'Tags' in volume:
                for tags in volume['Tags']:
                    if tags["Key"] == 'Name':
                        volumename = tags["Value"]
            else:
                volumename = 'N/A'
                
            # Add volume name to snapshot for easier identification
            snapshot.create_tags(Tags=[{'Key': 'Name','Value': volumename}])
            report[volumename]='SUCCESS'
        except Exception as e: 
            report[volumename]='FAILED'
            print(f"{volumename}")
            print(e)

    for key,value in report.items():
        print(f"{key}: {value}")
