pip install -e ".[dev]"# Run tests
pytest

# Start Layer 2 dashboard
python -m src.dydx_bot.dashboard.layer2_dashboard
```

## Architecture

Layer-by-layer development with 95% test coverage requirement per layer.

Currently building: **Layer 2 - dYdX v4 Client Integration**
