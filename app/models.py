import uuid
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model

class SMSInference(Model):
    __keyspace__ = 'ml_api'
    uuid = columns.UUID(primary_key=True, default=uuid.uuid1)
    query = columns.Text()
    label = columns.Text()
    confidence = columns.Float()