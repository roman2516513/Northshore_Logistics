import logging
import os
from datetime import datetime
import database

BASE_DIR = os.path.dirname(__file__)
LOG_DIR = os.path.join(BASE_DIR, 'logs')
LOG_PATH = os.path.join(LOG_DIR, 'app.log')

os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger('northshore')
logger.setLevel(logging.INFO)
if not logger.handlers:
    fh = logging.FileHandler(LOG_PATH)
    fmt = logging.Formatter('%(asctime)s %(levelname)s %(name)s - %(message)s')
    fh.setFormatter(fmt)
    logger.addHandler(fh)


def audit(user_id: int, role: str, action: str, details: str = '') -> None:
    ts = datetime.utcnow().isoformat()
    msg = f'user_id={user_id} role={role} action={action} details={details}'
    logger.info(msg)
    try:
        database.safe_execute(
            'INSERT INTO audit_logs (user_id, role, action, details, timestamp) VALUES (?, ?, ?, ?, ?)',
            (user_id, role, action, details, ts)
        )
    except Exception:
        logger.exception('Failed to write audit record to DB')
