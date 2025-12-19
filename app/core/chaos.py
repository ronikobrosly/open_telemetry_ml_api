import random
from app.schemas.request import ChaosConfig

class ChaosManager:
    """
    Centralized chaos injection management

    Uses pseudo-random triggers based on configured failure rates
    Each trigger is independent per request
    """

    def __init__(self):
        self.config = ChaosConfig()

    def update_config(self, new_config: ChaosConfig):
        """Update chaos configuration at runtime"""
        self.config = new_config

    def get_config(self) -> ChaosConfig:
        """Get current chaos configuration"""
        return self.config

    def should_trigger_model_failure(self) -> bool:
        """Determine if model should fail this request"""
        return random.random() < self.config.model_failure_rate

    def should_trigger_external_timeout(self) -> bool:
        """Determine if external API should timeout this request"""
        return random.random() < self.config.external_api_timeout_rate

    def should_trigger_slow_search(self) -> bool:
        """Determine if search should be slow this request"""
        return random.random() < self.config.slow_search_rate

    def should_trigger_external_failure(self) -> bool:
        """Determine if external API should fail this request"""
        return random.random() < self.config.external_api_failure_rate

# Global chaos manager instance
chaos_manager = ChaosManager()
