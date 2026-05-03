import traceback
import pika
import time
import logging
from tools.handler_message import handle_command

logger = logging.getLogger(__name__)

class RMQClient:
    def __init__(
        self,
        broker_ip=None,
        broker_port=None,
        queues_string=None,
        username=None,
        password=None,
        plc_connector=None
    ):
        self.broker_ip = broker_ip
        self.broker_port = broker_port
        self.queues_string = queues_string
        self.username = username
        self.password = password
        self.plc_connector = plc_connector

        self.credentials = pika.PlainCredentials(self.username, self.password)

    def send(self, message, retry=True):
        """Kirim pesan ke RabbitMQ, auto-reconnect kalau gagal"""
        while True:
            try:
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=self.broker_ip,
                        port=self.broker_port,
                        credentials=self.credentials
                    )
                )
                channel = connection.channel()
                channel.queue_declare(queue=self.queues_string, durable=True)

                channel.basic_publish(
                    exchange="",
                    routing_key=self.queues_string,
                    body=str(message).encode(),
                    properties=pika.BasicProperties(delivery_mode=2)  # persistent
                )

                logger.info(f"Pesan terkirim ke {self.queues_string}: {message}")
                connection.close()
                return True

            except Exception as e:
                logger.error(f"Gagal kirim pesan RMQ: {e}")
                if not retry:
                    return False
                logger.info("Coba lagi dalam 3 detik...")
                time.sleep(3)

    def listen(self):
        """Listen pesan dari RabbitMQ, auto-reconnect kalau terputus"""
        while True:
            try:
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=self.broker_ip,
                        port=self.broker_port,
                        credentials=self.credentials,
                        heartbeat=60,
                        blocked_connection_timeout=300
                    )
                )
                channel = connection.channel()
                channel.queue_declare(queue=self.queues_string, durable=True)

                logger.info(f"Terhubung ke RabbitMQ {self.broker_ip}:{self.broker_port}, listening queue: {self.queues_string}")

                # default callback
                def callback(ch, method, properties, body):
                    try:
                        data = body.decode()
                        logger.debug(f"Pesan diterima: {data}")

                        if handle_command:
                            success = handle_command(data, self.plc_connector)  # <<<< panggil dengan PLC
                            if success:
                                ch.basic_ack(delivery_tag=method.delivery_tag)
                            else:
                                logger.warning("Pesan gagal diproses, tidak ack.")
                        else:
                            ch.basic_ack(delivery_tag=method.delivery_tag)

                    except Exception as e:
                        logger.exception(f"Error saat handle message: {e}")

                channel.basic_consume(
                    queue=self.queues_string,
                    on_message_callback=callback,
                    auto_ack=False
                )

                logger.info("Menunggu pesan... (CTRL+C untuk stop)")
                channel.start_consuming()

            except Exception as e:
                logger.exception(f"Listener terputus: {e}")
                logger.info("Reconnect dalam 3 detik...")
                time.sleep(3)
