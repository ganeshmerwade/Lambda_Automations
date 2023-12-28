# Backup all in-use volumes in all regions
# Detailed instructions available on 
#https://medium.com/@codebyamir/automate-ebs-snapshots-using-aws-lambda-cloudwatch-1e2acfb0a45a#:~:text=In%20the%20Lambda%20console%2C%20go%20to%20Functions%20%3E,all%20regions%20import%20boto3%20def%20lambda_handler%20%28event%2C%20context%29%3A
import boto3
import traceback
import time
from datetime import datetime, timedelta
def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    ec2resource = boto3.resource('ec2')
    
    # Get all in-use volumes in all regions
    result = ec2.describe_volumes( Filters=[{'Name': 'status', 'Values': ['in-use']}, {'Name': 'tag-key', 'Values': ['Backup']}])
    report = {}
    for volume in result['Volumes']:
        volume_id = volume['VolumeId']
        volume_name = volume['VolumeId']
        # Find name tag for volume
        if 'Tags' in volume:
            for tags in volume['Tags']:
                if tags["Key"] == 'Name':
                    volume_name = tags["Value"]
        try:                        
            if 'Tags' in volume:
                for tags in volume['Tags']:
                    if tags["Key"] == 'Backup':
                        frequency = tags["Value"]    
            
            # Find last snaphot for the volume        
            response = ec2.describe_snapshots(Filters=[{'Name': 'volume-id', 'Values': [volume_id]}])
            sorted_response = sorted(response['Snapshots'], key=lambda x: x['StartTime'], reverse=True)
            
            if sorted_response:
                # latest_snapshot_id = sorted_response[0]['SnapshotId']
                ec2resource = boto3.resource('ec2')
                snapshot = ec2resource.Snapshot(sorted_response[0]['SnapshotId'])
                time_difference = datetime.now() - snapshot.start_time.replace(tzinfo=None)
                days_difference = time_difference.days
                
                if days_difference > int(frequency):
                    result = ec2.create_snapshot(VolumeId=volume['VolumeId'],Description='Created by Lambda backup function ebs-snapshots')
                    snap = ec2resource.Snapshot(result['SnapshotId'])
                    
                    # Add volume name to snapshot for easier identification
                    snap.create_tags(Tags=[{'Key': 'Name','Value': volume_name}])
                    
                    #add retention period in tags
                    retention_period = int(frequency) + 1

                    snap.create_tags(Tags=[{'Key': 'RetentionTime','Value': str(retention_period)}])
                    report[volume_name]='SUCCESS'
                else:
                    print(f"snapshot for {volume_name} is created {days_difference} days ago")    
            else:         
            
                print(f"Backing up {volume['VolumeId']} in {volume['AvailabilityZone']} for first time")
            
                # Create snapshot
                result = ec2.create_snapshot(VolumeId=volume['VolumeId'],Description='Created by Lambda backup function ebs-snapshots')
            
                # Get snapshot resource
                snapshot = ec2resource.Snapshot(result['SnapshotId'])
                            
                # Add volume name to snapshot for easier identification
                snapshot.create_tags(Tags=[{'Key': 'Name','Value': volume_name}])

                #add retention period in tags
                retention_period = int(frequency) + 1

                snapshot.create_tags(Tags=[{'Key': 'RetentionTime','Value': str(retention_period)}])

                report[volume_name]='SUCCESS'

        except Exception as e: 
            report[volume_name]='FAILED'
            print(f"{volume_name}")
            print(e)
            traceback.print_exc()

    for key,value in report.items():
        print(f"{key}: {value}")
