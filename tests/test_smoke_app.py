import pandas as pd

from agents.chart_selector import get_anomalies, get_col_types, render_chart


def _sample_df():
	return pd.DataFrame(
		{
			"order_id": [1, 2, 3, 4, 5, 6],
			"order_date": [
				"2026-01-01",
				"2026-01-02",
				"2026-01-03",
				"2026-01-04",
				"2026-01-05",
				"2026-01-06",
			],
			"region": ["North", "South", "North", "West", "South", "West"],
			"sales": [100, 140, 180, 210, 260, 300],
			"profit": [20, 25, 32, 40, 50, 62],
			"cost": [80, 115, 148, 170, 210, 238],
		}
	)


def test_get_col_types_smoke():
	df = _sample_df()
	numeric, categorical, date_cols = get_col_types(df)

	assert "sales" in numeric
	assert "profit" in numeric
	assert "region" in categorical
	assert "order_date" in date_cols


def test_render_chart_bar_smoke():
	df = _sample_df()
	spec = {
		"chart_type": "bar",
		"x": "region",
		"y": "sales",
		"color": None,
		"agg": "sum",
		"title": "Sales by Region",
		"reason": "Category comparison",
	}
	result = render_chart(df, spec)

	assert result is not None
	assert "fig" in result
	assert result["title"] == "Sales by Region"


def test_get_anomalies_returns_list():
	# Profit and returns are intentionally negatively correlated.
	df = pd.DataFrame(
		{
			"profit": [100, 90, 80, 70, 60, 50],
			"returns": [5, 8, 12, 16, 20, 24],
			"volume": [10, 11, 12, 13, 14, 15],
		}
	)
	anomalies = get_anomalies(df)

	assert isinstance(anomalies, list)
	assert any(
		{"profit", "returns"} == {a[0], a[1]} for a in anomalies
	)
