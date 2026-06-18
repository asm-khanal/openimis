import logging

from core.signals import bind_service_signal

logger = logging.getLogger(__name__)


def bind_service_signals():
    """
    Bind service signals for the hospital_payment module.
    Called automatically by signal_binding app during startup.
    """
    logger.debug("hospital_payment service signals bound")
