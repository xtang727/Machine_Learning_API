import pathlib
from typing import Optional
from fastapi import FastAPI
from fastapi.params import Query
from fastapi.responses import StreamingResponse
from cassandra.query import SimpleStatement
from cassandra.cqlengine.management import sync_table

from . import (config, db, models, ml, schema)

app = FastAPI()
settings = config.get_settings()

BASE_DIR = pathlib.Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR.parent / 'models'
SMS_SPAM_MODEL_DIR = MODEL_DIR / 'spam-sms'
MODEL_PATH = SMS_SPAM_MODEL_DIR / 'spam-model.h5'
TOKENIZER_PATH = SMS_SPAM_MODEL_DIR / 'spam-classifer-tokenizer.json'
METADATA_PATH = SMS_SPAM_MODEL_DIR / 'spam-classifer-metadata.json'

ML_MODEL = None
DB_SESSION = None
SMSInference = models.SMSInference

@app.on_event('startup')
def on_startup():
    global ML_MODEL, DB_SESSION
    ML_MODEL = ml.MLModel(
        model_path = MODEL_PATH,
        tokenizer_path = TOKENIZER_PATH,
        metadata_path = METADATA_PATH
        )
    DB_SESSION = db.get_session()
    sync_table(SMSInference)
        
@app.get('/')
def read_index(q:Optional[str]=None):
    return {'Hello': 'world'}

@app.post('/')
def create_inference(query:schema.Query):
    global ML_MODEL
    preds_dict = ML_MODEL.predict_text(query.q)
    top = preds_dict.get('top')
    data = {'query': query.q, **top}
    obj = SMSInference.objects.create(**data)
    return obj

@app.get('/inferences')
def list_inference():
    q = SMSInference.objects.all()
    return list(q)

@app.get('/inferences/{my_uuid}')
def read_inference(my_uuid):
    obj = SMSInference.objects.get(uuid=my_uuid)
    return obj

def fetch_rows(stmt:SimpleStatement, fetch_size:int = 5, session=None):
    stmt.fetch_size = fetch_size
    result_set = session.execute(stmt)
    has_pages = result_set.has_more_pages
    yield 'uuid,label,confidence,query\n'
    while has_pages:
        for row in result_set.current_rows:
            yield f"{row['uuid']}, {row['label']}, {row['confidence']}, {row['query']}\n"
        has_pages = result_set.has_more_pages
        result_set = session.execute(stmt, paging_state=result_set.paging_state)

@app.get('/dataset')
def export_inference():
    global DB_SESSION
    cql_query = 'SELECT * FROM ml_api.smsinference LIMIT 10000'
    statement = SimpleStatement(cql_query)
    # rows = DB_SESSION.execute(cql_query)
    return StreamingResponse(fetch_rows(statement, 5, DB_SESSION))