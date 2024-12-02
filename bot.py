from discord.ext import commands
import discord
import csv
import json
import asyncio
from rich.console import Console

console = Console()

def run(token, running):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    bot = commands.Bot(command_prefix="$", self_bot=True, request_guilds=False, chunk_guilds_at_startup=False)

    def format_products(products):
        formatted = []
        for product_id, details in products.items():
            formatted.append(details['product_name'])
        return "\n- ".join(formatted)
    
    def format_product_details(details):
        product_name = details['product_name']
        price = details['price']
        stock = details['stock']
        min_buy = details.get('min_buy', 'N/A')
        return product_name, price, stock, min_buy

    @bot.command
    async def cmds(ctx):
        await ctx.message.delete()
        help_text = """
## Bot Commands
```ini
+ [!help] - Shows this help message
+ [!crypto coin] - Get crypto address for specified coin
+ [!stock category product] - Check stock information
>     Without product: Lists all products in category
>     With product: Shows detailed product information
+ [!payment type] - Get payment information
>     crypto: Shows crypto payment details
>     paypal: Shows PayPal payment details
```
"""
        await ctx.send(help_text)
    
    @bot.command()
    async def crypto(ctx, coin: str):
        await ctx.message.delete()
        with open("crypto_addresses.csv", "r") as file:
            reader = csv.reader(file)
            coin_address = None
            for row in reader:
                if row[0].lower() == coin.lower():
                    coin_address = row[1]
                    break
        
        if coin_address:
            await ctx.send(f"> {coin.upper()}\n> {coin_address}")
        else:
            await ctx.send(f"No address found for {coin}", delete_after=3)
    
    @bot.command()
    async def stock(ctx, category: str, product: str=None):
        await ctx.message.delete()
        try:
            with open("stock.json", "r") as file:
                stock_data = json.load(file)

            if not category:
                print("Please enter a category!")
            elif category not in stock_data:
                print("Category not found!")
            else:
                category_data = stock_data[category]['products']
                if not product:
                    await ctx.send(f"All products in {stock_data[category]['category_name']}:\n- " + format_products(category_data))
                else:
                    if product in category_data:
                        product_name, price, stock, min_buy = format_product_details(category_data[product])
                        await ctx.send(f"## Product Details - {product_name}\n> Price: {price}\n> Stock: {stock}\n> Min Buy: {min_buy}")
                    else:
                        await ctx.send(f"Product not found in {stock_data[category]['category_name']}\nAvailable products:\n- " + format_products(category_data))

        except FileNotFoundError:
            print("Stock file not found!")
        except json.JSONDecodeError:
            print("Invalid JSON file format!")

    @stock.error
    async def stock_error(ctx):
        await ctx.message.delete()
        await ctx.send("<a:error:1263985932080779355> Please enter a category!", delete_after=3)
        

    @bot.command()
    async def payment(ctx, payment_type: str=None):
        await ctx.message.delete()
        if payment_type == "crypto":
            await ctx.send("<:CRYPTO:1291409202224300074> Crypto Payments:\n > Accepting LTC, USDT, XRP, USDC, TRON\n > TXID must be sent after payment\n > Payments can be processed via DMs or on [our website](https://petsgostore.sellsn.io/).")
        elif payment_type == "paypal":
            await ctx.send("<:PAYPAL:1295671746346614878> PayPal Payments:\n > Accepting PayPal Friends & Family Only\n > Send a screenshot of the payment receipt after purchase\n > 5% processing fee will be added to your purchase\n > Payments can only be processed via DMs.")
        elif payment_type == "stripe":
            await ctx.send("<:card:1168240268668059811> Stripe Payments:\n > Accepting card payments via Stripe\n > Send your SellSN invoice after purchase.\n > 5% processing fee will be added to your purchase\n > Payments can only be processed through [our website](https://petsgostore.sellsn.io/).")
        else:
            await ctx.send("<:money:1265013290640211999> Payment Types:\n > <:CRYPTO:1291409202224300074> Crypto\n > <:PAYPAL:1295671746346614878> PayPal F&F (DMs ONLY)\n > <:card:1168240268668059811> Stripe (Website Only)")

    @bot.command()
    async def sell(ctx, product: str, quantity: int, payment_type: str=None):
        await ctx.message.delete()
        try:
            with open("stock.json", "r") as file:
                stock_data = json.load(file)

            # Search through categories to find product
            product_found = False
            product_price = None
            for category in stock_data.values():
                if product in category['products']:
                    product_data = category['products'][product]
                    
                    # Get price (remove $ and convert to float)
                    price_str = product_data['price'].replace('$', '')
                    if '/m' in price_str:  # Handle prices like "$1/m"
                        price_str = price_str.split('/')[0]
                    product_price = float(price_str)
                    
                    # Check if enough stock
                    if product_data['stock'] >= quantity:
                        if payment_type == "stripe":
                            payment_type = "<:card:1168240268668059811> Stripe"
                        elif payment_type == "paypal":
                            payment_type = "<:PAYPAL:1295671746346614878> PayPal F&F"
                        elif payment_type == "crypto":
                            payment_type = "<:CRYPTO:1291409202224300074> Crypto"
                        
                        await ctx.send(f"## Sell Order - {product_data['product_name']}\n> Price: ${product_price}\n> Quantity: {quantity}\n> Payment Type: {payment_type}\n\nSend `confirm` to finalize your order.\n-# By confirming, you agree that all sales are final and no refunds will be given.")

                        def check(message):
                            return message.content.lower() == "confirm"
                        
                        try:
                            message = await bot.wait_for("message", timeout=30.0, check=check)
                        except asyncio.TimeoutError:
                            await ctx.send("Order timed out!")
                            return
                        else:
                            # Update stock
                            product_data['stock'] -= quantity
                            product_found = True
                            
                            # Write updated stock back to file
                            with open("stock.json", "w") as f:
                                json.dump(stock_data, f, indent=4)
                            
                            # Add order to orders.json
                            with open("orders.json", "r") as file:
                                orders_data = json.load(file)
                            
                            orders_data['orders'][str(len(orders_data['orders']) + 1)] = {
                                "product": product,
                                "quantity": quantity,
                                "price": product_price,
                                "payment_type": payment_type
                            }
                            
                            with open("orders.json", "w") as f:
                                json.dump(orders_data, f, indent=4)
                                
                            await ctx.send(f"> <a:animated_right_tick:983462311819886593> Successfully reserved `{quantity}x {product_data['product_name']}`!\n-# Please wait for your order to be delivered.")
                    else:
                        await ctx.send(f"> <a:animated_wrong_cross:983462314059632671> Not enough stock! Only {product_data['stock']} available.", delete_after=3)
                    break
            
            if not product_found:
                await ctx.send(f"Product '{product}' not found!", delete_after=3)

        except FileNotFoundError:
            await ctx.send("Stock file not found!", delete_after=3)
        except json.JSONDecodeError:
            await ctx.send("Invalid stock file format!", delete_after=3)
        except ValueError:
            await ctx.send("Error processing product price!", delete_after=3)

    @bot.command()
    async def add_stock(ctx, product: str, quantity: int):
        await ctx.message.delete()
        try:
            with open("stock.json", "r") as file:
                stock_data = json.load(file)

            if product not in stock_data:
                await ctx.send(f"Product '{product}' not found!", delete_after=3)
            else:
                stock_data[product]['stock'] += quantity
                with open("stock.json", "w") as f:
                    json.dump(stock_data, f, indent=4)
                await ctx.send(f"> <a:animated_right_tick:983462311819886593> Successfully added {quantity} to {product}!")

        except FileNotFoundError:
            await ctx.send("Stock file not found!", delete_after=3)
        except json.JSONDecodeError:
            await ctx.send("Invalid stock file format!", delete_after=3)
    

    try:
        loop.run_until_complete(bot.start(token))
        while running:
            try:
                loop.run_until_complete(asyncio.sleep(1))
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                break
    finally:
        loop.run_until_complete(bot.close())
        loop.close()
    