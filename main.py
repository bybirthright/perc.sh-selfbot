import discord as dc
from discord.ext import commands
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.spinner import Spinner
from rich.align import Align
import csv
import keyboard
import time
import os
import bot
import json
import threading

console = Console()  # Global console instance
bot_thread = None
bot_running = False

def wait_for_key(*keys):
    while True:
        for key in keys:
            if keyboard.is_pressed(key):
                time.sleep(0.2)  # Prevent key bounce
                return key

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def read_crypto_addresses():
    addresses = []
    try:
        with open("crypto_addresses.csv", "r") as file:
            reader = csv.reader(file)
            addresses = list(reader)
    except FileNotFoundError:
        pass
    return addresses

def write_crypto_addresses(addresses):
    with open("crypto_addresses.csv", "w", newline='') as file:
        writer = csv.writer(file)
        writer.writerows(addresses)

def remove_crypto_menu():
    addresses = read_crypto_addresses()
    if not addresses:
        console.print("[yellow]No crypto addresses found![/yellow]")
        time.sleep(2)
        return

    console.print("\n[bold]Current Crypto Addresses:[/bold]\n")
    for i, (name, address) in enumerate(addresses, 1):
        console.print(f"[green][[bold white]{i}[/bold white]] {name}: {address}[/green]")
    
    console.print("\n[blue]Press the number to remove an address (or 'b' to go back)[/blue]")
    valid_keys = [str(i) for i in range(1, len(addresses) + 1)] + ['b']
    choice = wait_for_key(*valid_keys)
    
    if choice == 'b':
        return
    
    index = int(choice) - 1
    removed_name = addresses[index][0]
    addresses.pop(index)
    write_crypto_addresses(addresses)
    
    console.print(f"[green]Successfully removed {removed_name}![/green]")
    time.sleep(2)

def load_token():
    try:
        with open("token.txt", "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return None

def start_bot_thread(token):
    global bot_running
    bot_running = True
    bot.run(token, bot_running)

def stop_bot_thread():
    global bot_running, bot_thread
    bot_running = False
    if bot_thread:
        bot_thread.join()
        bot_thread = None

def main():
    global bot_thread, bot_running
    current_menu = "main"
    
    while True:
        clear_screen()
        
        console.print(f"""[red]
                            ░       ░░░        ░░       ░░░░      ░░░░░░░      ░░░  ░░░░  ░
                            ▒  ▒▒▒▒  ▒▒  ▒▒▒▒▒▒▒▒  ▒▒▒▒  ▒▒  ▒▒▒▒  ▒▒▒▒▒  ▒▒▒▒▒▒▒▒  ▒▒▒▒  ▒
                            ▓       ▓▓▓      ▓▓▓▓       ▓▓▓  ▓▓▓▓▓▓▓▓▓▓▓▓      ▓▓▓        ▓
                            █  ████████  ████████  ███  ███  ████  ███████████  ██  ████  █
                            █  ████████        ██  ████  ███      ███ ███      ███  ████  █
                                                             
        [/red]""")
        if current_menu == "main":
            if not bot_running:
                console.print(Panel("                                         [bold red][italic]perc.sh[/italic][white] - Discord Selfbot - [/white][bold red]OFFLINE[/bold red]", box=box.MARKDOWN))
                console.print()
            else:
                console.print(Panel("                                         [bold red][italic]perc.sh[/italic][white] - Discord Selfbot - [/white][bold green]ONLINE[/bold green]", box=box.MARKDOWN))
                console.print()

            # Modify options based on bot state
            if not bot_running:
                options = [
                    ("1", "Start Selfbot"),
                    ("2", "Orders"),
                    ("3", "Settings"),
                    ("4", "Exit")
                ]
            else:
                options = [
                    ("1", "Stop Selfbot"),
                    ("2", "Orders"),
                    ("3", "Settings"),
                    ("4", "Exit")
                ]
            
            menu_text = "\n".join([
                f"[red][[bold white]{opt}[/bold white]] {desc}[/red]"
                for opt, desc in options
            ])
            
            console.print(Align.center(Panel(menu_text, box=box.ROUNDED, title="Main Menu", title_align="center", expand=False, padding=(0, 3)), vertical="middle"))
            
            choice = wait_for_key("1", "2", "3", "4")
            if choice == "1":
                if not bot_running:
                    token = load_token()
                    if not token:
                        console.print("[red]No token found! Please set your token in settings first.[/red]")
                        time.sleep(2)
                        continue
                    bot_thread = threading.Thread(target=start_bot_thread, args=(token,))
                    bot_thread.daemon = True
                    bot_thread.start()
                    with console.status("[green]Selfbot starting...[/green]", spinner="material"):
                        time.sleep(4)
                    console.print("[green]Selfbot started successfully![/green]")
                    time.sleep(2)
                else:
                    stop_bot_thread()
                    with console.status("[red]Selfbot stopping...[/red]", spinner="material"):
                        time.sleep(4)
                    console.print("[green]Selfbot stopped successfully![/green]")
                    time.sleep(2)
            elif choice == "2":
                current_menu = "orders"
            elif choice == "3":
                current_menu = "settings"
            elif choice == "4":
                if bot_running:
                    stop_bot_thread()
                exit()

        elif current_menu == "settings":
            title = Text("Settings", style="bold red")

            if not bot_running:
                console.print(Panel("                                         [bold red][italic]perc.sh[/italic][white] - Discord Selfbot - [/white][bold red]OFFLINE[/bold red]", box=box.MARKDOWN))
                console.print()
            else:
                console.print(Panel("                                         [bold red][italic]perc.sh[/italic][white] - Discord Selfbot - [/white][bold green]ONLINE[/bold green]", box=box.MARKDOWN))
                console.print()

            options = [
                ("1", "Change Token"),
                ("2", "Manage Crypto Addresses"),
                ("3", "Back")
            ]

            settings_text = "\n".join([
                f"[blue][[bold white]{opt}[/bold white]] {desc}[/blue]"
                for opt, desc in options
            ])
            console.print(Panel(settings_text, box=box.ROUNDED, title="Settings", title_align="center"))
            
            choice = wait_for_key("1", "2", "3")
            if choice == "1":
                change_token()
                current_menu = "main"
            elif choice == "2":
                current_menu = "crypto"
            elif choice == "3":
                current_menu = "main"

        elif current_menu == "crypto":
            title = Text("Manage Crypto Addresses", style="bold red")
            console.print(Panel(title, box=box.DOUBLE_EDGE))
            console.print()

            options = [
                ("1", "Add Crypto Address"),
                ("2", "Remove Crypto Address"),
                ("3", "Back")
            ]

            crypto_text = "\n".join([
                f"[color=130][[bold white]{opt}[/bold white]] {desc}[/color]"
                for opt, desc in options
            ])
            console.print(Panel(crypto_text, box=box.ROUNDED))
            
            choice = wait_for_key("1", "2", "3")
            if choice == "1":
                new_address = []
                console.print(f"[green]Enter your crypto name:[/green]")
                new_address.append(console.input("> "))
                console.print(f"[green]Enter your crypto address:[/green]")
                new_address.append(console.input("> "))
                with open("crypto_addresses.csv", "a", newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(new_address)
                console.print("[green]Crypto address added successfully![/green]")
                time.sleep(2)
                current_menu = "crypto"
            elif choice == "2":
                clear_screen()
                remove_crypto_menu()
                current_menu = "crypto"
            elif choice == "3":
                current_menu = "settings"
        
        elif current_menu == "orders":
            title = Text("View Orders", style="bold red")
            console.print(Panel(title, box=box.DOUBLE_EDGE))
            console.print()

            with open("orders.json", "r") as file:
                orders_data = json.load(file)

            for order_id, order_details in orders_data['orders'].items():
                console.print(f"[green][[bold white]Order {order_id}[/bold white]]")
                console.print(f"  > Product: {order_details['product']}")
                console.print(f"  > Quantity: {order_details['quantity']}")
                console.print(f"  > Price: ${order_details['price']}")
                console.print(f"  > Payment Type: {order_details['payment_type']}")
                console.print()

            console.print(f"[blue]Press 'b' to go back[/blue]")
            back_key = wait_for_key("b")
            if back_key == "b":
                current_menu = "main"
            


def change_token():
    global token
    console.print(f"[green]Enter your new token:[/green]")
    token = console.input("> ")
    with open("token.txt", "w") as file:
        file.write(token)

if __name__ == "__main__":
    main()