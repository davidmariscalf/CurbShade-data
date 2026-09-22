from curbshade_data.osm import first, number


def test_first_normalizes_scalar_and_list_values():
    assert first("asphalt") == "asphalt"
    assert first(["asphalt", "gravel"]) == "asphalt"
    assert first([]) is None


def test_number_rejects_non_finite_and_parses_percentages():
    assert number("12%") == 12.0
    assert number(["1.5"]) == 1.5
    assert number("nan") is None
    assert number("inf") is None
    assert number("not-a-number") is None
