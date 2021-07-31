# PR2021-03-08 from https://simpleisbetterthancomplex.com/tutorial/2017/08/01/how-to-setup-amazon-s3-in-a-django-project.html

from storages.backends.s3boto3 import S3Boto3Storage

import boto3
from botocore.exceptions import ClientError

from awpr import settings

import logging

#class StaticStorage(S3Boto3Storage):
#    location = settings.AWS_STATIC_LOCATION

#class PublicMediaStorage(S3Boto3Storage):
#    location = settings.AWS_PUBLIC_MEDIA_LOCATION
#    file_overwrite = False

class PrivateMediaStorage(S3Boto3Storage):
    # attachments are stored in spaces awpmedia/awpmedia/media/private PR2021-07-27
    location = settings.AWS_PRIVATE_MEDIA_LOCATION
    default_acl = 'private'
    file_overwrite = False
    custom_domain = False


# PR2021-03-17 from https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-presigned-urls.html
def create_presigned_url(object_name):
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """
    expiration = 3600

    # Generate a presigned URL for the S3 object
    s3_client = boto3.client('s3')
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response
