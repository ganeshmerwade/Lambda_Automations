# This script will create a snapshot of volumes that match a certain filter based on tags which match [Backup]
# Creating the snapshot is determined based on a Backup tag (provided for volumes through terraform) and the date of the last snapshot in AWS.
# This scipt requires python 3.x 
# Additional information: https://medium.com/@codebyamir/automate-ebs-snapshots-using-aws-lambda-cloudwatch-1e2acfb0a45a#:~:text=In%20the%20Lambda%20console%2C%20go%20to%20Functions%20%3E,all%20regions%20import%20boto3%20def%20lambda_handler%20%28event%2C%20context%29%3A

import boto3
import traceback
import time
from datetime import datetime, timedelta

def get_volume_name(volume_obj):
    vol_name = volume_obj['VolumeId']
    if 'Tags' in volume_obj:
            for tags in volume_obj['Tags']:
                if tags["Key"] == 'Name':
                    vol_name = tags["Value"]

    return vol_name                

def get_backup_frequency_value(volume_obj):
    if 'Tags' in volume:
        for tags in volume['Tags']:
            if tags["Key"] == 'Backup':
                frequency = tags["Value"]
    return frequency

def find_latest_snapshot(ec2client_obj, volume_obj):
    response = ec2client_obj.describe_snapshots(Filters=[{'Name': 'volume-id', 'Values': [volume_obj['VolumeId']]}])
    sorted_response = sorted(response['Snapshots'], key=lambda x: x['StartTime'], reverse=True)

    return sorted_response

def create_snapshot(volume_obj, ec2client_obj, ec2resource_obj, vol_name,  report_dict):
    try:                             
            backup_frequency = get_backup_frequency_value(volume_obj)        
            
            latest_snapshot = find_latest_snapshot(ec2client_obj, volume_obj)            
            if latest_snapshot:
                snapshot = ec2resource_obj.Snapshot(latest_snapshot[0]['SnapshotId'])
                time_difference = datetime.now() - snapshot.start_time.replace(tzinfo=None)
                days_difference = time_difference.days
                
                if days_difference > int(frequency):
                    result = ec2client_obj.create_snapshot(VolumeId=volume['VolumeId'],Description='Created by Lambda backup function ebs-snapshots')
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

def lambda_handler(event, context):
    ec2_client = boto3.client('ec2')
    ec2_resource = boto3.resource('ec2')
    
    # Get all in-use volumes in all regions
    result = ec2_client.describe_volumes( Filters=[{'Name': 'status', 'Values': ['in-use']}, {'Name': 'tag-key', 'Values': ['Backup']}])
    report = {}
    for volume_data in result['Volumes']: 
        get_volume_name =  get_volume_name(volume_data)

        

    for key,value in report.items():
        print(f"{key}: {value}")
