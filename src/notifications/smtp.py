import smtplib,sys ,os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from templates.notifacation_templates import NotificationTemplates

class SMTPNotifier:
    def __init__(self, config: dict):
        self.server = config.get('server', 'smtp.gmail.com')
        self.port = config.get('port', 587)
        self.username = config.get('username')
        self.password = config.get('password')
        self.use_tls = config.get('use_tls', True)

    def send_notification(self, 
                                program_name: str,
                                action: str,
                                from_addr: str,
                                to_addrs: List[str],
                                is_success: bool = True,
                                error_message: str = None,
                                retry_count: int = 3) -> bool:
            """Send notification using predefined templates"""
            
            if is_success:
                template = NotificationTemplates.success_template(program_name, action)
            else:
                template = NotificationTemplates.failure_template(program_name, action, error_message or "Unknown error")
            
            body = template['body'].format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            message = MIMEMultipart()
            message["Subject"] = template['subject']
            message["From"] = from_addr
            message["To"] = ", ".join(to_addrs)
            message.attach(MIMEText(body, "plain"))

            for attempt in range(retry_count):
                try:
                    with smtplib.SMTP(self.server, self.port) as server:
                        if self.use_tls:
                            server.starttls()
                        if self.username and self.password:
                            server.login(self.username, self.password)
                        server.send_message(message)
                        return True
                except Exception as e:
                    print(f"issue sending email: {e}")
                    if attempt == retry_count - 1:
                        return False
            return False
