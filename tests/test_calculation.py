from app.calculation import Calculation

def test_calc_model():
    c = Calculation.from_values("add", 2, 3, 5)
    d = c.to_dict()
    assert d["operation"] == "add"
    assert d["a"] == 2
    assert d["b"] == 3
    assert d["result"] == 5
    assert "timestamp" in d