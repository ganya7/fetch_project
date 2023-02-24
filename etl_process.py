import boto3
import json
from hashlib import sha256
from datetime import date
import psycopg2
from psycopg2.extras import execute_values

sqs = boto3.setup_default_session(region_name="us-west-1")
sqs = boto3.client("sqs", endpoint_url="http://localhost:4566/000000000000/login-queue")

queue_url = "http://localhost:4566/000000000000/login-queue"
user_values = []

print("Polling the queue to receive message")
response = sqs.receive_message(
    QueueUrl=queue_url, MaxNumberOfMessages=1, WaitTimeSeconds=1
)
if not "Messages" in response:
    print("No messages")
messages = response["Messages"]

while len(messages) > 0:
    message = response["Messages"][0]
    receipt_handle = message["ReceiptHandle"]

    user_login = {}
    user_login = json.loads(message["Body"])
    try:
        # encrypt and mask ip and device_id using sha256
        user_login["masked_ip"] = sha256(user_login["ip"].encode()).hexdigest()
        user_login["masked_device_id"] = sha256(
            user_login["device_id"].encode()
        ).hexdigest()

        # remove ip, device_id key-pair from dict
        user_login.pop("ip")
        user_login.pop("device_id")

        user_login["create_date"] = date.today().strftime("%m/%d/%y")
        user_login["app_version"] = user_login["app_version"].replace(".", "")

        # convert locale=None to str 'null'
        if user_login["locale"] is None:
            user_login["locale"] = "null"

        print(user_login)
        user_values.append(user_login)
    except KeyError:
        print("Missing column in input data")

    print("Polling the queue to receive message")
    response = sqs.receive_message(
        QueueUrl=queue_url, MaxNumberOfMessages=1, WaitTimeSeconds=1
    )
    if not "Messages" in response:
        print("No messages")
        break
    messages = response["Messages"]

    # delete the message from the queue
    sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
    print("Message processed and deleted from queue")

print("Completed processing the queue")

try:
    print("Connecting to Postgres database")

    conn = psycopg2.connect(
        database="postgres",
        user="postgres",
        password="postgres",
        host="127.0.0.1",
        port="5432",
    )

    print("Connected to database")

    conn.autocommit = True

    cursor = conn.cursor()
    columns = user_values[0].keys()
    user = user_values[0]

    query = "INSERT INTO user_logins ({}) VALUES %s".format(",".join(columns))
    values = [[value for value in user_login.values()] for user_login in user_values]
    # bulk insert into database
    execute_values(cursor, query, values)
    print("Inserted into the database")

    conn.commit()
    conn.close()
    print("Postgres database connection closed")

except Exception:
    print("Unable to connect to Postgres DB")
