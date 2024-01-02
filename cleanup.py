# The script retrieves snapshots created by the Lambda backup function with a specific description 
# Evaluates their age based on a retention time(difined by lambda backup function), and deletes snapshots that exceed this retention period.


import boto3
import traceback
import time
from datetime import datetime, timedelta

def get_snapshot_name(snapshot_obj):
    """
    get_snapshot_name function extracts name tag assosiated with the Snapshot,
    if there is no name tag avilable snapshot id will be returned as snapshot name
    """
    ss_name = snapshot_obj['SnapshotId']
    # Find name tag
    if 'Tags' in snapshot_obj:
        for tags in snapshot_obj['Tags']:
            if tags["Key"] == 'Name':
                ss_name = tags["Value"]
    return ss_name 

def calculate_days_since(snap_start_time):
    """
    calculate_days_since function calculates time difference between snapshot start time and present time 
    and returns difference in days 
    """
    time_difference = datetime.now() - snap_start_time.replace(tzinfo=None)
    days_difference = time_difference.days
    return days_difference
    
def delete_snapshot(snapshot_obj, ec2resource_obj, report_dict, ss_name):
    try:
        if 'Tags' in snapshot_obj:
            for tags in snapshot_obj['Tags']:
                if tags["Key"] == 'RetentionTime':
                    retention_time = tags["Value"]
        
        # Get snapshot resource
        snap = ec2resource_obj.Snapshot(snapshot_obj['SnapshotId'])
        
        # Creation time of snapshot
        start_time = snap.start_time
        deletion_time = calculate_days_since(start_time)    
                
        # Delete Snapshot older than retaintion_time
        if deletion_time > int(retention_time):
            print(f"Deleting {ss_name}")
            snap.delete()
            report_dict[ss_name]='DELETED'
        else:
            report_dict[ss_name]=(f"NOT OLDER THAN {retention_time} DAYS")    
    
    except Exception as e: 
        report_dict[ss_name]='FAILED_TO_DELETE'
        print(f"{ss_name}")
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
    
    # list the snapshots generated by lambda function
    result = ec2_client.describe_snapshots(Filters=[{'Name': 'description', 'Values': ['Created by Lambda backup function ebs-snapshots']}])
    report = {}
    for snapshot_data in result['Snapshots']:
        snapshot_name = get_snapshot_name(snapshot_data)
        report = delete_snapshot(snapshot_data, ec2_resource, report, snapshot_name)    
        
    print_report(report)

    print('Snapshot cleanup completed')
