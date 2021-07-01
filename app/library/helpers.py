import os.path
import markdown
import pandas as pd
import Model
import os
import logging
import boto3
from botocore.exceptions import ClientError
from botocore.client import Config


# AWS_SECRET_ACCESS_KEY =
# AWS_ACCESS_KEY_ID =
AWS_S3_REGION_NAME = "ap-south-1"
AWS_S3_BUCKET = 'nqr-poc-bucket'
# AWS_S3_BUCKET = 'nlp-as-a-service-bucket'
PREFIX_NQR = 'NQR/'
PREFIX_QE = 'QE/'
PREFIX_FR = 'FR/'


def openfile(filename):
    filepath = os.path.join("app/pages/", filename)
    with open(filepath, "r", encoding="utf-8") as input_file:
        text = input_file.read()

    html = markdown.markdown(text)
    data = {
        "text": html
    }
    return data


def append_id(df1, df2):
    database = df1['Question'].tolist()
    ids = df1['FAQ Id'].tolist()
    dict_database = dict(zip(ids, database))
    lst = []
    for utt in df2['closest_found_utt'].tolist():
        for key, value in dict_database.items():
            if utt != value:
                continue
            lst.append(key)
    df2['closest_found_utt_id'] = pd.Series(lst).values
    return df2


def predict_nqr(df, top_k):
    # top_k = request.json['top_k']
    queries = df['Question'].tolist()
    req_format_list = []
    for query in queries:
        score_list, sentences_list = Model.get_scores(query, queries, topk=top_k)
        if len(sentences_list) == 0:
            first = " "
        else:
            first = sentences_list[0]
            for i in range(1, len(sentences_list)):
                first = first + "$$$" + sentences_list[i]
        req_format_list.append(first)
    df['Recommendation'] = pd.Series(req_format_list)
    return df


def predict_qe(df):
    # top_k = request.json['top_k']
    req_format_list = []
    filtered_df = df[df['Variation'].isnull()]
    queries = filtered_df['Question'].tolist()
    for query in queries:
        sentences = Model.generate_paraphrases(query, topk=5)
        first = sentences[0]
        for i in range(1, len(sentences)):
            first = first + "$$$" + sentences[i]
        req_format_list.append(first)
    filtered_df['Variation'] = pd.Series(req_format_list).values
    df["Variation"].fillna(filtered_df["Variation"], inplace=True)
    return df


def predict_fr(df3, df4, top_k=1):
    # top_k = request.json['top_k']
    df4['Utterance'] = df4['Utterance'].astype(str)
    database = df3['Question'].tolist()
    queries = df4['Utterance'].tolist()
    utt_list = []
    scores = []
    for query in queries:
        score_list, sentences_list = Model.get_scores(query, database, topk=top_k)
        if len(sentences_list) == 0:
            first = " "
        else:
            first = sentences_list[0]
            score = score_list[0]
        utt_list.append(first)
        scores.append(score)
    df4['closest_found_utt'] = pd.Series(utt_list).values
    df4['similarity_score'] = pd.Series(scores).values
    res = append_id(df3, df4)
    return res


def create_presigned_post(bucket_name, object_name,
                          fields=None, conditions=None, expiration=3600):
    """Generate a presigned URL S3 POST request to upload a file

    :param bucket_name: string
    :param object_name: string
    :param fields: Dictionary of prefilled form fields
    :param conditions: List of conditions to include in the policy
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Dictionary with the following keys:
        url: URL to post to
        fields: Dictionary of form fields and values to submit with the POST
    :return: None if error.
    """

    # Generate a presigned S3 POST URL
    s3_client = boto3.client('s3')
    try:
        response = s3_client.generate_presigned_post(bucket_name,
                                                     object_name,
                                                     Fields=fields,
                                                     Conditions=conditions,
                                                     ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL and required fields
    return response


def create_presigned_url(bucket_name, object_name, expiration=3600):
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    # Generate a presigned URL for the S3 object
    s3_client = boto3.client('s3', region_name=AWS_S3_REGION_NAME, config=Config(signature_version='s3v4'))
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response


def upload_file(file_name, bucket):
    """
    Function to upload a file to an S3 bucket
    """
    object_name = file_name
    s3_client = boto3.client('s3', aws_secret_access_key=AWS_SECRET_ACCESS_KEY, aws_access_key_id=AWS_ACCESS_KEY_ID,)
    response = s3_client.upload_file(file_name, bucket, object_name)
    return response


def download_file(bucket, prefix):
    """
    Function to download a given file from an S3 bucket
    """
    s3_client = boto3.client('s3', aws_secret_access_key=AWS_SECRET_ACCESS_KEY, aws_access_key_id=AWS_ACCESS_KEY_ID)
    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
    files_list = response['Contents']
    latest_key = max(files_list, key=lambda x: x['LastModified'])
    filename = os.path.basename(latest_key['Key'])
    output = "downloads" + "/" + filename
    # print(output)
    s3_client.download_file(bucket, latest_key['Key'], filename)
    return response


def get_object_name(bucket, prefix):
    s3_client = boto3.client('s3', aws_secret_access_key=AWS_SECRET_ACCESS_KEY, aws_access_key_id=AWS_ACCESS_KEY_ID)
    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
    files_list = response['Contents']
    latest_key = max(files_list, key=lambda x: x['LastModified'])
    # filename = os.path.basename(latest_key['Key'])
    return latest_key['Key']

