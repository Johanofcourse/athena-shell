from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-flash"

    bls_api_key: str = ""

    # For the planned FRED (FHFA House Price Index by metro) ingest, not built yet.
    fred_api_key: str = ""

    database_url: str = "sqlite:///./athena.db"

    cors_origins: str = "http://localhost:5173"

    # IPs exempt from the free daily query cap (see app/usage.py), beyond
    # loopback - e.g. Johan's own IP, so his own testing/verification
    # doesn't eat into (or get mistaken for) real visitor traffic. Set via
    # the server's own .env, never committed - a real person's IP is
    # identifying info, same handling as any other secret here.
    exempt_ips: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def exempt_ip_set(self) -> set[str]:
        return {ip.strip() for ip in self.exempt_ips.split(",") if ip.strip()}


settings = Settings()
