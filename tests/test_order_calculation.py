from decimal import Decimal


def test_ragi_milk_order_calculation():

    price_500ml = Decimal("45.00")
    price_1litre = Decimal("72.00")

    total = (
        price_500ml * 2
        + price_1litre * 1
    )

    assert total == Decimal("162.00")


def test_multiple_500ml_bottles():

    total = Decimal("45.00") * 5

    assert total == Decimal("225.00")


def test_multiple_1litre_bottles():

    total = Decimal("72.00") * 3

    assert total == Decimal("216.00")