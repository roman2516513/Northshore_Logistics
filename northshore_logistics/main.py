import os
import logging
import database
import seed_data
import gui

BASE_DIR = os.path.dirname(__file__)
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, filename=os.path.join(LOGS_DIR, 'app.log'),
                    format='%(asctime)s %(levelname)s %(name)s - %(message)s')
logger = logging.getLogger('northshore.main')


def main():
    try:
        database.initialise_database()
        seed_data.seed_if_empty()
        gui.launch()
    except Exception as e:
        logger.exception('Application failed to start: %s', e)


if __name__ == '__main__':
    main()
