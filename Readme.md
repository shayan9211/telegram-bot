## Documentation for Telegram Username Searcher

### Overview

This code is designed to automate the process of searching for Telegram usernames based on specific keywords. It also supports using multiple API keys to avoid rate limits and handles potential rate limits using exponential backoff.

### Libraries Used

- `sqlite3`: Used for lightweight database interactions.
- `datetime`: Used for date and time manipulations.
- `asyncio`: Enables asynchronous operations.
- `pyrogram`: A Telegram client used for interacting with the Telegram API.

### Setup and Configuration

1. Database Configuration (`names.db`):
    - Table `names_fifo`: Stores names to search for on Telegram. Structure:
        - `id`: Auto-incremented primary key.
        - `name`: Name or keyword.

2. Telegram API Configuration:
    - Multiple API keys can be configured.
    - Each API key entry includes `api_id`, `api_hash`, `phone` and `proxy` details.

3. Configuration Variables:
    - `USERNAME_KEYWORDS`: Keywords to match against usernames found on Telegram.
    - `CAN_PROCESS_MESSAGES`: Flag to indicate if messages can be processed.
    - `SEARCH_LIMIT_PER_KEY`: Maximum searches allowed per API key per day.
    - `DAILY_LIMIT_PER_KEY`: The daily limit of searches for each API key.
    - `MAX_RETRY_DELAY`: Maximum delay when facing rate limits.
    - `retry_delay`: Starting delay when faced with rate limits.

### Functionalities

1. **Multiple API Key Handling**:
    - The script creates instances of the Telegram client (`app_instances`) for each provided API key.
    - It uses one key at a time and switches to the next one when reaching the daily limit or the search limit for a key.

2. **Rate Limit Handling**:
    - Exponential backoff is implemented to handle rate limits.
    - If a rate limit (`FloodWait`) error is encountered, the script doubles the delay, capped at `MAX_RETRY_DELAY`.

3. **Message Handling**:
    - The script listens for messages from a specific chat (`@AllCAforTN`). 
    - When a message starting with "Name:" is detected, the name is extracted and stored in the database.

4. **Searching & Forwarding**:
    - The main loop of the script (`search_and_forward_channels()`) fetches a name from the database and searches for it on Telegram.
    - If a channel or group matches the `USERNAME_KEYWORDS` and its last message is not older than 15 days, it forwards the username to `@cadatachannel`.

### Utility Functions

1. **`switch_to_next_key()`**:
    - Switches to the next API key.

2. **`reset_daily_counts_if_new_day()`**:
    - Checks if it's a new day. If so, it resets the search counts.

3. **`search(_keywords)`**:
    - Performs the search on Telegram for a given keyword and handles the results.

4. **`fetch_name_from_db()`**:
    - Fetches the next name from the database.

5. **`delete_name_from_db(name_id)`**:
    - Deletes a name from the database using its `id`.

### Execution

- When the script is run, it starts the main loop to search and forward channels/groups based on names from the database.
- On KeyboardInterrupt (e.g., pressing Ctrl+C), the script will stop all client instances gracefully.


### Proxy Setup with SmartProxy

1. **Purchasing the SmartProxy Plan**:
    - Navigate to the SmartProxy website.
    - Choose the "Buy As You Go" plan, which costs around $8.5 per GB.
    - Complete the purchase process by following the on-site instructions.

2. **Enabling Telegram API Access on SmartProxy**:
    - After purchasing the plan, navigate to the help chat on the SmartProxy platform.
    - Ask the support staff to enable access to the Telegram API for your account. They should be able to assist with this.

3. **Retrieve Proxy Credentials**:
    - Once Telegram API access is enabled, go to your SmartProxy dashboard.
    - Retrieve your proxy credentials which include: `hostname`, `port`, `username`, and `password`.

4. **Integrate Proxy Credentials into the Script**:
    - Locate the `API_KEYS` list in the script.
    - For each API key you intend to use with a proxy, fill in the proxy details in the following format:
      ```python
      "proxy": {
          'hostname': 'YOUR_SMARTPROXY_HOSTNAME',
          'port': YOUR_SMARTPROXY_PORT,
          'username': 'YOUR_SMARTPROXY_USERNAME',
          'password': 'YOUR_SMARTPROXY_PASSWORD',
          'scheme': 'SOCKS5'
      }
      ```

# telegram-bot
