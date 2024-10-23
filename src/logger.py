import logging

def init_logger():
    # Configure the logger
    global logger
    logging.basicConfig(
        level=logging.DEBUG,  # Set the minimum level of messages to log
        format='%(asctime)s - %(levelname)s - %(message)s',  # Customize the log message format
        handlers=[
            logging.FileHandler("app.log", mode='w'),  # Log messages to a file
        ]
    )
    
logger = logging.getLogger(__name__)