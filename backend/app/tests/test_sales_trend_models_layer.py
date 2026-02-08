from datetime import date, timedelta


from app.dashboard_cientifico.models_layer import PracticalModels


def _make_daily_sales(totals):
    start = date(2026, 1, 1)
    out = []
    for i, total in enumerate(totals):
        out.append({"data": (start + timedelta(days=i)).strftime("%Y-%m-%d"), "total": total})
    return out


def test_detect_sales_trend_indeterminate_with_few_days():
    daily_sales = _make_daily_sales([100, 110, 90, 95, 105, 100])
    result = PracticalModels.detect_sales_trend(daily_sales)
    assert result["trend"] == "indeterminate"


def test_detect_sales_trend_outlier_does_not_flip_to_up():
    totals = [100] * 14
    totals[10] = 100000
    daily_sales = _make_daily_sales(totals)

    result = PracticalModels.detect_sales_trend(daily_sales)
    assert result["trend"] in {"stable", "indeterminate"}


def test_detect_sales_trend_detects_up_trend():
    totals = [100 + i * 2 for i in range(30)]
    daily_sales = _make_daily_sales(totals)

    result = PracticalModels.detect_sales_trend(daily_sales)
    assert result["trend"] == "up"
