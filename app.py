import os
from flask import Flask, render_template, request, jsonify
import sqlite3
import random
import string
import requests

# Configurations, loaded from env variables
# If using env.sh, make sure to run source env.sh
NAMECHEAP_API_USER = os.getenv('API_USER') 
NAMECHEAP_API_KEY = os.getenv('API_KEY') 
NAMECHEAP_API_IP = os.getenv('API_IP')
DATABASE_PATH = 'domains.db'

app = Flask(__name__, template_folder="templates/")

def create_database():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS domains (
            domain_name TEXT PRIMARY KEY,
            available INT,
            favorite INT DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def check_domain_availability(domains):
    """
    Checks if a list of domains is available using Namecheap's API.

    :param domains: A list of domains to check.
    :param api_user: Your Namecheap API username.
    :param api_key: Your Namecheap API key.
    :param client_ip: The IP address that is whitelisted for API access.
    :return: A dictionary with domain names as keys and their availability as values.
    """
    # Namecheap API endpoint for checking domain availability
    # using the sandbox has.... questionable results
    endpoint = "https://api.sandbox.namecheap.com/xml.response"
    # Prepare the parameters for the API request
    params = {
        'ApiUser': NAMECHEAP_API_USER,
        'ApiKey': NAMECHEAP_API_KEY,
        'UserName': NAMECHEAP_API_USER,
        'ClientIp': NAMECHEAP_API_IP,
        'Command': 'namecheap.domains.check',
        'DomainList': ','.join(domains)
    }
    
    # Initialize the result dictionary
    results = {}
    try:
        # Make the request to Namecheap API
        response = requests.get(endpoint, params=params)
        response.raise_for_status()  # Raise an error for bad responses

        # Parse the XML response (simplified for demonstration)
        from xml.etree import ElementTree as ET
        tree = ET.fromstring(response.content)
        # Iterate through each domain check result
        for domain in tree.findall('.//{http://api.namecheap.com/xml.response}DomainCheckResult'):
            print(domain.attrib['Domain'], domain.attrib['Available'], domain.attrib['IsPremiumName'], domain.attrib['PremiumRegistrationPrice'])
            domain_name = domain.attrib['Domain']
            available = domain.attrib['Available'] == 'true'
            premium = domain.attrib.get('IsPremiumName', 'false') == 'true'
            premium_price = domain.attrib.get('PremiumRegistrationPrice', '0.00') 
            # Convert premium_price to a float or other desired format
            try:
                premium_price = float(premium_price)
            except ValueError:
                premium_price = None  # Handle conversion error
            results[domain_name] = [available, premium, premium_price]
    except requests.RequestException as e:
        print(f"Error checking domain availability: {e}")
    
    return results
    
def cache_result(domain_name, domain_info):
    domain_availability = domain_info[0]
    domain_is_premium = domain_info[1]
    domain_premium_price = domain_info[2]

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO domains (domain_name, available, premium, premium_price) VALUES (?, ?, ?, ?)",\
                    (domain_name, domain_availability, domain_is_premium, domain_premium_price))
    conn.commit()
    conn.close()

def generate_domains(prefix="", suffix="", must_contain=[], exclude=[], length=5, num_results=10):
    # generate domain names that follow the consonant/vowel/consonant pattern for ease of speaking
    vowels = 'aeiou'
    consonants = ''.join(set(string.ascii_lowercase) - set(vowels))
    results = set()
    random_part_length = length - len(prefix) - len(suffix)
    max_attempts = num_results * 5000  # Increased attempts due to added complexity
    attempts = 0

    # Determine the starting character type based on the last letter of the prefix
    last_char_type = None
    if prefix and prefix[-1] in vowels:
        last_char_type = 'consonant'  # Start with a consonant if the prefix ends with a vowel
    elif prefix and prefix[-1] in consonants:
        last_char_type = 'vowel'  # Start with a vowel if the prefix ends with a consonant

    while len(results) < num_results and attempts < max_attempts:
        random_part = ''
        for _ in range(random_part_length):
            if last_char_type == 'vowel' or last_char_type is None:
                char = random.choice(consonants)
                last_char_type = 'consonant'
            else:
                char = random.choice(vowels)
                last_char_type = 'vowel'
            random_part += char

        domain = f'{prefix}{random_part}{suffix}.com'
        if all(substring in domain for substring in must_contain) and \
           not any(substring in domain for substring in exclude) and \
           all(c in string.ascii_lowercase for c in random_part):
            results.add(domain)
        attempts += 1

    result_list = list(results)
    if len(result_list) > 0:
        result_list.sort()

    return result_list


@app.route('/toggle_favorite', methods=['POST'])
def toggle_favorite():
    # Attempt to retrieve the domain name from the form data
    domain_name = request.form.get('domainName')
    if not domain_name:
        # If domain name is not provided, return an error response
        return jsonify({'success': False, 'message': 'Domain name is required.'}), 400

    try:
        # Establish a connection to the database
        with sqlite3.connect(DATABASE_PATH) as conn:
            cur = conn.cursor()

            # Fetch the current favorite status for the given domain
            cur.execute("SELECT favorite FROM domains WHERE domain_name = ?", (domain_name,))
            result = cur.fetchone()
            if result is None:
                # If the domain does not exist, return an error response
                print("domain not found")
                return jsonify({'success': False, 'message': 'Domain not found'}), 404

            current_favorite_status = result[0]

            # Toggle the favorite status
            new_favorite_status = 0 if current_favorite_status else 1

            # Execute the update query to set the domain as favorite
            cur.execute("UPDATE domains SET favorite = ? WHERE domain_name = ?", (new_favorite_status, domain_name))
            # Commit the changes to the database
            conn.commit()
            # If everything is successful, return a success response
            return jsonify({'success': True, 'message': 'Domain favorited successfully', 'isFavorite':new_favorite_status})
    except sqlite3.Error as e:
        # In case of a database error, return an error response
        print("database error occured:",str(e))
        return jsonify({'success': False, 'message': 'Database error occurred.', 'error': str(e)}), 500
    finally:
        # Ensure that the database connection is closed
        if conn:
            conn.close()
    
@app.route('/favorites', methods=['GET'])
def get_favorites():
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cur = conn.cursor()
            # Execute the SQL query to select domains where 'favorite' is set to 1
            cur.execute("SELECT domain_name FROM domains WHERE favorite = 1")
            # Fetch all matching records
            favorites = cur.fetchall()
            # Use 'render_template' to display the favorites on a webpage
            return render_template('favorites.html', favorites=favorites)
    except sqlite3.Error as e:
        # In case of a database error, log the error and return an error message
        return jsonify({'success':False, 'message': "An error occurred while fetching favorites."}), 500

@app.route('/all_domains', methods=['GET'])
def get_domains():
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cur = conn.cursor()
            # Fetch all domains with their availability and favorite status
            cur.execute("SELECT domain_name, available, favorite FROM domains")
            # Construct a list of dictionaries for each domain
            domains = [{'name': row[0], 'available': row[1], 'favorited': row[2]} for row in cur.fetchall()]
            # Render the template with the domains data
            return render_template('all_domains.html', all_domains=domains)
    except sqlite3.Error as e:
        # Log the error (consider using a logging framework or print for simplicity)
        print(f"Database error: {e}")
        # Return an error message or render an error template
        return jsonify({'success':False, 'message': "An error occurred while fetching the domain information."}), 500

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':

        # Domain Generation
        prefix = request.form.get('domain_prefix', '')
        suffix = request.form.get('domain_suffix', '')
        must_contain = request.form.get('must_contain', '').split(',') if request.form.get('must_contain') else []
        exclude = request.form.get('exclude', '').split(',') if request.form.get('exclude') else []
        length = int(request.form.get('length', 5) or 5)
        num_results = int(request.form.get('num_results', 50) or 50)

        results = generate_domains(prefix, suffix, must_contain, exclude, length, num_results)

        # Check availability and update results

        check_list = []
        availabilities = []

        for _,domain in enumerate(results):
            # Check database cache first
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT available FROM domains WHERE domain_name=?", (domain,))
            result = cursor.fetchone()
            conn.close()

            if result is not None:
                available = bool(result[0])
            else:
                check_list.append(domain)

        # Assuming check_domain_availability is a function that returns a dictionary
        # where each key is a domain and its value is the availability (boolean).
        domain_results = check_domain_availability(check_list)

        if len(domain_results) == 0:
            # There was an error with getting the results
            return render_template('index.html')
        # Use list comprehension to build the availabilities list.
        availabilities = [domain_results.get(domain)[0] for domain in check_list]

        # Cache results. Assuming cache_result() is a function that caches domain availability.
        for domain in check_list:
            cache_result(domain, domain_results.get(domain, [False, False, 0.0]))

        # Use zip in the template rendering to pair each domain with its availability.
        return render_template('index.html', results=zip(check_list, availabilities))

    else:
        return render_template('index.html')

if __name__ == '__main__':
    create_database() 
    app.run(debug=True) 