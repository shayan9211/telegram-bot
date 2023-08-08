import sqlite3
import datetime
import asyncio
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.raw import functions

# Database setup
conn = sqlite3.connect('names.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS names_fifo (
    id INTEGER PRIMARY KEY,
    name TEXT
)
''')
conn.commit()

API_KEYS = [
    {
        "api_id": "",
        "api_hash": "",
        "phone": "",
        "proxy": {
            'hostname': 'proxy1_hostname',
            'port': 10000,
            'username': 'proxy1_username',
            'password': 'proxy1_password',
            'scheme': 'SOCKS5'
        }
    },
    {
        "api_id": "",
        "api_hash": "",
        "phone": "",
        "proxy": {
            'hostname': 'proxy2_hostname',
            'port': 10001,
            'username': 'proxy2_username',
            'password': 'proxy2_password',
            'scheme': 'SOCKS5'
        }
    },
    # ... (other API keys with their proxies)
]


USERNAME_KEYWORDS = ["erc", "portal", "token",
                     "eth", "erc20", "official", "coin", "meme"]

CAN_PROCESS_MESSAGES = True

SEARCH_LIMIT_PER_KEY = 200
DAILY_LIMIT_PER_KEY = 200

# Initial setup for tracking
CURRENT_KEY_INDEX = 0
SEARCH_COUNTS = [0] * len(API_KEYS)
LAST_SEARCH_TIMESTAMP = [datetime.datetime.now() for _ in API_KEYS]

app_instances = [
    Client(
        "my_account_" + key["phone"],
        api_id=key["api_id"],
        api_hash=key["api_hash"],
        phone_number=key["phone"],
        proxy=dict(
            hostname=key['proxy']['hostname'],
            port=key['proxy']['port'],
            username=key['proxy']['username'],
            password=key['proxy']['password'],
            scheme=key['proxy']['scheme']
        )
    ) for key in API_KEYS
]

for app in app_instances:
    app.start()

current_app = app_instances[CURRENT_KEY_INDEX]

# Added exponential backoff for rate limiting
MAX_RETRY_DELAY = 600  # e.g., 600 seconds or 10 minutes
retry_delay = 1  # start with a 1-second delay


@current_app.on_message(filters.chat("@AllCAforTN"))
async def forward_handler(client, message):
    global CAN_PROCESS_MESSAGES
    if not CAN_PROCESS_MESSAGES:
        return
    for line in message.text.split('\n'):
        if line.startswith("Name:"):
            name = ' '.join(line.split()[1:]).split('(')[0].strip()
            cursor.execute("INSERT INTO names_fifo (name) VALUES (?)", (name,))
            conn.commit()
            print(f"Name added to database: {name}")
            break


def switch_to_next_key():
    global CURRENT_KEY_INDEX, current_app
    CURRENT_KEY_INDEX += 1
    if CURRENT_KEY_INDEX >= len(API_KEYS):
        CURRENT_KEY_INDEX = 0
    current_app = app_instances[CURRENT_KEY_INDEX]
    print(f"Switched to API key: {API_KEYS[CURRENT_KEY_INDEX]['phone']}")


def reset_daily_counts_if_new_day():
    global CAN_PROCESS_MESSAGES, LAST_SEARCH_TIMESTAMP, SEARCH_COUNTS
    CAN_PROCESS_MESSAGES = True
    for i, timestamp in enumerate(LAST_SEARCH_TIMESTAMP):
        if (datetime.datetime.now().date() - timestamp.date()).days > 0:
            SEARCH_COUNTS[i] = 0
            LAST_SEARCH_TIMESTAMP[i] = datetime.datetime.now()


async def search(_keywords):
    global CURRENT_KEY_INDEX, LAST_SEARCH_TIMESTAMP, retry_delay

    days_old = datetime.datetime.now() - datetime.timedelta(days=15)

    print(
        f"Searching with key: {API_KEYS[CURRENT_KEY_INDEX]['phone']} (Search #{SEARCH_COUNTS[CURRENT_KEY_INDEX] + 1} of the day) for: {_keywords}")

    try:
        response = await current_app.invoke(functions.contacts.Search(q=_keywords, limit=30))
        all_usernames = [chat.username for chat in response.chats if hasattr(
            chat, 'username') and chat.username]
        print(f"All usernames found for {_keywords}: {all_usernames}")

        found_matching_channel = False

        for chat in response.chats:
            if not hasattr(chat, 'username') or not chat.username:
                continue

            username = chat.username
            if not any(keyword in username.lower() for keyword in USERNAME_KEYWORDS):
                continue

            message = await current_app.get_messages(username, 1)
            if message.date and message.date <= days_old:
                continue

            if message.date and message.date > days_old:
                print(
                    f"Found @{username} that matches the criteria. Forwarding to @cadatachannel.")
                await current_app.send_message("@cadatachannel", username)
                await asyncio.sleep(1)
                found_matching_channel = True

        if not found_matching_channel:
            print("No channels matched the criteria.")

        retry_delay = 1  # If the search was successful, reset the delay.

    except FloodWait as e:
        print(f"FloodWait error. Need to wait for {e.x} seconds.")
        await asyncio.sleep(e.x)
        # Double the delay.
        retry_delay = min(2 * retry_delay, MAX_RETRY_DELAY)

    finally:
        LAST_SEARCH_TIMESTAMP[CURRENT_KEY_INDEX] = datetime.datetime.now()


async def search_and_forward_channels():
    global CURRENT_KEY_INDEX, SEARCH_COUNTS, CAN_PROCESS_MESSAGES
    while True:
        reset_daily_counts_if_new_day()

        if SEARCH_COUNTS[CURRENT_KEY_INDEX] >= DAILY_LIMIT_PER_KEY:
            switch_to_next_key()

            if all(count >= DAILY_LIMIT_PER_KEY for count in SEARCH_COUNTS):
                CAN_PROCESS_MESSAGES = False

                next_available_time = min(
                    (timestamp + datetime.timedelta(days=1)
                     for timestamp in LAST_SEARCH_TIMESTAMP)
                )
                sleep_duration = (next_available_time -
                                  datetime.datetime.now()).total_seconds()

                if sleep_duration > 0:
                    await asyncio.sleep(sleep_duration)
                continue

        CAN_PROCESS_MESSAGES = True

        name_entry = fetch_name_from_db()
        if not name_entry:
            await asyncio.sleep(60)
            continue

        name_id, name = name_entry
        await search(name)
        delete_name_from_db(name_id)

        SEARCH_COUNTS[CURRENT_KEY_INDEX] += 1
        if SEARCH_COUNTS[CURRENT_KEY_INDEX] >= SEARCH_LIMIT_PER_KEY:
            switch_to_next_key()


def fetch_name_from_db():
    cursor.execute("SELECT id, name FROM names_fifo ORDER BY id ASC LIMIT 1")
    return cursor.fetchone()


def delete_name_from_db(name_id):
    cursor.execute("DELETE FROM names_fifo WHERE id=?", (name_id,))
    conn.commit()


async def main():
    await search_and_forward_channels()

if __name__ == '__main__':
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        for app in app_instances:
            app.stop()
