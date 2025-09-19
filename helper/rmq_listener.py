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
        plc_connector=None,
        ui=None  # <<<< tambahan, referensi ke UI
    ):
        self.broker_ip = broker_ip
        self.broker_port = broker_port
        self.queues_string = queues_string
        self.username = username
        self.password = password
        self.plc_connector = plc_connector
        self.ui = ui

        self.credentials = pika.PlainCredentials(self.username, self.password)

    def log(self, message: str):
        """Kirim log ke UI kalau ada, kalau tidak fallback ke print"""
        if self.ui:
            self.ui.write_log(message)
        else:
            print(message)

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

                self.log(f"✅ Pesan terkirim ke {self.queues_string}: {message}")
                connection.close()
                return True

            except Exception as e:
                self.log(f"❌ Gagal kirim pesan RMQ: {e}")
                if not retry:
                    return False
                self.log("🔄 Coba lagi dalam 3 detik...")
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

                self.log(f"✅ Terhubung ke RabbitMQ {self.broker_ip}:{self.broker_port}, listening queue: {self.queues_string}")

                # default callback
                def callback(ch, method, properties, body):
                    try:
                        data = body.decode()
                        self.log(f"📩 Pesan diterima: {data}")

                        if handle_command:
                            success = handle_command(data, self.plc_connector, self.ui)
                            if success:
                                ch.basic_ack(delivery_tag=method.delivery_tag)
                            else:
                                self.log("⚠️ Pesan gagal diproses, tidak ack.")
                        else:
                            ch.basic_ack(delivery_tag=method.delivery_tag)

                    except Exception as e:
                        self.log(f"❌ Error saat handle message: {e}")
                        traceback.print_exc()

                channel.basic_consume(
                    queue=self.queues_string,
                    on_message_callback=callback,
                    auto_ack=False
                )

                self.log("👂 Menunggu pesan... (CTRL+C untuk stop)")
                channel.start_consuming()

            except Exception as e:
                self.log(f"❌ Listener terputus: {e}")
                traceback.print_exc()
                self.log("🔄 Reconnect dalam 3 detik...")
                time.sleep(3)
