import traceback

import pika
import time
from tools.handler_message import handle_command


class RMQClient:
    def __init__(
        self,
        broker_ip="10.10.10.10",
        broker_port=5672,
        queues_string="junbiki_inventory_lamp_test",
        username="ansei",
        password="ansei",
        plc_connector=None  # <<<< tambahan untuk PLC
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

                print(f"✅ Pesan terkirim ke {self.queues_string}: {message}")
                connection.close()
                return True

            except Exception as e:
                print(f"❌ Gagal kirim pesan RMQ: {e}")
                if not retry:
                    return False
                print("🔄 Coba lagi dalam 3 detik...")
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

                print(f"✅ Terhubung ke RabbitMQ {self.broker_ip}:{self.broker_port}, listening queue: {self.queues_string}")

                # default callback
                def callback(ch, method, properties, body):
                    try:
                        data = body.decode()
                        print(f"📩 Pesan diterima: {data}")

                        if handle_command:
                            success = handle_command(data, self.plc_connector)  # <<<< panggil dengan PLC
                            if success:
                                ch.basic_ack(delivery_tag=method.delivery_tag)
                            else:
                                print("⚠️ Pesan gagal diproses, tidak ack.")
                        else:
                            ch.basic_ack(delivery_tag=method.delivery_tag)

                    except Exception as e:
                        print(f"❌ Error saat handle message: {e}")

                channel.basic_consume(
                    queue=self.queues_string,
                    on_message_callback=callback,
                    auto_ack=False
                )

                print("👂 Menunggu pesan... (CTRL+C untuk stop)")
                channel.start_consuming()

            except Exception as e:
                print(f"❌ Listener terputus: {e}")
                traceback.print_exc()  # <--- ini buat print full stacktrace
                print("🔄 Reconnect dalam 3 detik...")
                time.sleep(3)
