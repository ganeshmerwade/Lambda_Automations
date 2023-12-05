# Backup all in-use volumes in all regions
# Detailed instructions available on 
#https://medium.com/@codebyamir/automate-ebs-snapshots-using-aws-lambda-cloudwatch-1e2acfb0a45a#:~:text=In%20the%20Lambda%20console%2C%20go%20to%20Functions%20%3E,all%20regions%20import%20boto3%20def%20lambda_handler%20%28event%2C%20context%29%3A
import boto3
import traceback
import time
def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    
    # Get all in-use volumes in all regions
    result = ec2.describe_volumes( Filters=[{'Name': 'status', 'Values': ['in-use']}, {'Name': 'tag:Backup', 'Values': ['15-days']}])
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

            #wait for snapshot to complete
            while snapshot.state == 'pending':
                print(f"{volumename}: {snapshot.state}")
                time.sleep(1)
                snapshot.reload()

            if snapshot.state == 'completed':

                # Add volume name to snapshot for easier identification
                snapshot.create_tags(Tags=[{'Key': 'Name','Value': volumename}])

                report[volumename]='SUCCESS'
            else:
                report[volumename]='FAILED'
        except Exception as e: 
            report[volumename]='FAILED'
            print(f"{volumename}")
            print(e)
            traceback.print_exc()

    for key,value in report.items():
        print(f"{key}: {value}")
