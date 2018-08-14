import pacu
from utils import get_database_connection, set_sigint_handler
from core.base import Base
from core.models import AWSKey, PacuSession, ProxySettings

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from pathlib import Path
import importlib
import os



import boto3
from moto import mock_s3


pacu_instance = pacu.Main()

@mock_s3
def test_run_s3():
	
	# SETUP
    conn = boto3.resource('s3', region_name='us-east-1')
    bucket_name = 'my-bucket'
    conn.create_bucket(Bucket=bucket_name)    
    conn.Bucket(bucket_name).put_object(Key='test.txt', Body=b'test')

    module = importlib.import_module('modules.s3_bucket_dump.main')
    pacu_instance.exec_module(['run' , 's3_bucket_dump', '--names-only'])

    #ASSERTS
    # Need to make sure the file test.txt can be found
    bucket_file = Path(Path.cwd(), 'sessions', 'TestSession', 'downloads', 's3_bucket_dump', 's3_bucket_dump_file_names.txt')
    with bucket_file.open() as open_file:
        data = open_file.read()
        assert bucket_name in data
    return True

def setup():
    if Path('test.db').exists():
        os.remove('test.db')

    assert not Path('test').exists()

    engine = create_engine('sqlite:///test.db', echo=False)	
    Base.metadata.create_all(engine)
    Base.metadata.bind = engine
    pacu_instance.database = sessionmaker(bind=engine)()

    init_session()
    # pacu_instance.set_keys()

    if test_run_s3():
        print('Test Successful!')


def init_session():
	session_data = {
		'id': 1,
		'name':'TestSession',
		'is_active':True,
		'access_key_id':'test',
		'secret_access_key':'test',
		
	}
	session = PacuSession(**session_data)
	pacu_instance.database.add(session)
	
	session_downloads_directory = './sessions/{}/downloads/'.format('TestSession')
	if not os.path.exists(session_downloads_directory):
		os.makedirs(session_downloads_directory)
	
	# pacu_instance.database.query(PacuSession).one().activate(pacu_instance.database)
	
	proxy_data = {
		'id':1,
	}
	proxy = ProxySettings(**proxy_data)
	pacu_instance.database.add(proxy)
	
	key_data = {
		'id':1,
		'access_key_id':'test',
		'secret_access_key':'test'
	}
	awskey = AWSKey(**key_data)
	pacu_instance.database.add(awskey)
	
	pacu_instance.database.commit()
	

def cleanup():
	#clean up temp directory
	#clean up database
	return True
	

if __name__ == '__main__':
    setup()