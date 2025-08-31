"""
Cron job functions for the order app
"""
import logging
from django.utils import timezone
from django.conf import settings
from .models import Checkout

logger = logging.getLogger(__name__)

def cleanup_expired_checkouts_job():
    """
    Cron job function to clean up expired checkouts
    This function is called automatically by django-crontab
    """
    try:
        logger.info("Starting cleanup of expired checkouts...")
        
        # Find all expired checkouts
        expired_checkouts = Checkout.objects.filter(
            is_active=True,
            expires_at__lt=timezone.now()
        )
        
        if not expired_checkouts.exists():
            logger.info("No expired checkouts found.")
            return
        
        logger.info(f"Found {expired_checkouts.count()} expired checkout(s)")
        
        # Process expired checkouts
        processed_count = 0
        for checkout in expired_checkouts:
            try:
                checkout.mark_expired()
                processed_count += 1
                logger.info(f"Processed expired checkout #{checkout.id} by {checkout.user}")
            except Exception as e:
                logger.error(f"Error processing checkout #{checkout.id}: {e}")
        
        logger.info(f"Successfully processed {processed_count} expired checkout(s)")
        
    except Exception as e:
        logger.error(f"Error in cleanup_expired_checkouts_job: {e}")
        raise
