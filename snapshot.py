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

def time_difference(snapshot_obj):
    time_difference = datetime.now() - snapshot_obj.start_time.replace(tzinfo=None)
    days_difference_to_last_snap = time_difference.days
    return days_difference_to_last_snap

def create_snapshot(volume_obj, ec2client_obj, ec2resource_obj, vol_name,  report_dict):
    try:                             
        backup_frequency = get_backup_frequency_value(volume_obj)        
        
        # Find last snaphot for the volume        
        response = ec2client_obj.describe_snapshots(Filters=[{'Name': 'volume-id', 'Values': [volume_obj['VolumeId']]}])
        sorted_response = sorted(response['Snapshots'], key=lambda x: x['StartTime'], reverse=True)
        
        if sorted_response:
            snapshot = ec2resource_obj.Snapshot(sorted_response[0]['SnapshotId'])
            days_difference = time_difference(snapshot)
            
            if days_difference > int(backup_frequency):
                result = ec2client_obj.create_snapshot(VolumeId=volume['VolumeId'],Description='Created by Lambda backup function ebs-snapshots')
                snap = ec2resource_obj.Snapshot(result['SnapshotId'])
                
                # Add volume name to snapshot for easier identification
                snap.create_tags(Tags=[{'Key': 'Name','Value': vol_name}])
                
                #add retention period in tags
                retention_period = int(backup_frequency) + 1

                snap.create_tags(Tags=[{'Key': 'RetentionTime','Value': str(retention_period)}])
                report_dict[vol_name]='SUCCESS'
            else:
                print(f"snapshot for {vol_name} is created {days_difference} days ago")    
        else:         
        
            print(f"Backing up {volume_obj['VolumeId']} in {volume_obj['AvailabilityZone']} for first time")
        
            # Create snapshot
            result = ec2client_obj.create_snapshot(VolumeId=volume_obj['VolumeId'],Description='Created by Lambda backup function ebs-snapshots')
        
            # Get snapshot resource
            snapshot = ec2resource_obj.Snapshot(result['SnapshotId'])
                        
            # Add volume name to snapshot for easier identification
            snapshot.create_tags(Tags=[{'Key': 'Name','Value': vol_name}])

            #add retention period in tags
            retention_period = int(backup_frequency) + 1

            snapshot.create_tags(Tags=[{'Key': 'RetentionTime','Value': str(retention_period)}])

            report_dict[vol_name]='SUCCESS'

    except Exception as e: 
        report_dict[vol_name]='FAILED'
        print(f"{vol_name}")
        print(e)
        traceback.print_exc()

    return report_dict

def print_report(report_dict):
    """
    print_report functions prints the final report dictionary with snapshot name and its status
    """
    for key,value in report_dict.items():
        print(f"{key}: {value}")


def lambda_handler(event, context):
    ec2_client = boto3.client('ec2')
    ec2_resource = boto3.resource('ec2')
    
    # Get all in-use volumes in all regions
    result = ec2_client.describe_volumes( Filters=[{'Name': 'status', 'Values': ['in-use']}, {'Name': 'tag-key', 'Values': ['Backup']}])
    report = {}
    for volume_data in result['Volumes']: 
        volume_name =  get_volume_name(volume_data)
        report = create_snapshot(volume_data, ec2_client, ec2_resource, volume_name,  report)

    print_report(report)
