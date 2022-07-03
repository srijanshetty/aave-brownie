from brownie import network, accounts, config

FORKED_MAINET_ENVIRONEMNTS = ("mainnet-fork-dev", )
LOCAL_NETWORKS = ("development", "local-ganache")
DECIMALS = 8
STARTING_ETHER = 1200 * 10 ** 8


def get_account(index=None, id=None):
    # Fetch from local accounts
    if index is not None:
        return accounts[index]

    # Fetch from brownie configuration
    if id is not None:
        return accounts.load(id)

    # Default values
    current_network = network.show_active()
    if (
        current_network in LOCAL_NETWORKS
        or current_network in FORKED_MAINET_ENVIRONEMNTS
    ):
        return accounts[0]

    return accounts.add(config["wallets"]["from_key"])
