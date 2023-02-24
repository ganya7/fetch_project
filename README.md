README

Prerequisites:

Download and install Docker
Download the provided Docker images for the test data: Postgres and Localstack
Install the PostgresSQL
Postgres creds: 
    database: postgres
    username: postgres
    password: postgres
Pip install awslocal, awscli

or install the packages from the requirements.txt file by running the following in terminal: 
`pip install -r requirements.txt`


Steps To run the Python script:

1. Git clone this repo into a folder `fetch_project` and in terminal `cd ./fetch_project`
2. Run `pip install -r requirements.txt`
3. Configure aws profile if not previously:
In terminal `aws configure --profile default`
```
AWS Access Key ID [None]: test
AWS Secret Access Key [None]: test
Default region name [None]: us-west-1
Default output format [None]: text
```
4. Run `docker compose up` to start the Postgres DB and the localstack AWS SQS service
5. Run the python script in a terminal with `python3 etl_process.py`

Driving decisions:

1. How will you read messages from the queue?

The messages are read from the SQS queue one at a time. They are processed as
a JSON string and the masked fields are hashed using SHA256 algorithm to mask
the PII data. Once the current queue messages have been processed they are written to 
the Postgres database. The messages should be deleted from the SQS queue once processed.


2. What type of data structures should be used?

Python dictionary is a data structure that would be appropriate in this scenario as it 
deals with JSON data which is of the key-value pair structure. This data structure is the 
closest to resemble the tabular relation of the database format as well.

3. How will you mask the PII data so that duplicate values can be identified?

The PII data is encrypted using SHA256 function and then stored in the Postgres database.
The hash value enables in identifying the data and find duplicate as the hash value will 
be same for the same input value. This hashed value is the table will mask the PII and at 
the same time can be used to deduplicate the database.

4. What will be your strategy for connecting and writing to Postgres?

Processing a batch of data and transforming and then performing a bulk insert into 
Postgres database is an efficient way. It would be an expensive operation to insert a 
data record as soon as its processed and to be written into the database as it involves 
connecting to the database in a repeating fashion, resulting in poor application performance. 
