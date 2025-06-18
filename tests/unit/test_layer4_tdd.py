"""
Layer 4 Signal Types - STRICT TDD
Starting with ONE test function only.
"""

import pytest
from enum import Enum


class TestSignalType:
    """Test SignalType enum with STRICT TDD - ONE test at a time."""
    
    def test_signal_type_has_momentum(self):
        """RED: Test that SignalType has MOMENTUM value."""
        # This test will fail because SignalType doesn't exist yet
        from src.dydx_bot.signals.types import SignalType
        
        assert SignalType.MOMENTUM == "momentum"
    
    def test_signal_type_has_volume(self):
        """RED: Test that SignalType has VOLUME value."""
        from src.dydx_bot.signals.types import SignalType
        
        assert SignalType.VOLUME == "volume"
    
    def test_signal_type_has_volatility(self):
        """RED: Test that SignalType has VOLATILITY value."""
        from src.dydx_bot.signals.types import SignalType
        
        assert SignalType.VOLATILITY == "volatility"
    
    def test_signal_type_has_orderbook(self):
        """RED: Test that SignalType has ORDERBOOK value."""
        from src.dydx_bot.signals.types import SignalType
        
        assert SignalType.ORDERBOOK == "orderbook"


class TestSignalSet:
    """Test SignalSet dataclass for holding multiple signal scores per market."""
    
    def test_signal_set_creation_with_valid_scores(self):
        """Test creating SignalSet with valid signal scores (0-100)."""
        from datetime import datetime
        from src.dydx_bot.signals.types import SignalSet
        
        # Create SignalSet with valid scores
        signal_set = SignalSet(
            market="BTC-USD",
            momentum=75.0,
            volume=80.0,
            volatility=65.0,
            orderbook=85.0,
            timestamp=datetime.now(),
            metadata={}
        )
        
        # Verify all attributes are set correctly
        assert signal_set.market == "BTC-USD"
        assert signal_set.momentum == 75.0
        assert signal_set.volume == 80.0
        assert signal_set.volatility == 65.0
        assert signal_set.orderbook == 85.0
        assert isinstance(signal_set.timestamp, datetime)
        assert signal_set.metadata == {}

    def test_signal_set_validates_score_range(self):
        """Test that SignalSet validates scores are within 0-100 range."""
        from datetime import datetime
        from src.dydx_bot.signals.types import SignalSet
        
        # Test score > 100 raises ValueError
        with pytest.raises(ValueError, match="Signal scores must be between 0 and 100"):
            SignalSet(
                market="BTC-USD",
                momentum=150.0,  # Invalid score > 100
                volume=80.0,
                volatility=65.0,
                orderbook=85.0,
                timestamp=datetime.now(),
                metadata={}
            )
    
    def test_signal_set_validates_negative_scores(self):
        """Test that SignalSet validates scores are not negative."""
        from datetime import datetime
        from src.dydx_bot.signals.types import SignalSet
        
        # Test negative score raises ValueError
        with pytest.raises(ValueError, match="Signal scores must be between 0 and 100"):
            SignalSet(
                market="BTC-USD",
                momentum=75.0,
                volume=-10.0,  # Invalid negative score
                volatility=65.0,
                orderbook=85.0,
                timestamp=datetime.now(),
                metadata={}
            )


class TestSignalEngine:
    """Test SignalEngine base class - STRICT TDD ONE test at a time."""
    
    def test_signal_engine_has_signal_type_property(self):
        """Test that SignalEngine has a signal_type property."""
        from src.dydx_bot.signals.engine import SignalEngine
        from src.dydx_bot.signals.types import SignalType
        
        # Create a concrete engine (momentum for example)
        engine = SignalEngine(signal_type=SignalType.MOMENTUM)
        
        # Verify it has the signal_type property
        assert engine.signal_type == SignalType.MOMENTUM
    
    def test_signal_engine_can_calculate_signal_score(self):
        """Test that SignalEngine can calculate signal score for market data."""
        from src.dydx_bot.signals.engine import SignalEngine
        from src.dydx_bot.signals.types import SignalType
        
        # Create momentum engine
        engine = SignalEngine(signal_type=SignalType.MOMENTUM)
        
        # Mock market data (simplified for this test)
        market_data = {
            "symbol": "BTC-USD",
            "price": 50000.0,
            "volume": 1000.0
        }
        
        # Calculate signal score
        score = engine.calculate_signal(market_data)
        
        # Verify score is valid (0-100 range)
        assert isinstance(score, float)
        assert 0 <= score <= 100


class TestMomentumEngine:
    """Test MomentumEngine for momentum signal calculation."""
    
    def test_momentum_engine_creation(self):
        """Test creating MomentumEngine with correct signal type."""
        from src.dydx_bot.signals.engine import MomentumEngine
        from src.dydx_bot.signals.types import SignalType
        
        # Create momentum engine
        engine = MomentumEngine()
        
        # Verify it has correct signal type
        assert engine.signal_type == SignalType.MOMENTUM


class TestVolumeEngine:
    """Test VolumeEngine for volume signal calculation."""
    
    def test_volume_engine_creation(self):
        """Test creating VolumeEngine with correct signal type."""
        from src.dydx_bot.signals.engine import VolumeEngine
        from src.dydx_bot.signals.types import SignalType
        
        # Create volume engine
        engine = VolumeEngine()
        
        # Verify it has correct signal type
        assert engine.signal_type == SignalType.VOLUME


class TestVolatilityEngine:
    """Test VolatilityEngine for volatility signal calculation."""
    
    def test_volatility_engine_creation(self):
        """Test creating VolatilityEngine with correct signal type."""
        from src.dydx_bot.signals.engine import VolatilityEngine
        from src.dydx_bot.signals.types import SignalType
        
        # Create volatility engine
        engine = VolatilityEngine()
        
        # Verify it has correct signal type
        assert engine.signal_type == SignalType.VOLATILITY


class TestOrderbookEngine:
    """Test OrderbookEngine for orderbook signal calculation."""
    
    def test_orderbook_engine_creation(self):
        """Test creating OrderbookEngine with correct signal type."""
        from src.dydx_bot.signals.engine import OrderbookEngine
        from src.dydx_bot.signals.types import SignalType
        
        # Create orderbook engine
        engine = OrderbookEngine()
        
        # Verify it has correct signal type
        assert engine.signal_type == SignalType.ORDERBOOK


class TestMomentumCalculation:
    """Test MomentumEngine signal calculation logic."""
    
    def test_momentum_engine_calculates_simple_price_momentum(self):
        """Test momentum calculation based on price change."""
        from src.dydx_bot.signals.engine import MomentumEngine

        # Create momentum engine
        engine = MomentumEngine()

        # Mock market data with real dYdX format (positive price movement)
        market_data = {
            "price": 50000.0,
            "price_change_24h": 2000.0,  # $2000 increase
            "volume_24h": 1000000.0,
            "bid_price": 49990.0,
            "ask_price": 50010.0,
            "bid_size": 1.5,
            "ask_size": 2.0,
            "trades_count": 5000,
            "volatility": 0.025
        }

        # Calculate signal score
        score = engine.calculate_signal(market_data)

        # Verify score is above 50 for positive momentum (4% increase = +8 points)
        assert isinstance(score, float)
        assert 0.0 <= score <= 100.0
        assert score > 55.0  # Should be around 58 (50 + 4*2)


class TestVolumeCalculation:
    """Test VolumeEngine signal calculation logic."""
    
    def test_volume_engine_calculates_signal(self):
        """Test volume calculation based on relative volume."""
        from src.dydx_bot.signals.engine import VolumeEngine

        # Create volume engine
        engine = VolumeEngine()

        # Mock market data with real dYdX format (high volume)
        market_data = {
            "price": 50000.0,
            "price_change_24h": 500.0,
            "volume_24h": 5000000.0,  # High volume
            "bid_price": 49990.0,
            "ask_price": 50010.0,
            "bid_size": 1.5,
            "ask_size": 2.0,
            "trades_count": 10000,  # High trade count
            "volatility": 0.025
        }

        # Calculate signal score
        score = engine.calculate_signal(market_data)

        # Verify score is reasonable for high volume
        assert isinstance(score, float)
        assert 0.0 <= score <= 100.0
        assert score > 70.0  # High volume should result in high score


class TestVolatilityCalculation:
    """Test VolatilityEngine signal calculation logic."""
    
    def test_volatility_engine_calculates_volatility_signal(self):
        """Test volatility calculation based on price volatility metrics."""
        from src.dydx_bot.signals.engine import VolatilityEngine

        # Create volatility engine
        engine = VolatilityEngine()

        # Mock market data with real dYdX format (high volatility)
        market_data = {
            "price": 50000.0,
            "price_change_24h": 1000.0,
            "volume_24h": 2000000.0,
            "bid_price": 49900.0,  # Wide spread indicating volatility
            "ask_price": 50100.0,
            "bid_size": 1.0,
            "ask_size": 1.0,
            "trades_count": 8000,
            "volatility": 0.05  # Higher volatility value
        }

        # Calculate signal score
        score = engine.calculate_signal(market_data)

        # Verify score reflects high volatility
        assert isinstance(score, float)
        assert 0.0 <= score <= 100.0
        assert score > 80.0  # High volatility should result in high score


class TestOrderbookCalculation:
    """Test OrderbookEngine signal calculation logic."""
    
    def test_orderbook_engine_calculates_orderbook_signal(self):
        """Test orderbook calculation based on bid-ask spread and depth."""
        from src.dydx_bot.signals.engine import OrderbookEngine

        # Create orderbook engine
        engine = OrderbookEngine()

        # Mock market data with real dYdX format (buy-heavy orderbook)
        market_data = {
            "price": 50000.0,
            "price_change_24h": 200.0,
            "volume_24h": 1500000.0,
            "bid_price": 49995.0,
            "ask_price": 50005.0,
            "bid_size": 3.0,  # More bids than asks
            "ask_size": 1.0,
            "trades_count": 6000,
            "volatility": 0.025
        }

        # Calculate signal score
        score = engine.calculate_signal(market_data)

        # Verify score reflects buy-heavy orderbook (3/(3+1) = 0.75 = 75%)
        assert isinstance(score, float)
        assert 0.0 <= score <= 100.0
        assert score > 70.0  # Buy-heavy orderbook should be > 70


class TestSignalManager:
    """Test SignalManager for coordinating all signal engines."""
    
    def test_signal_manager_creation(self):
        """Test creating SignalManager with all engines."""
        from src.dydx_bot.signals.manager import SignalManager
        
        # Create signal manager
        manager = SignalManager()
        
        # Verify it has all required engines
        assert hasattr(manager, 'momentum_engine')
        assert hasattr(manager, 'volume_engine')
        assert hasattr(manager, 'volatility_engine')
        assert hasattr(manager, 'orderbook_engine')
    
    def test_signal_manager_calculates_complete_signal_set(self):
        """Test SignalManager can calculate complete SignalSet for a market."""
        from src.dydx_bot.signals.manager import SignalManager
        from src.dydx_bot.signals.types import SignalSet
        from datetime import datetime
        
        # Create signal manager
        manager = SignalManager()
        
        # Mock comprehensive market data
        market_data = {
            "symbol": "BTC-USD",
            "price_change_percent": 3.0,  # For momentum
            "volume_ratio": 1.2,          # For volume
            "volatility_percentile": 75.0, # For volatility
            "order_book_imbalance": 0.6    # For orderbook
        }
        
        # Calculate complete signal set
        signal_set = manager.calculate_signals("BTC-USD", market_data)
        
        # Verify it returns a SignalSet instance
        assert isinstance(signal_set, SignalSet)
        assert signal_set.market == "BTC-USD"
        assert isinstance(signal_set.timestamp, datetime)
        
        # Verify all signal scores are calculated and in valid range
        assert 0.0 <= signal_set.momentum <= 100.0
        assert 0.0 <= signal_set.volume <= 100.0
        assert 0.0 <= signal_set.volatility <= 100.0
        assert 0.0 <= signal_set.orderbook <= 100.0


class TestSignalManager:
    """Test SignalManager aggregation and publishing logic with STRICT TDD."""

    def test_signal_manager_aggregates_and_publishes_signals(self):
        """RED: Test that SignalManager aggregates signals and publishes a SignalSet."""
        from src.dydx_bot.signals.manager import SignalManager
        from src.dydx_bot.signals.types import SignalSet

        # Create SignalManager instance
        manager = SignalManager()

        # Mock input data for all signal engines
        mock_data = {
            "momentum": {"price_change_percent": 0.02},
            "volume": {"volume_ratio": 1.5},
            "volatility": {"volatility_percentile": 70.0},
            "orderbook": {"order_book_imbalance": 0.6},
        }

        # Aggregate and publish signals
        signal_set = manager.aggregate_and_publish(mock_data)

        # Assert SignalSet is correctly created
        assert isinstance(signal_set, SignalSet)
        assert 0 <= signal_set.momentum <= 100
        assert 0 <= signal_set.volume <= 100
        assert 0 <= signal_set.volatility <= 100
        assert 0 <= signal_set.orderbook <= 100


class TestVolatilityEngine:
    """Test VolatilityEngine calculation logic with STRICT TDD."""

    def test_volatility_engine_calculates_signal(self):
        """RED: Test that VolatilityEngine calculates a valid signal."""
        from src.dydx_bot.signals.engine import VolatilityEngine

        # Create a VolatilityEngine instance
        engine = VolatilityEngine()

        # Mock input data for calculation
        mock_data = {
            "price_changes": [0.01, -0.02, 0.03, -0.01, 0.02],
        }

        # Calculate signal
        signal = engine.calculate_signal(mock_data)

        # Assert signal is within valid range
        assert 0 <= signal <= 100


class TestOrderbookEngine:
    """Test OrderbookEngine calculation logic with STRICT TDD."""

    def test_orderbook_engine_calculates_signal(self):
        """RED: Test that OrderbookEngine calculates a valid signal."""
        from src.dydx_bot.signals.engine import OrderbookEngine

        # Create an OrderbookEngine instance
        engine = OrderbookEngine()

        # Mock input data for calculation
        mock_data = {
            "orderbook": {
                "bids": [100, 200, 300],
                "asks": [150, 250, 350],
            }
        }

        # Calculate signal
        signal = engine.calculate_signal(mock_data)

        # Assert signal is within valid range
        assert 0 <= signal <= 100


class TestConnectionManager:
    """Test ConnectionManager integration with STRICT TDD."""

    def test_connection_manager_singleton(self):
        """RED: Test that ConnectionManager is a singleton shared across signal engines."""
        from src.dydx_bot.signals.connection_manager import ConnectionManager
        from src.dydx_bot.signals.engine import MomentumEngine, VolumeEngine

        # Get ConnectionManager instance
        connection_manager_1 = ConnectionManager.get_instance()
        connection_manager_2 = ConnectionManager.get_instance()

        # Assert both instances are the same
        assert connection_manager_1 is connection_manager_2

        # Verify integration with signal engines
        momentum_engine = MomentumEngine()
        volume_engine = VolumeEngine()

        assert momentum_engine.connection_manager is connection_manager_1
        assert volume_engine.connection_manager is connection_manager_1

    def test_connection_manager_connect_method(self):
        """RED: Test that ConnectionManager connect method establishes connection."""
        from src.dydx_bot.signals.connection_manager import ConnectionManager

        # Get ConnectionManager instance
        manager = ConnectionManager.get_instance()

        # Test connect method
        manager.connect()

        # Assert connection was established
        assert manager.connection == "WebSocket Connection Established"

    def test_connection_manager_disconnect_method(self):
        """RED: Test that ConnectionManager disconnect method closes connection."""
        from src.dydx_bot.signals.connection_manager import ConnectionManager

        # Get ConnectionManager instance
        manager = ConnectionManager.get_instance()

        # Establish connection first
        manager.connect()
        assert manager.connection is not None

        # Test disconnect method
        manager.disconnect()

        # Assert connection was closed
        assert manager.connection is None

    def test_connection_manager_singleton_exception(self):
        """RED: Test that ConnectionManager raises exception when trying to create second instance."""
        from src.dydx_bot.signals.connection_manager import ConnectionManager

        # Get the singleton instance (should already exist from other tests)
        first_instance = ConnectionManager.get_instance()

        # Try to create another instance directly - should raise exception
        with pytest.raises(Exception, match="This class is a singleton!"):
            ConnectionManager()

        # Verify the singleton instance still works
        assert first_instance is ConnectionManager.get_instance()


class TestSignalManagerIntegration:
    """Test SignalManager integration with ConnectionManager."""

    def test_signal_manager_uses_connection_manager(self):
        """RED: Test that SignalManager uses ConnectionManager for WebSocket connection."""
        from src.dydx_bot.signals.manager import SignalManager
        from src.dydx_bot.signals.connection_manager import ConnectionManager

        # Create SignalManager instance
        manager = SignalManager()

        # Get ConnectionManager instance
        connection_manager = ConnectionManager.get_instance()

        # Assert SignalManager uses the same ConnectionManager instance
        assert manager.momentum_engine.connection_manager is connection_manager
        assert manager.volume_engine.connection_manager is connection_manager
        assert manager.volatility_engine.connection_manager is connection_manager
        assert manager.orderbook_engine.connection_manager is connection_manager

        # Verify WebSocket connection establishment
        connection_manager.connect()
        assert connection_manager.connection == "WebSocket Connection Established"

        # Verify WebSocket connection closure
        connection_manager.disconnect()
        assert connection_manager.connection is None


class TestSignalManager:
    """Test SignalManager aggregation and publishing logic with STRICT TDD."""

    def test_signal_manager_aggregates_and_publishes_signals(self):
        """RED: Test that SignalManager aggregates signals and publishes a SignalSet."""
        from src.dydx_bot.signals.manager import SignalManager
        from src.dydx_bot.signals.types import SignalSet

        # Create SignalManager instance
        manager = SignalManager()

        # Mock input data for all signal engines
        mock_data = {
            "momentum": {"price_change_percent": 0.02},
            "volume": {"volume_ratio": 1.5},
            "volatility": {"volatility_percentile": 70.0},
            "orderbook": {"order_book_imbalance": 0.6},
        }

        # Aggregate and publish signals
        signal_set = manager.aggregate_and_publish(mock_data)

        # Assert SignalSet is correctly created
        assert isinstance(signal_set, SignalSet)
        assert 0 <= signal_set.momentum <= 100
        assert 0 <= signal_set.volume <= 100
        assert 0 <= signal_set.volatility <= 100
        assert 0 <= signal_set.orderbook <= 100

    def test_signal_manager_calculate_signals_method(self):
        """RED: Test that SignalManager calculate_signals method works correctly."""
        from src.dydx_bot.signals.manager import SignalManager
        from src.dydx_bot.signals.types import SignalSet

        # Create SignalManager instance
        manager = SignalManager()

        # Mock input data for signal calculation
        mock_data = {
            "price_change_percent": 0.02,
            "volume_ratio": 1.5,
            "volatility_percentile": 70.0,
            "order_book_imbalance": 0.6,
        }

        # Calculate signals using the calculate_signals method
        signal_set = manager.calculate_signals("BTC-USD", mock_data)

        # Assert SignalSet is correctly created
        assert isinstance(signal_set, SignalSet)
        assert signal_set.market == "BTC-USD"
        assert 0 <= signal_set.momentum <= 100
        assert 0 <= signal_set.volume <= 100
        assert 0 <= signal_set.volatility <= 100
        assert 0 <= signal_set.orderbook <= 100
