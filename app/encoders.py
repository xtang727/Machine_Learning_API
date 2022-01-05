from json import encoder
import numpy as np
import json

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

def encode_to_json(data, as_py=True):
    encoded = json.dumps(data, cls=NumpyEncoder)
    if as_py:
        return json.loads(encoded)
    return encoded