from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        protected_namespaces=('settings_',)  # Fix model_ namespace conflict
    )

    # Application
    app_name: str = "Search & Recommendation Service"
    app_version: str = "1.0.0"
    environment: str = "development"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True

    # Database
    database_path: str = "app/data/search.db"

    # External API
    wikipedia_api_url: str = "https://en.wikipedia.org/api/rest_v1"
    wikipedia_timeout: float = 5.0
    wikipedia_max_retries: int = 2

    # Chaos
    chaos_model_failure_rate: float = 0.05
    chaos_external_timeout_rate: float = 0.1
    chaos_slow_search_rate: float = 0.2
    chaos_external_failure_rate: float = 0.05

    # Performance
    search_slow_threshold_ms: int = 500
    model_timeout_seconds: float = 2.0

    # Ranking
    weight_search: float = 0.5
    weight_recommendation: float = 0.3
    weight_external: float = 0.2

    # NLP
    stopwords: str = "the,a,an,and,or,but,in,on,at,to,for,of,with,by,from,as,is,was,are,were,be,been"

    # OpenTelemetry
    otel_service_name: str = "search-recommendation-service"
    otel_service_version: str = "1.0.0"
    otel_deployment_environment: str = "development"
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_exporter_otlp_protocol: str = "grpc"
    otel_traces_sampler: str = "always_on"
    otel_traces_sampler_arg: str = "1.0"
    otel_metrics_exporter: str = "otlp"
    otel_metric_export_interval: str = "60000"

    @property
    def stopwords_list(self) -> List[str]:
        return [w.strip() for w in self.stopwords.split(',')]

# Global settings instance
settings = Settings()
