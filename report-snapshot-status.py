# The script is a Lambda function that checks and reports the status of EBS snapshots created by a backup function. 
# It identifies snapshots with a specific description, checks their status (pending, completed, or failed), and generates a report

import boto3
import traceback
import time

def get_snapshot_name(snapshot_obj):
    ss_name = snapshot_obj['SnapshotId']
    # Find name tag
    if 'Tags' in snapshot_obj:
                for tags in snapshot_obj['Tags']:
                    if tags["Key"] == 'Name':
                        ss_name = tags["Value"]
    return ss_name 

def update_report(snapshot_obj, ec2resource_obj, report_dict, ss_name):
    try:         
        # Get snapshot resource
        snap = ec2resource_obj.snapshot_obj(snapshot_obj['SnapshotId'])
                    
        if snap.state == 'pending':
            print(f"{ss_name}: {snap.state}")
            report_dict[ss_name]='PENDING'
        elif snap.state == 'completed':
            report_dict[ss_name]='SUCCESS'
        else:
            report_dict[ss_name]='FAILED'
    except Exception as e: 
        report_dict[ss_name]='FAILED'
        print(f"{ss_name}")
        print(e)
        traceback.print_exc()
    
    return report_dict 

def print_report(report_dict):
    for key,value in report.items():
        print(f"{key}: {value}")

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    ec2_resource = boto3.resource('ec2')

    # list the snapshots generated by lambda function
    result = ec2.describe_snapshots(Filters=[{'Name': 'description', 'Values': ['Created by Lambda backup function ebs-snapshots']}])
    report = {}
    for Snapshot in result['Snapshots']:
        snapshot_name = get_snapshot_name(Snapshot)
        report = update_report(snapshot, ec2_resource, report, snapshot_name)
        print_report(report)

    
    print('Snapshot status check completed')
