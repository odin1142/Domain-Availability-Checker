# Domain Availability Checker

## Overview

The Domain Availability Checker is a web application built with Flask that allows users to check the availability of domain names. It utilizes Namecheap's API to check domain availability and stores results in a SQLite database. The application supports filtering domains based on user-defined criteria, such as prefixes, suffixes, and strings that must or must not be included.

## Features

Check the availability of domain names using Namecheap's API.
Filter domain names based on prefixes, suffixes, and inclusion/exclusion of specific strings.
Store domain availability results in a SQLite database.
Mark domains as favorites for easy tracking.
Prerequisites

Before running the application, ensure you have the following:

- Python 3.6 or higher
- pip (Python package installer)

## Setup Instructions

### 1. Clone the Repository
Clone the application repository to your local machine using Git.

### 2. Set Up a Python Virtual Environment
Setting up a virtual environment is crucial for isolating the project's dependencies. Perform the following steps in your terminal:

```bash
# Navigate to the project directory
cd path/to/Domain-Availability-Checker

# Create the virtual environment
python3 -m venv venv

# Activate the virtual environment
# On Windows
venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate
```

### 3. Install Required Packages
Install all the required Python packages using pip:

```bash
pip install -r requirements.txt
```
### 4. Environment Variables
The application requires setting up the following environment variables:

- `API_USER`: Your Namecheap API username.
- `API_KEY`: Your Namecheap API key.
- `API_IP`: The IP address whitelisted for API access.
These can be set in your environment or using an .env file that the application will read upon startup.

### 5. Initialize the Database
Before running the application for the first time, initialize the SQLite database by starting the application once. This process creates the necessary tables.

### 6. Run the Application
Run the application using the following command:

```bash
python app.py
```
The application will start and be accessible at `http://localhost:5000`.

## Usage

Navigate to http://localhost:5000 in your web browser to access the Domain Availability Checker. Use the web interface to input your search criteria and check the availability of domain names.

## Contributing

Contributions are welcome! Please fork the repository and submit pull requests with any improvements or bug fixes.

