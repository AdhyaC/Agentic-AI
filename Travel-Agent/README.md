# Travel Agent

A conversational travel-planning demo built with Flask and the Groq API. It collects trip details, searches mock flight and hotel options, then asks you to approve or reject the suggested itinerary.

> **Note:** This project uses mock travel data. Approving a trip only simulates a booking; it does not reserve or purchase anything.

## Features

- Collects travel details through a chat interface
- Finds mock flights and hotels for supported destinations
- Considers traveler count, budget, and saved preferences
- Requests approval before simulating a booking
- Saves preferences locally in `preferences.json`

## Requirements

- Python 3.10 or later
- A Groq API key

## Setup

Open PowerShell in the `Travel-Agent` folder and create a virtual environment:

Install the dependencies:


Create a .env file in the Travel-Agent folder and add your Groq API key:


Keep your API key private. Do not commit .env to version control.

Run the app
With the virtual environment activated, start the Flask server:

python app.py


Open this address in your browser:

http://127.0.0.1:5000

Using the app
Enter your destination, travel date, and number of nights.
Answer any questions the agent asks, such as your departure city.
Review the suggested flight, hotel, and estimated total.
Select Approve trip to simulate booking, or Reject to cancel.
Project structure

Limitations
Flight, hotel, and booking data are mock data defined in tools.py.
Only destinations with entries in the mock data are supported.
Booking confirmation is simulated; no real travel is booked.
Pending approval is held in server memory and is lost if the Flask app restarts.
