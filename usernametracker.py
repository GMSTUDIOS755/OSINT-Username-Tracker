import json
import os
import sys
import time
import requests
import concurrent.futures
from colorama import init, Fore, Style

# Initialize colorama for Windows and Unix
init(autoreset=True)

SITES_FILE = "sites.json"

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
    try:
        # allow_redirects=False improves accuracy for sites that redirect to homepage if user doesn't exist
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=False)
        
        # Status code 200 means the page exists
        # We exclude 3xx codes (redirects) which often indicate page not found
        if response.status_code == 200:
            # Further check: if the content is too small, it might be a fake 200 page
            if len(response.text) > 1000:
                return site_name, url, True
        return site_name, url, False
    except requests.exceptions.RequestException:
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

1. EDUCATIONAL PURPOSE: This tool is provided "as is" and exclusively for 
   educational purposes, authorized Open Source Intelligence (OSINT) research, 
   and personal digital footprint auditing.
2. NO LIABILITY: The author(s), contributor(s), and maintainer(s) of this script 
   assume absolutely NO responsibility for any consequences, damages, or legal 
   actions arising from the use or misuse of this software.
3. COMPLIANCE WITH LAWS: It is your sole responsibility to ensure that your use 
   of this tool complies with all applicable local, state, national, and 
   international privacy laws and regulations (e.g., GDPR, CCPA).
4. NO MALICIOUS USE: You expressly agree NOT to use this tool for stalking, 
   doxxing, harassment, unauthorized reconnaissance, or any other malicious 
   activity against individuals or organizations.
5. TERMS OF SERVICE: You are responsible for abiding by the Terms of Service 
   (ToS) and Acceptable Use Policies (AUP) of the individual platforms being 
   queried. This tool merely automates public HTTP requests; excessive usage 
   may lead to IP bans.

IF YOU DO NOT AGREE TO THESE TERMS, YOU MUST TERMINATE THIS SCRIPT IMMEDIATELY.
================================================================================{Style.RESET_ALL}
"""
    print(disclaimer)

def main():
    print_banner()
    print_disclaimer()
    
    # Dramatic pause to force reading the disclaimer
    time.sleep(2)
    
    # If the "--accept" argument is passed, skip the confirmation
    if "--accept" not in sys.argv:
        accetta = input(f"{Fore.YELLOW}Have you read, understood, and do you fully accept the conditions above? (y/n): {Style.RESET_ALL}")
        if accetta.lower() != 'y':
            print(f"{Fore.RED}[!] Execution aborted. You must accept the disclaimer to use this tool.{Style.RESET_ALL}")
            sys.exit(1)
            
    # Filter any arguments not related to the username
    args = [arg for arg in sys.argv[1:] if arg != "--accept"]
    
    if len(args) > 0:
        username = args[0]
    else:
        username = input(f"{Fore.BLUE}[?] Enter the username to track: {Style.RESET_ALL}")

    if not username.strip():
        print(f"{Fore.RED}[!] Invalid username.{Style.RESET_ALL}")
        sys.exit(1)

    sites = load_sites()
    
    print(f"\\n{Fore.CYAN}[*] Search in progress for: {Fore.WHITE}{username}{Fore.CYAN} across {len(sites)} websites...{Style.RESET_ALL}\\n")

    found_accounts = []
    
    # Increase workers to handle the larger number of sites
    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        future_to_site = {
            executor.submit(check_username, name, url_tpl, username): name 
            for name, url_tpl in sites.items()
        }
        
        for future in concurrent.futures.as_completed(future_to_site):
            site_name, url, is_found = future.result()
            if is_found:
                print(f"{Fore.GREEN}[+] FOUND: {site_name}{Style.RESET_ALL} -> {url}")
                found_accounts.append(url)
            else:
                # We disable printing "NOT FOUND" to keep the output clean
                pass

    print(f"\\n{Fore.CYAN}[*] Search completed! Found {Fore.GREEN}{len(found_accounts)}{Fore.CYAN} accounts across {len(sites)} tested.{Style.RESET_ALL}")
    
    if found_accounts:
        report_file = f"report_{username}.txt"
        with open(report_file, 'w') as f:
            f.write(f"Report for username: {username}\\n")
            f.write("="*30 + "\\n")
            for acc in found_accounts:
                f.write(acc + "\\n")
        print(f"{Fore.YELLOW}[!] Results have been saved in {report_file}{Style.RESET_ALL}\\n")

if __name__ == "__main__":
    main()
