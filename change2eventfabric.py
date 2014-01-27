"send wiki changes to Event Fabric"
import sys
import json
import eventfabric as ef

import wmchangebot as wmbot

CONFIG_FIELDS = ["ef_username", "ef_password", "ef_channel", "irc_server_url",
    "irc_server_port", "irc_channel", "irc_nickname", "irc_listen_nickname"]

def make_on_change_handler(ef_client, ef_channel):
    def on_change(data):
        event = ef.Event(data, ef_channel)
        ok, response = ef_client.send_event(event)

        if not ok:
            print("Error sending event", response)

    return on_change

def main():
    if len(sys.argv) != 2:
        print("usage: {} config.json".format(sys.argv[0]))
        sys.exit(1)

    config_path = sys.argv[1]
    try:
        with open(config_path) as f_in:
            config = json.load(f_in)
    except IOError as io_error:
        print("Error loading config from {}: {}".format(config_path, io_error))
        sys.exit(1)

    missing_fields = False
    for field in CONFIG_FIELDS:
        if field not in config:
            missing_fields = True
            print("Required field '{}' missing in config".format(field))

    if missing_fields:
        sys.exit(1)

    ef_url = config.get("ef_url", "http://event-fabric.com/api")
    ef_channel = config["ef_channel"]
    ef_client = ef.Client(config["ef_username"], config["ef_password"], ef_url)
    on_change = make_on_change_handler(ef_client, ef_channel)
    bot = wmbot.WikiChangeBot(config["irc_channel"], config["irc_nickname"],
            config["irc_server_url"], int(config["irc_server_port"]),
            config["irc_listen_nickname"], on_change)
    print("logging in to event fabric")
    login_ok, login_response = ef_client.login()

    if login_ok:
        print("logged in")
    else:
        print("login to event fabric failed")
        sys.exit(1)

    print("starting bot")
    bot.start()

if __name__ == "__main__":
    main()
