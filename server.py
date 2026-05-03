import logging
import threading
import time
import os
import sys
from dotenv import load_dotenv

from helper.db_connection import api_check_postgres
from helper.mc_connection import PLCConnector
from helper.rmq_listener import RMQClient

# Setup basic logging for the project
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("GatewayServer")

class GatewayServer:
    def __init__(self):
        self.load_config()
        self.plc = None
        self.rmq = None
        self._running = False

    def load_config(self):
        """Loads environment variables and configuration."""
        load_dotenv()
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_port = os.getenv("DB_PORT", "5432")
        self.db_name = os.getenv("DB_NAME", "postgres")
        self.db_user = os.getenv("DB_USER", "postgres")
        self.db_password = os.getenv("DB_PASSWORD", "postgres")

        self.plc_ip = os.getenv("PLC_IP", "192.168.63.254")
        try:
            self.plc_port = int(os.getenv("PLC_PORT", "5040"))
        except ValueError:
            logger.warning("Invalid PLC_PORT in env, falling back to 5040")
            self.plc_port = 5040

        self.rmq_host = os.getenv("RMQ_HOST", "103.103.23.26")
        try:
            self.rmq_port = int(os.getenv("RMQ_PORT", "5672"))
        except ValueError:
            logger.warning("Invalid RMQ_PORT in env, falling back to 5672")
            self.rmq_port = 5672
            
        self.rmq_queue = os.getenv("RMQ_QUEUE", "junbiki_inventory_lamp_test")
        self.rmq_user = os.getenv("RMQ_USER", "ansei")
        self.rmq_pass = os.getenv("RMQ_PASS", "ansei")

    def check_database(self):
        """Checks the connection to the PostgreSQL database."""
        logger.info("Checking database connection...")
        try:
            if api_check_postgres():
                logger.info("Database connection is OK.")
            else:
                logger.error("Database connection failed. Server will continue running, but please check the database.")
        except Exception as e:
            logger.exception(f"Unexpected error while checking database: {e}")

    def setup_plc(self):
        """Initializes and connects to the PLC."""
        logger.info(f"Connecting to PLC at {self.plc_ip}:{self.plc_port}...")
        self.plc = PLCConnector(ip=self.plc_ip, port=self.plc_port)

        # Initial connection attempt
        try:
            if self.plc.connect():
                logger.info("PLC Connected successfully.")
            else:
                logger.warning("Failed to connect to PLC initially. Auto-reconnect will run in the background.")
        except Exception as e:
            logger.exception(f"Error during initial PLC connection: {e}")

        # Start PLC auto-connect thread
        plc_thread = threading.Thread(target=self.plc.auto_connect, daemon=True, name="PLC-AutoConnectThread")
        plc_thread.start()

    def setup_rmq(self):
        """Initializes and connects to the RabbitMQ listener."""
        self.rmq = RMQClient(
            broker_ip=self.rmq_host,
            broker_port=self.rmq_port,
            queues_string=self.rmq_queue,
            username=self.rmq_user,
            password=self.rmq_pass,
            plc_connector=self.plc
        )

        # Start RMQ listener thread
        rmq_thread = threading.Thread(target=self.rmq.listen, daemon=True, name="RMQ-ListenerThread")
        rmq_thread.start()
        logger.info("Server is ready and listening for messages from RMQ.")

    def run(self):
        """Main execution flow for the server."""
        logger.info("Starting Server...")
        self._running = True
        
        try:
            self.check_database()
            self.setup_plc()
            self.setup_rmq()

            # Main loop for health check / monitoring
            last_plc_state = None
            while self._running:
                time.sleep(5)
                
                # Log PLC state changes rather than spamming every 5 seconds
                current_plc_state = self.plc.connected if self.plc else False
                if current_plc_state != last_plc_state:
                    if not current_plc_state:
                        if last_plc_state is not None:
                            logger.warning("PLC connection lost. Auto-connect is attempting to reconnect...")
                        else:
                            logger.info("PLC is currently disconnected. Auto-connect is running...")
                    else:
                        if last_plc_state is not None:
                            logger.info("PLC connection restored.")
                    last_plc_state = current_plc_state
                    
        except KeyboardInterrupt:
            logger.info("Server manually stopped via KeyboardInterrupt.")
            self.shutdown()
        except Exception as e:
            logger.exception(f"Unexpected error occurred in main loop: {e}")
            self.shutdown()
            sys.exit(1)

    def shutdown(self):
        """Handles graceful shutdown procedures."""
        logger.info("Shutting down server...")
        self._running = False
        # Future enhancements: Add logic to gracefully close RMQ and PLC connections if needed.

def main():
    server = GatewayServer()
    server.run()

if __name__ == "__main__":
    main()
