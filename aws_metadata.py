
import boto3
import json
import sys

def get_s3_metadata(config_item):
    metadata_list = []
    name = config_item['resourceName']
    configuration = config_item['supplementaryConfiguration']
    encryption =  json.loads((configuration['ServerSideEncryptionConfiguration']))['rules'][0]['applyServerSideEncryptionByDefault']['sseAlgorithm']
    logging = True if json.loads(configuration['BucketLoggingConfiguration'])['destinationBucketName'] else False

    try:
        public = s3.get_bucket_policy_status(Bucket=name)['PolicyStatus']['IsPublic']
    except:
        public = None

    try:
        lifecycle = s3.get_bucket_lifecycle_configuration(Bucket=name)['Rules']
        lifecycle = True
    except:
        lifecycle = False

    metadata = {
        'AccountId': config_item['accountId'],
        'Region': config_item['awsRegion'],
        'BucketName': name,
        'CreationTime': str(config_item['resourceCreationTime']),
        'Encryption':encryption,
        'Logging': logging,
        'IsPublic': public,
        'StorageClass': config_item.get('StorageClass', 'Standard'),
        'Lifecycle': lifecycle
    }
    metadata_list.append(metadata)
    return metadata_list

def get_ec2_metadata(config_item):
    metadata_list = []
    name = config_item['tags']['Name']
    configuration = json.loads(config_item['configuration'])

    security_group_check = False
    for group in configuration['securityGroups']:
        if group['groupName'] == 'launch-wizard-1':
            security_group_check = True
            break

    metadata = {
        'AccountId': config_item['accountId'],
        'Region': config_item['awsRegion'],
        'InstanceName': name,
        'CreationTime': str(config_item['resourceCreationTime']),
        'LaunchTime': configuration['launchTime'],
        'State': configuration['state']['name'],
        'OS': configuration['platformDetails'],
        'InstanceType': configuration['instanceType'],
        'PublicIpAddress': configuration['publicIpAddress'],
        'PrivateIpAddress': configuration['privateIpAddress'],
        'KeyPair': configuration['keyName'],
        'IAMRole': configuration['iamInstanceProfile'],
        'SecurityGroupCheck': security_group_check

    }

    metadata_list.append(metadata)
    return metadata_list


def get_ecr_metadata(config_item):
    metadata_list = []
    name = config_item['resourceName']
    configuration = json.loads(config_item['configuration'])
    encryption_type = configuration['EncryptionConfiguration']['EncryptionType']
    scan_on_push = configuration['ImageScanningConfiguration']['ScanOnPush']
    lifecycle = True if len(configuration['LifecyclePolicy'])>0 else False
    images = ecr.list_images(repositoryName=name)['imageIds']
    for image in images:
        image_info = ecr.describe_images(repositoryName=name, imageIds=[image])['imageDetails'][0]
        image_tag = image_info.get('imageTags', ['<untagged>'])
        image_size = image_info.get('imageSizeInBytes', 0) / (1024 * 1024)

        metadata = {
            'AccountId': config_item['accountId'],
            'Region': config_item['awsRegion'],
            'ImageName': name,
            'CreationTime': str(config_item['resourceCreationTime']),
            'ImageTag': image_tag,
            'ImageSize':image_size,
            'EncryptionType':encryption_type,
            'ScanOnPush': scan_on_push,
            'Lifecycle': lifecycle
        }
        metadata_list.append(metadata)
    return metadata_list

service_types = {
    'S3': 'AWS::S3::Bucket',
    'EC2': 'AWS::EC2::Instance',
    'ECR': 'AWS::ECR::Repository',
    'EKS': 'AWS::EKS::Cluster'
}


try:
    service = sys.argv[1]
except:
    service = 'S3'

print("==========")
print("Now getting the metadata of :", service)
print("==========\n")

rtype = service_types[service]
config = boto3.client('config')

paginator = config.get_paginator('list_discovered_resources')
for page in paginator.paginate(resourceType=rtype):
    for resource in page['resourceIdentifiers']:
        config_item = config.get_resource_config_history(
            resourceType=rtype,
            resourceId=resource['resourceId'],
            limit=1
        )['configurationItems'][0]

        match service:
            case "S3":
                s3 = boto3.client('s3')
                metadata_list = get_s3_metadata(config_item)
            case 'EC2':
                metadata_list = get_ec2_metadata(config_item)
            case 'ECR':
                ecr = boto3.client('ecr')
                metadata_list = get_ecr_metadata(config_item)
            case 'EKS':
                print("not ready")
            case _:
                print("not ready")
                metadata_list = []
        
        for metadata in metadata_list:
            print("====================")
            print(metadata)
            print("====================")
            print("\n")