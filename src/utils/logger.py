import logging
import json
import sys
from datetime import datetime

class CustomFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "function": record.funcName,
            "path": record.pathname,
            "line": record.lineno
        }
        
        if hasattr(record, 'request_id'):
            log_obj['request_id'] = record.request_id
            
        if record.exc_info:
            log_obj['error'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
            
        return json.dumps(log_obj)

def setup_logger():
    logger = logging.getLogger('vercel_app')
    logger.setLevel(logging.DEBUG)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CustomFormatter())
    logger.addHandler(handler)
    
    return logger

logger = setup_logger() 