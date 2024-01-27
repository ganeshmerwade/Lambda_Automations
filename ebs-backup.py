# This script will create a snapshot of volumes that match a certain filter based on tags which match [Backup]
# Creating the snapshot is determined based on a Backup tag (provided for volumes through terraform) and the date of the last snapshot in AWS.
# This scipt requires python 3.x 
# Additional information: https://medium.com/@codebyamir/automate-ebs-snapshots-using-aws-lambda-cloudwatch-1e2acfb0a45a#:~:text=In%20the%20Lambda%20console%2C%20go%20to%20Functions%20%3E,all%20regions%20import%20boto3%20def%20lambda_handler%20%28event%2C%20context%29%3A

import boto3
import traceback
from datetime import datetime

# get_volume_name function extracts name tag associated with volume.
# if there is no name tag avilable Volume id will be returned as Volume name
def get_volume_name(volume_obj):
    vol_name = ""
    if 'Tags' in volume_obj:
            for tags in volume_obj['Tags']:
                if tags['Key'] == 'Name':
                    vol_name = tags['Value']
    return vol_name                

# get_backup_frequency_value function extracts value of tag Backup (which shall be provided through terraform) and feed the value to variable frequency
def get_backup_frequency_value(volume_obj):
    if 'Tags' in volume_obj:
        for tags in volume_obj['Tags']:
            if tags['Key'] == 'Backup':
                frequency = tags['Value']
    return frequency

# time_difference function will estimate the difference in days between current time and start time of the last snapshot created for voulmeId under consideration
def time_difference(snapshot_obj):
    time_difference = datetime.now() - snapshot_obj.start_time.replace(tzinfo=None)
    days_difference_to_last_snap = time_difference.days
    return days_difference_to_last_snap

# get_sorted_snapshots function list all the previous snapshots of volume under consideration and sort them in descending order wrt start time
def get_sorted_snapshots(ec2client_obj,volume_obj):
    response = ec2client_obj.describe_snapshots(Filters=[{'Name': 'volume-id', 'Values': [volume_obj['VolumeId']]}])
    sorted_response = sorted(response['Snapshots'], key=lambda x: x['StartTime'], reverse=True)
    return sorted_response

# calculate_retention_period function returns retention period value for the snapshot (bacup frequency + 1 day)
def calculate_retention_period(volume_obj):
    calculated_retention_period = int(get_backup_frequency_value(volume_obj)) + 1
    return calculated_retention_period

# initiate_snapshot function creates snapshot and assigns tags (name and retention_period)
def initiate_snapshot(ec2client_obj, ec2resource_obj, vol_name, volume_obj):
    result = ec2client_obj.create_snapshot(VolumeId=volume_obj['VolumeId'],Description='Created by Lambda backup function ebs-snapshots')
    snap = ec2resource_obj.Snapshot(result['SnapshotId'])
    
    # Add volume name to snapshot for easier identification
    snap.create_tags(Tags=[{'Key': 'Name','Value': vol_name}])
    
    #add retention period in tags
    retention_period = calculate_retention_period(volume_obj)
    snap.create_tags(Tags=[{'Key': 'RetentionTime','Value': str(retention_period)}])

    #add creator tag
    snap.create_tags(Tags=[{'Key': 'CreatedBy','Value': 'ebsBackupLambdaFunction'}])

def update_report(report_dict, vol_name, status):
    report_dict[vol_name] = status

# Returns True if days since the last snapshot for the volume exceed the backup frequency.
# If there are no previous snapshots, returns True for the first-time snapshot creation.
def is_snapshot_needed(volume_obj, ec2client_obj, ec2resource_obj):
    backup_frequency = get_backup_frequency_value(volume_obj)
    sorted_snapshots = get_sorted_snapshots(ec2client_obj, volume_obj)

    if sorted_snapshots:
        days_difference = time_difference(ec2resource_obj.Snapshot(sorted_snapshots[0]['SnapshotId']))
        if days_difference > int(backup_frequency):
            return True, 'previously present', days_difference
        else:
            return False, 'previously present', days_difference
    else:
        return True, 'first time' , 0

# creates snapshots and updates report
def create_snapshot(volume_obj, ec2client_obj, ec2resource_obj, report_dict):
    try:
        vol_name = get_volume_name(volume_obj)
        if vol_name 
            should_create, status, days_difference = is_snapshot_needed(volume_obj, ec2client_obj, ec2resource_obj)
            
            if should_create:
                if status == 'first time':
                    print(f"Backing up {vol_name} for first time")   
                
                initiate_snapshot(ec2client_obj, ec2resource_obj, vol_name, volume_obj)
                update_report(report_dict, vol_name, 'SUCCESS')
            else:
                print(f"snapshot for {vol_name} is created {days_difference} days ago")
            
        else:
            update_report(report_dict, volume_obj['VolumeId'], f'FAILED: name tag unavailable')
    except Exception as e: 
        update_report(report_dict, vol_name, 'FAILED')
        print(f'{vol_name}')
        print(e)
        traceback.print_exc()

    return report_dict


# print_report functions prints the final report dictionary with snapshot name and its status
def print_report(report_dict):
    for key,value in report_dict.items():
        print(f'{key}: {value}')


def lambda_handler(event, context):
    ec2_client = boto3.client('ec2')
    ec2_resource = boto3.resource('ec2')
    
    # Get all in-use volumes in all regions
    result = ec2_client.describe_volumes( Filters=[{'Name': 'status', 'Values': ['in-use']}, {'Name': 'tag-key', 'Values': ['Backup']}])
    report = {}
    for volume_data in result['Volumes']: 
        report = create_snapshot(volume_data, ec2_client, ec2_resource, report)

    print_report(report)

