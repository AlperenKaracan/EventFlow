from pathlib import Path

REPOSITORY_ROOT = Path(__file__).parents[3]


def test_loki_uses_tsdb_filesystem_and_seven_day_retention() -> None:
    config = (REPOSITORY_ROOT / "observability" / "loki.yaml").read_text(encoding="utf-8")

    assert "store: tsdb" in config
    assert "object_store: filesystem" in config
    assert "schema: v13" in config
    assert "retention_enabled: true" in config
    assert "delete_request_store: filesystem" in config
    assert "retention_period: ${LOKI_RETENTION_PERIOD}" in config


def test_alloy_limits_discovery_and_index_labels() -> None:
    config = (
        REPOSITORY_ROOT / "observability" / "alloy" / "config.alloy"
    ).read_text(encoding="utf-8")

    assert 'values = ["com.docker.compose.project=eventflow"]' in config
    assert 'values = ["service_name", "environment", "level", "route"]' in config
    assert "drop_malformed = false" in config
    assert 'source   = "parse_error"' in config
    assert "requestId" not in config
    assert "actorId" not in config
    assert "email" not in config
    assert config.count('sys.env("ALLOY_DOCKER_REFRESH_INTERVAL")') == 2


def test_compose_mounts_docker_socket_read_only_and_uses_named_storage() -> None:
    compose = (REPOSITORY_ROOT / "compose.yaml").read_text(encoding="utf-8")

    assert "grafana/loki:3.7.6" in compose
    assert "grafana/alloy:v1.18.1" in compose
    assert "/var/run/docker.sock:/var/run/docker.sock:ro" in compose
    assert "loki_data:/loki" in compose
    assert 'user: "473:473"' in compose
    assert "${DOCKER_SOCKET_GID:-0}" in compose
