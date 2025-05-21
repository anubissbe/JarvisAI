import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional

from .base import BaseIntegration

logger = logging.getLogger(__name__)

class EmailIntegration(BaseIntegration):
    async def execute(self, action: str, parameters: Dict[str, Any], api_key: Optional[str] = None) -> Any:
        """Execute an email action"""
        action = action.lower()
        
        if action == "send":
            return await self._send_email(
                parameters.get("to", ""),
                parameters.get("subject", ""),
                parameters.get("body", ""),
                parameters.get("smtp_server", ""),
                parameters.get("smtp_port", 587),
                parameters.get("username", ""),
                parameters.get("password", api_key or "")
            )
        else:
            raise ValueError(f"Unknown email action: {action}")
    
    async def _send_email(
        self, 
        to: str, 
        subject: str, 
        body: str,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str
    ) -> Dict[str, Any]:
        """Send an email"""
        if not to or not subject or not body:
            return {"error": "Missing required parameters (to, subject, body)"}
        
        if not smtp_server or not username or not password:
            return {"error": "Missing SMTP configuration"}
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = username
            msg['To'] = to
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(username, password)
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            return {"status": "success", "message": "Email sent successfully"}
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return {"error": f"Failed to send email: {str(e)}"}