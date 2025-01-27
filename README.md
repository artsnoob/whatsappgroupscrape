# WhatsApp Group Scraper

This project scrapes data from WhatsApp groups.

## Prerequisites

- Python 3.6 or higher
- pip

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/your-repo.git
   cd your-repo
   ```
2. Install the required dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

## Usage

1.  Prepare the `group_details.csv` file with the necessary group information. This file should contain the following columns: `group_name`, `group_link`, and `last_message_time`.
2.  Run the main script:
    ```bash
    python3 main.py
    ```

The scraped data will be saved in the `scraped_data` directory. Each group's data will be saved in a separate CSV file named after the group, with the format `group_name_unread_messages.csv`.

## Project Structure

-   `main.py`: The main script for scraping WhatsApp group data.
-   `group_details.csv`: CSV file containing group details.
-   `requirements.txt`: List of required Python packages.
-   `scraped_data/`: Directory to store scraped data.
