"""Kafka topic name constants."""

TOPICS = {
    "tickets_incoming": "fte.tickets.incoming",
    "email_inbound": "fte.channels.email.inbound",
    "webform_inbound": "fte.channels.webform.inbound",
    "whatsapp_inbound": "fte.channels.whatsapp.inbound",
    "whatsapp_outbound": "fte.channels.whatsapp.outbound",
    "email_outbound": "fte.channels.email.outbound",
    "escalations": "fte.escalations",
    "metrics": "fte.metrics",
    "dlq": "fte.dlq",
}
