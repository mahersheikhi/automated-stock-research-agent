import pytest

from data.universe_loader import iter_symbol_batches, load_market_universe


def test_load_market_universe_filters_normalizes_and_deduplicates(tmp_path):
    universe = tmp_path / "universe.csv"
    universe.write_text(
        "symbol,asset_type,enabled\n"
        "nvda,stock,true\n"
        "SPY,ETF,yes\n"
        "NVDA,STOCK,1\n"
        "BAD SYMBOL,STOCK,true\n"
        "MSFT,STOCK,false\n",
        encoding="utf-8",
    )

    assert load_market_universe(universe) == ["NVDA", "SPY"]
    assert load_market_universe(universe, asset_types=["ETF"]) == ["SPY"]


def test_load_market_universe_requires_expected_columns(tmp_path):
    universe = tmp_path / "universe.csv"
    universe.write_text("symbol,asset_type\nNVDA,STOCK\n", encoding="utf-8")

    with pytest.raises(ValueError, match="enabled"):
        load_market_universe(universe)


def test_iter_symbol_batches():
    assert list(iter_symbol_batches(["AAA", "BBB", "CCC"], batch_size=2)) == [
        ["AAA", "BBB"],
        ["CCC"],
    ]
