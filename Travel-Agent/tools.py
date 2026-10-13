import uuid

# ---------------------------------------------------------------------------
# MOCK DATA (swap these for real services later)
# ---------------------------------------------------------------------------
CURRENCY = "INR"

# Dates with no flights, so we can test re-planning.
SOLD_OUT_DATES = {"2026-12-25"}

MOCK_FLIGHTS = {
    "goa": [
        {"airline": "IndiGo", "flight_no": "6E-201", "depart": "06:15", "price": 4500},
        {"airline": "Air India", "flight_no": "AI-681", "depart": "09:40", "price": 5800},
        {"airline": "Akasa Air", "flight_no": "QP-1102", "depart": "18:30", "price": 4900},
    ],
    "delhi": [
        {"airline": "IndiGo", "flight_no": "6E-505", "depart": "07:00", "price": 5200},
        {"airline": "Air India", "flight_no": "AI-502", "depart": "11:20", "price": 6900},
    ],
    "mumbai": [
        {"airline": "IndiGo", "flight_no": "6E-337", "depart": "08:10", "price": 3900},
        {"airline": "Akasa Air", "flight_no": "QP-1301", "depart": "15:45", "price": 4300},
    ],
}

MOCK_HOTELS = {
    "goa": [
        {"name": "Sunset Hostel", "style": "budget", "price_per_night": 1800, "rating": 4.0},
        {"name": "Palm Grove Resort", "style": "resort", "price_per_night": 6500, "rating": 4.5},
        {"name": "Casa Azul Boutique", "style": "boutique", "price_per_night": 4200, "rating": 4.6},
    ],
    "delhi": [
        {"name": "Metro Inn", "style": "budget", "price_per_night": 2200, "rating": 3.9},
        {"name": "Haveli Heritage Stay", "style": "boutique", "price_per_night": 5500, "rating": 4.7},
    ],
    "mumbai": [
        {"name": "Harbour Stay", "style": "budget", "price_per_night": 2800, "rating": 4.0},
        {"name": "Marine Drive Hotel", "style": "luxury", "price_per_night": 9500, "rating": 4.6},
    ],
}


# ---------------------------------------------------------------------------
# TOOL 1: search_flights
# ---------------------------------------------------------------------------
def search_flights(origin, destination, date, max_price=None):
    """Find flights.

    Input:  origin (str), destination (str), date (str, YYYY-MM-DD),
            max_price (number, optional, per person)
    Output: list of flight dicts (id, airline, flight_no, origin, destination,
            date, depart, price). Empty list if none found.
    """
    # >>> SWAP IN REAL API HERE: call your flight service and map its response
    # >>> to the same dict shape returned below.
    if date in SOLD_OUT_DATES:
        return []

    results = []
    for i, f in enumerate(MOCK_FLIGHTS.get(destination.strip().lower(), [])):
        if max_price is not None and f["price"] > max_price:
            continue
        results.append({
            "id": f"FL{i + 1}",
            "origin": origin,
            "destination": destination,
            "date": date,
            **f,
        })
    return results


# ---------------------------------------------------------------------------
# TOOL 2: search_hotels
# ---------------------------------------------------------------------------
def search_hotels(destination, check_in, nights, max_price_per_night=None):
    """Find hotels.

    Input:  destination (str), check_in (str, YYYY-MM-DD), nights (int),
            max_price_per_night (number, optional)
    Output: list of hotel dicts (id, name, style, price_per_night, rating,
            check_in, nights, total). Empty list if none found.
    """
    # >>> SWAP IN REAL API HERE: call your hotel service and map its response
    # >>> to the same dict shape returned below.
    results = []
    for i, h in enumerate(MOCK_HOTELS.get(destination.strip().lower(), [])):
        if max_price_per_night is not None and h["price_per_night"] > max_price_per_night:
            continue
        results.append({
            "id": f"HT{i + 1}",
            "check_in": check_in,
            "nights": nights,
            "total": h["price_per_night"] * nights,
            **h,
        })
    return results


# ---------------------------------------------------------------------------
# TOOL 3: book_trip  (only call this AFTER human approval)
# ---------------------------------------------------------------------------
def book_trip(flight, hotel, travelers=1):
    """Book the chosen flight and hotel.

    Input:  flight (dict from search_flights), hotel (dict from search_hotels),
            travelers (int)
    Output: dict with status, confirmation_id, total_cost, currency.
    """
    # >>> SWAP IN REAL API HERE: call your booking/payment service.
    total = flight["price"] * travelers + hotel["total"]
    return {
        "status": "confirmed",
        "confirmation_id": "TRIP-" + uuid.uuid4().hex[:8].upper(),
        "flight": f'{flight["airline"]} {flight["flight_no"]}',
        "hotel": hotel["name"],
        "travelers": travelers,
        "total_cost": total,
        "currency": CURRENCY,
    }


# Lets the agent look up a tool by name (used in later phases).
TOOLS = {
    "search_flights": search_flights,
    "search_hotels": search_hotels,
    "book_trip": book_trip,
}


# ---------------------------------------------------------------------------
# Quick self-test: run `python tools.py`
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("1) Flights to Goa:")
    flights = search_flights("Bengaluru", "Goa", "2026-12-20")
    for f in flights:
        print("  ", f)

    print("\n2) Flights to Goa under 5000:")
    print("  ", [f["flight_no"] for f in search_flights("Bengaluru", "Goa", "2026-12-20", max_price=5000)])

    print("\n3) Sold-out date (should be empty):")
    print("  ", search_flights("Bengaluru", "Goa", "2026-12-25"))

    print("\n4) Hotels in Goa, 3 nights:")
    hotels = search_hotels("Goa", "2026-12-20", 3)
    for h in hotels:
        print("  ", h)

    print("\n5) Unknown destination (should be empty):")
    print("  ", search_hotels("Atlantis", "2026-12-20", 3))

    print("\n6) Booking:")
    print("  ", book_trip(flights[0], hotels[0], travelers=2))