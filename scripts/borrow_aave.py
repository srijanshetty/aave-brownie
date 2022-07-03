from brownie import config, network, interface
from eth_utils import address
from scripts import get_weth
from scripts.helpers import get_account
from web3 import Web3

AMOUNT = Web3.toWei(0.01, "ether")


def approve_erc20(amount, spender, erc20_address, account):
    """
    You approve the spender to take the given ERC20 token amount
    from your account.
    """
    print(f"Approving {amount} {erc20_address} to {spender}")
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    print(f"Approved {amount} {erc20_address} to {spender}")
    return tx


def get_lending_pool():
    """
    Get the lending_pool using the provider
    """
    # Use the provider to fetch the lending_pool address
    lending_pool_address_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_address_provider"]
    )
    lending_pool_address = lending_pool_address_provider.getLendingPool()

    # Fetch the lending pool with the adddress
    lending_pool = interface.ILendingPool(lending_pool_address)
    print(f"Lending pool: {lending_pool.address}")
    return lending_pool


def get_borrowable_data(lending_pool, account):
    (
        total_collateral_eth,
        total_debt_eth,
        available_borrow_eth,
        current_liquidation_threshold,
        tlv,
        health_factor,
    ) = lending_pool.getUserAccountData(account.address)
    available_borrow_eth = Web3.fromWei(available_borrow_eth, "ether")
    total_collateral_eth = Web3.fromWei(total_collateral_eth, "ether")
    total_debt_eth = Web3.fromWei(total_debt_eth, "ether")

    print(f"You have {total_collateral_eth} worth of ETH deposited.")
    print(f"You have {total_debt_eth} worth of ETH borrowed.")
    print(f"You can borrow {available_borrow_eth} worth of ETH.")

    return (float(available_borrow_eth), float(total_debt_eth))


def get_asset_price():
    # For mainnet we can just do:
    # return Contract(f"{pair}.data.eth").latestAnswer() / 1e8
    dai_eth_price_feed = interface.IAggregatorV3(
        config["networks"][network.show_active()]["dai_eth_price_feed"]
    )
    latest_price = Web3.fromWei(dai_eth_price_feed.latestRoundData()[1], "ether")
    print(f"The DAI/ETH price is {latest_price}")
    return float(latest_price)


def repay_all(amount, lending_pool, account):
    approve_erc20(
        Web3.toWei(amount, "ether"),
        lending_pool.address,
        config["networks"][network.show_active()]["aave_dai_token"],
        account
    )

    repay_txn = lending_pool.repay(
        config["networks"][network.show_active()]["aave_dai_token"],
        Web3.toWei(amount, "ether"),
        1,
        account.address,
        {"from": account}
    )
    repay_txn.wait(1)

    print(f"We have repayed everything")


def borrow_aave():
    """
    Borrow Aave
    """
    account = get_account()
    amount = AMOUNT
    weth_address = config["networks"][network.show_active()]["weth_token"]

    if network.show_active() in ["mainet-fork"]:
        get_weth.get_weth()

    lending_pool = get_lending_pool()

    available_borrow_eth, total_debt_eth = get_borrowable_data(lending_pool, account)

    if total_debt_eth > 0:
        # repay loans
        print("It's time to pay up")
        repay_all(total_debt_eth, lending_pool, account)
    else:
        if available_borrow_eth > 0:
            print("We can already borrow")
        else:
            # Approve ERC20
            approve_erc20(AMOUNT, lending_pool.address, weth_address, account)

            print("Depositing WETH")
            txn = lending_pool.deposit(weth_address, amount, account.address, 0, {"from": account})
            txn.wait(1)
            print("Deposited WETH")

        # Get the DAI/ETH price
        dai_eth_price = get_asset_price()
        amount_dai_to_borrow = (available_borrow_eth * 0.5) / dai_eth_price
        print(f"We are going to borrow {amount_dai_to_borrow} DAI")

        # Let's borrow the amount
        txn = lending_pool.borrow(
            config["networks"][network.show_active()]["aave_dai_token"],
            Web3.toWei(amount_dai_to_borrow, "ether"),
            1,
            0,
            account.address,
            {"from": account},
        )
        txn.wait(1)
        print(f"We have borrowed DAI")

        # Reprint the user metrics
        get_borrowable_data(lending_pool, account)


def main():
    """
    Pass through
    """
    borrow_aave()
