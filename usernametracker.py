import json
import os
import sys
import time
import logging
import requests
import concurrent.futures
from colorama import init, Fore, Style

# Initialize colorama for Windows and Unix
init(autoreset=True)

SITES_FILE = "sites.json"

# Configura il sistema di logging
logging.basicConfig(
    filename='ghostfinder.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def load_sites():
    if not os.path.exists(SITES_FILE):
        print(f"{Fore.RED}[!] Error: {SITES_FILE} not found.{Style.RESET_ALL}")
        sys.exit(1)
    with open(SITES_FILE, 'r') as f:
        return json.load(f)

def check_username(site_name, url_template, username):
    url = url_template.format(username)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    # Limite di velocità per non saturare la rete e rispettare i server (Rate Limiting)
    time.sleep(0.5)
    
    try:
        logging.info(f"Checking {site_name} at {url}")
        # allow_redirects=False improves accuracy for sites that redirect to homepage if user doesn't exist
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=False)
        
        if response.status_code == 200:
            if len(response.text) > 1000:
                logging.info(f"FOUND - {site_name}: {url}")
                return site_name, url, True
        
        logging.info(f"NOT FOUND - {site_name} (Status: {response.status_code})")
        return site_name, url, False
    except requests.exceptions.RequestException as e:
        logging.error(f"ERROR on {site_name}: {str(e)}")
        return site_name, url, False

def print_banner():
    banner = f"""
{Fore.CYAN}
  _    _                                       _______             _             
 | |  | |                                     |__   __|           | |            
 | |  | |___  ___ _ __ _ __   __ _ _ __ ___   ___| | _ __ __ _  ___| | _____ _ __ 
 | |  | / __|/ _ \\ '__| '_ \\ / _` | '_ ` _ \\ / _ \\ || '__/ _` |/ __| |/ / _ \\ '__|
 | |__| \\__ \\  __/ |  | | | | (_| | | | | | |  __/ || | | (_| | (__|   <  __/ |   
  \\____/|___/\\___|_|  |_| |_|\\__,_|_| |_| |_|\\___|_||_|  \\__,_|\\___|_|\\_\\___|_|   
                                                                                 
{Fore.YELLOW}  OSINT Username Tracker - Enhanced Edition
{Style.RESET_ALL}
"""
    print(banner)

def print_disclaimer():
    disclaimer = f"""
{Fore.RED}{Style.BRIGHT}================================================================================
                                LEGAL DISCLAIMER
================================================================================
By using this software, you acknowledge and agree to the following terms:

1. PUBLIC DATA ONLY: This tool exclusively collects publicly accessible 
   information.
2. NO BYPASSING SECURITY: This tool does NOT bypass authentication mechanisms, 
   CAPTCHAs, or any security measures.
3. NO UNAUTHORIZED ACCESS: This tool does NOT perform unauthorized access to 
   systems, accounts, or private databases.
4. COMPLIANCE WITH LAWS: Your use of this tool must strictly comply with all 
   applicable laws and the Terms of Service (ToS) of the queried websites.
5. RATE LIMITING: This tool includes logging and rate-limiting to prevent 
   excessive requests to targeted servers and maintain ethical OSINT practices.

IF YOU DO NOT AGREE TO THESE TERMS, YOU MUST TERMINATE THIS SCRIPT IMMEDIATELY.
================================================================================{Style.RESET_ALL}
"""
    print(disclaimer)

def main():
    print_banner()
    print_disclaimer()
    
    time.sleep(2)
    
    if "--accept" not in sys.argv:
        accetta = input(f"{Fore.YELLOW}Have you read, understood, and do you fully accept the conditions above? (y/n): {Style.RESET_ALL}")
        if accetta.lower() != 'y':
            print(f"{Fore.RED}[!] Execution aborted. You must accept the disclaimer to use this tool.{Style.RESET_ALL}")
            sys.exit(1)
            
    args = [arg for arg in sys.argv[1:] if arg != "--accept"]
    
    if len(args) > 0:
        username = args[0]
    else:
        username = input(f"{Fore.BLUE}[?] Enter the username to track: {Style.RESET_ALL}")

    if not username.strip():
        print(f"{Fore.RED}[!] Invalid username.{Style.RESET_ALL}")
        sys.exit(1)

    sites = load_sites()
    
    logging.info(f"=== STARTED NEW SCAN FOR USERNAME: {username} ===")
    print(f"\\n{Fore.CYAN}[*] Search in progress for: {Fore.WHITE}{username}{Fore.CYAN} across {len(sites)} websites...{Style.RESET_ALL}\\n")

    found_accounts = []
    
    # Reduced max_workers to 5 to enforce rate limiting and be polite to networks
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_site = {
            executor.submit(check_username, name, url_tpl, username): name 
            for name, url_tpl in sites.items()
        }
        
        for future in concurrent.futures.as_completed(future_to_site):
            site_name, url, is_found = future.result()
            if is_found:
                print(f"{Fore.GREEN}[+] FOUND: {site_name}{Style.RESET_ALL} -> {url}")
                found_accounts.append(url)

    print(f"\\n{Fore.CYAN}[*] Search completed! Found {Fore.GREEN}{len(found_accounts)}{Fore.CYAN} accounts across {len(sites)} tested.{Style.RESET_ALL}")
    
    logging.info(f"=== SCAN COMPLETED. FOUND {len(found_accounts)} ACCOUNTS ===")
    
    if found_accounts:
        report_file = f"report_{username}.txt"
        with open(report_file, 'w') as f:
            f.write(f"Report for username: {username}\\n")
            f.write("="*30 + "\\n")
            for acc in found_accounts:
                f.write(acc + "\\n")
        print(f"{Fore.YELLOW}[!] Results have been saved in {report_file}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[!] Execution logs saved in ghostfinder.log{Style.RESET_ALL}\\n")

if __name__ == "__main__":
    main()
