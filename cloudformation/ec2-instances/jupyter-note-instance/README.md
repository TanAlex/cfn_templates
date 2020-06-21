stacker build -r us-east-2 ./main.env ./main.yaml


/home/ubuntu/anaconda3/envs/python3/bin/python /home/ubuntu/anaconda3/envs/python3/bin/jupyter-notebook --ip 0.0.0.0 --port 8888

git clone https://github.com/awslabs/aws-data-wrangler.git

aws configure set region us-east-2 --profile default

boto3.setup_default_session(region_name="us-east-2")


import awswrangler as wr
import pandas as pd

df = pd.DataFrame({"id": [1, 2], "value": ["foo", "boo"]})
wr.catalog.create_database("my_db")
# Storing data on Data Lake
wr.s3.to_parquet(
    df=df,
    path="s3://lab-test-bucket-01/dataset/",
    dataset=True,
    database="my_db",
    table="my_table"
)