"""Metrics collector worker - generates daily reports at midnight UTC."""
from src.kafka.client import FTEKafkaConsumer, FTEKafkaProducer
from src.kafka.topics import TOPICS
from src.database.connection import get_pool, close_pool
from src.config import get_settings
import logging
import asyncio
from datetime import datetime, timedelta
import asyncpg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collect and aggregate metrics for daily reports."""

    def __init__(self) -> None:
        self._producer = FTEKafkaProducer()

    async def start(self) -> None:
        """Start the metrics collector."""
        logger.info("Starting metrics collector...")
        await get_pool()
        await self._producer.start()

    async def stop(self) -> None:
        """Stop the metrics collector."""
        logger.info("Stopping metrics collector...")
        await self._producer.stop()
        await close_pool()

    async def generate_daily_report(self, target_date: datetime = None) -> dict:
        """
        Generate daily metrics report for a specific date.

        Args:
            target_date: Date to generate report for (defaults to yesterday)

        Returns:
            Dictionary with aggregated metrics
        """
        if target_date is None:
            # Default to yesterday
            target_date = datetime.utcnow() - timedelta(days=1)
        
        target_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        logger.info(f"Generating daily report for {target_date.date()}")
        
        pool = await get_pool()
        
        try:
            async with pool.acquire() as conn:
                # Get metrics by channel
                channels = ["email", "web_form"]
                report = {
                    "date": target_date.date().isoformat(),
                    "generated_at": datetime.utcnow().isoformat(),
                    "channels": {},
                }
                
                for channel in channels:
                    # Count tickets
                    ticket_result = await conn.fetchrow(
                        """
                        SELECT 
                            COUNT(*) as total,
                            COUNT(*) FILTER (WHERE status = 'escalated') as escalations,
                            COUNT(*) FILTER (WHERE status = 'resolved') as resolved
                        FROM tickets t
                        JOIN conversations c ON c.id = t.conversation_id
                        WHERE t.source_channel = $1
                        AND DATE(t.created_at) = $2
                        """,
                        channel,
                        target_date.date(),
                    )
                    
                    # Get average sentiment
                    sentiment_result = await conn.fetchrow(
                        """
                        SELECT AVG(c.sentiment_score) as avg_sentiment
                        FROM conversations c
                        JOIN tickets t ON t.conversation_id = c.id
                        WHERE t.source_channel = $1
                        AND DATE(t.created_at) = $2
                        AND c.sentiment_score IS NOT NULL
                        """,
                        channel,
                        target_date.date(),
                    )
                    
                    # Calculate average response time
                    response_time_result = await conn.fetchrow(
                        """
                        SELECT AVG(EXTRACT(EPOCH FROM (m_out.created_at - m_in.created_at))) as avg_response_time
                        FROM tickets t
                        JOIN conversations c ON c.id = t.conversation_id
                        JOIN messages m_in ON m_in.conversation_id = c.id AND m_in.direction = 'incoming'
                        JOIN messages m_out ON m_out.conversation_id = c.id AND m_out.direction = 'outgoing'
                        WHERE t.source_channel = $1
                        AND DATE(t.created_at) = $2
                        AND m_out.created_at > m_in.created_at
                        """,
                        channel,
                        target_date.date(),
                    )
                    
                    report["channels"][channel] = {
                        "total_tickets": ticket_result["total"] or 0,
                        "escalations": ticket_result["escalations"] or 0,
                        "resolved": ticket_result["resolved"] or 0,
                        "avg_sentiment": float(sentiment_result["avg_sentiment"]) if sentiment_result["avg_sentiment"] else 0.0,
                        "avg_response_time_sec": float(response_time_result["avg_response_time"]) if response_time_result["avg_response_time"] else 0.0,
                    }
                
                # Calculate totals
                total_tickets = sum(ch["total_tickets"] for ch in report["channels"].values())
                total_escalations = sum(ch["escalations"] for ch in report["channels"].values())
                total_resolved = sum(ch["resolved"] for ch in report["channels"].values())
                
                report["summary"] = {
                    "total_tickets": total_tickets,
                    "total_escalations": total_escalations,
                    "total_resolved": total_resolved,
                    "escalation_rate": (total_escalations / total_tickets * 100) if total_tickets > 0 else 0.0,
                    "resolution_rate": (total_resolved / total_tickets * 100) if total_tickets > 0 else 0.0,
                }
                
                # Store in agent_metrics table
                await self._store_metrics(conn, report)
                
                # Publish to Kafka for notifications
                await self._producer.publish(
                    TOPICS["metrics"],
                    {
                        "type": "daily_report",
                        "report": report,
                    }
                )
                
                logger.info(f"Daily report generated: {total_tickets} tickets, {total_escalations} escalations")
                
                return report
                
        except Exception as e:
            logger.error(f"Failed to generate daily report: {e}", exc_info=True)
            raise

    async def _store_metrics(self, conn: asyncpg.Connection, report: dict) -> None:
        """Store metrics in agent_metrics table."""
        for channel, metrics in report["channels"].items():
            await conn.execute(
                """
                INSERT INTO agent_metrics (metric_name, metric_value, channel, dimensions, recorded_at)
                VALUES ($1, $2, $3, $4, $5)
                """,
                "total_tickets",
                metrics["total_tickets"],
                channel,
                {"date": report["date"]},
                report["date"],
            )
            
            await conn.execute(
                """
                INSERT INTO agent_metrics (metric_name, metric_value, channel, dimensions, recorded_at)
                VALUES ($1, $2, $3, $4, $5)
                """,
                "avg_sentiment",
                metrics["avg_sentiment"],
                channel,
                {"date": report["date"]},
                report["date"],
            )
            
            await conn.execute(
                """
                INSERT INTO agent_metrics (metric_name, metric_value, channel, dimensions, recorded_at)
                VALUES ($1, $2, $3, $4, $5)
                """,
                "escalations",
                metrics["escalations"],
                channel,
                {"date": report["date"]},
                report["date"],
            )


async def run_scheduled_collector():
    """Run metrics collector at midnight UTC daily."""
    collector = MetricsCollector()
    await collector.start()
    
    try:
        while True:
            now = datetime.utcnow()
            midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            sleep_seconds = (midnight - now).total_seconds()
            
            logger.info(f"Next daily report in {sleep_seconds:.0f} seconds")
            await asyncio.sleep(sleep_seconds)
            
            # Generate report for yesterday
            yesterday = datetime.utcnow() - timedelta(days=1)
            await collector.generate_daily_report(yesterday)
            
    except KeyboardInterrupt:
        logger.info("Shutting down metrics collector...")
    finally:
        await collector.stop()


async def main():
    """Main entry point - generate report for yesterday."""
    collector = MetricsCollector()
    await collector.start()
    
    try:
        await collector.generate_daily_report()
    finally:
        await collector.stop()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--scheduled":
        # Run continuously, generating reports at midnight
        asyncio.run(run_scheduled_collector())
    else:
        # Generate single report
        asyncio.run(main())
