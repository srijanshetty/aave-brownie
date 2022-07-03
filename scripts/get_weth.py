from brownie import config, network, interface

from scripts.helpers import get_account

def get_weth(amount = 0.1):
    """
    Get WETH by using ETH
    """
    account = get_account()
    weth = interface.IWeth(config["networks"][network.show_active()]["weth_token"])
    txn = weth.deposit({"from": account, "value": amount * 10 ** 18})
    txn.wait(2)
    return txn


def main():
    """
    Passthrough
    """
    get_weth()
