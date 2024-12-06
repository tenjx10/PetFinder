from dotenv import load_dotenv
from flask import Flask, jsonify, make_response, Response, request

from cat_curious.models import Cat
from cat_curious.utils.sql_utils import check_database_connection, check_table_exists
from cat_curious.utils.cat_affection_utils import get_affection_level
from cat_curious.utils.cat_facts_utils import get_random_cat_facts
from cat_curious.utils.cat_info_utils import get_cat_pic 

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
cat_model = Cat()

####################################################
#
# Healthchecks
#
####################################################

@app.route('/api/health', methods=['GET'])
def healthcheck() -> Response:
    """
    Health check route to verify the service is running.

    Returns:
        JSON response indicating the health status of the service.
    """
    app.logger.info('Health check')
    return make_response(jsonify({'status': 'healthy'}), 200)


@app.route('/api/db-check', methods=['GET'])
def db_check() -> Response:
    """
    Route to check if the database connection and songs table are functional.

    Returns:
        JSON response indicating the database health status.
    Raises:
        404 error if there is an issue with the database.
    """
    try:
        app.logger.info("Checking database connection...")
        check_database_connection()
        app.logger.info("Database connection is OK.")
        app.logger.info("Checking if songs table exists...")
        check_table_exists("songs")
        app.logger.info("songs table exists.")
        return make_response(jsonify({'database_status': 'healthy'}), 200)
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 404)

##########################################################
#
# Cat Management
#
##########################################################

@app.route('/api/create-cat', methods=['POST'])
def add_cat() -> Response:
    """
    Route to add a new cat to the database.

    Expected JSON Input:
        - name (str): The cat's name.
        - breed (str): The cat's breed. 
        - age (int): The cat's age. 
        - weight (int): The cat's weight. 

    Returns:
        JSON response indicating the success of the cat addition.
    Raises:
        400 error if input validation fails.
        500 error if there is an issue adding the cat to the database.
    """
    app.logger.info('Adding a new cat to the database')
    try:
        data = request.get_json()

        name = data.get('name')
        breed = data.get('breed')
        age = data.get('age')
        weight = data.get('weight')

        if not name or not breed or age is None or weight is None:
            return make_response(jsonify({'error': 'Invalid input, all fields are required with valid values'}), 400)

        # Add the cat to the database
        app.logger.info("Adding cat: %s (%s, Age: %d, Weight: %d)", name, breed, age, weight)
        cat_model.create_cat(name=name, breed=breed, age=age, weight=weight)
        app.logger.info("Cat added to the database: %s", name)
        return make_response(jsonify({'status': 'success', 'cat': name}), 201)
    except Exception as e:
        app.logger.error("Failed to add cat: %s", str(e))
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/api/clear-cats', methods=['DELETE'])
def clear_cats() -> Response:
    """
    Route to clear all cats from the database.

    Returns:
        JSON response indicating success of the operation or error message.
    """
    try:
        app.logger.info("Clearing all cats from the database")
        cat_model.clear_cats()
        return make_response(jsonify({'status': 'success'}), 200)
    except Exception as e:
        app.logger.error(f"Error clearing catalog: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/api/delete-cat/<int:cat_id>', methods=['DELETE'])
def delete_cat(cat_id: int) -> Response:
    """
    Route to delete a cat by its ID (soft delete).

    Path Parameter:
        - cat_id (int): The ID of the cat to delete.

    Returns:
        JSON response indicating success of the operation or error message.
    """
    try:
        app.logger.info(f"Deleting cat by ID: {cat_id}")
        cat_model.delete_cat(cat_id)
        return make_response(jsonify({'status': 'success'}), 200)
    except Exception as e:
        app.logger.error(f"Error deleting song: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/api/get-cat-by-id/<int:cat_id>', methods=['GET'])
def get_cat_by_id(cat_id: int) -> Response:
    """
    Route to retrieve a cat by its ID.

    Path Parameter:
        - cat_id (int): The ID of the cat.

    Returns:
        JSON response with the cat details or error message.
    """
    try:
        app.logger.info(f"Retrieving cat by ID: {cat_id}")
        cat = cat_model.get_cat_by_id(cat_id)
        return make_response(jsonify({'status': 'success', 'cat': cat}), 200)
    except Exception as e:
        app.logger.error(f"Error retrieving cat by ID: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/api/get-cat-by-name/<str:cat_name>', methods=['GET'])
def get_cat_by_name(cat_name: str) -> Response:
    """
    Route to retrieve a cat by its name.

    Path Parameter:
        - cat_name (str): The name of the cat.

    Returns:
        JSON response with the cat details or error message.
    """
    try:
        app.logger.info(f"Retrieving cat by name: {cat_name}")
        cat = cat_model.get_cat_by_name(cat_name)
        return make_response(jsonify({'status': 'success', 'cat': cat}), 200)
    except Exception as e:
        app.logger.error(f"Error retrieving cat by name: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

####################################################
#
# Cat Information. routes on exist for functions already implemented!
#
####################################################

@app.route('/api/get-affection-level/<string:breed>', methods=['GET'])
def get_affection_level(breed: str) -> Response:
    """
    Route to fetch the affection level of a cat breed using TheCatAPI.

    Path Parameter:
        - breed (str): The cat breed to get affection level for.

    Returns:
        JSON response indicating the affection level or error message.
    """
    try:
        app.logger.info(f"Fetching affection level for breed: {breed}")
        url = f"https://api.thecatapi.com/v1/images/search?limit=1&breed_ids={breed}&api_key={KEY}"
        response = request.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data and "breeds" in data[0]:
            affection_level = data[0]["breeds"][0]["affection_level"]
            app.logger.info(f"Received affection level: {affection_level}")
            return make_response(jsonify({'status': 'success', 'breed': breed, 'affection_level': affection_level}), 200)
        else:
            app.logger.error("No breed information received from API.")
            return make_response(jsonify({'error': 'No breed information received from API.'}), 500)

    except request.exceptions.Timeout:
        app.logger.error("Request to TheCatAPI timed out.")
        return make_response(jsonify({'error': 'Request to TheCatAPI timed out.'}), 504)
    except request.exceptions.RequestException as e:
        app.logger.error(f"Request to TheCatAPI failed: {e}")
        return make_response(jsonify({'error': f'Request failed: {e}'}), 502)
    except Exception as e:
        app.logger.error(f"Error retrieving affection level of cat: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/api/get-cat-facts/<int:num_facts>', methods=['GET'])
def get_cat_facts(num_facts: int) -> Response:
    """
    Route to fetch a certain number of random cat facts.

    Path Parameter:
        - num_facts (int): The number of cat facts to retrieve.

    Returns:
        JSON response with the list of cat facts or error message.
    """
    if num_facts <= 0:
        app.logger.error("Invalid number of cat facts requested: %d", num_facts)
        return make_response(jsonify({'error': 'Num_facts must be a positive integer.'}), 400)

    url = f"https://catfact.ninja/facts?limit={num_facts}"
    try:
        app.logger.info("Fetching %d random cat facts from %s", num_facts, url)
        response = request.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        if "data" not in data:
            app.logger.error("Invalid response from Cat Facts API: %s", data)
            return make_response(jsonify({'error': 'Invalid response from Cat Facts API.'}), 500)

        facts = [fact["fact"] for fact in data["data"]]

        app.logger.info("Fetched %d cat facts.", len(facts))
        return make_response(jsonify({'status': 'success', 'facts': facts}), 200)

    except request.exceptions.Timeout:
        app.logger.error("Request to Cat Facts API timed out.")
        return make_response(jsonify({'error': 'Request to Cat Facts API timed out.'}), 504)

    except request.exceptions.RequestException as e:
        app.logger.error("Request to Cat Facts API failed: %s", e)
        return make_response(jsonify({'error': f'Request to Cat Facts API failed: {e}'}), 502)

    except Exception as e:
        app.logger.error("Error retrieving random number of cat facts: %s", e)
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/api/get-cat-pic/<string:breed>', methods=['GET'])
def get_cat_picture(breed: str) -> Response:
    """
    Route to fetch a cat picture for a cat breed.

    Path Parameter:
        - breed (str): The cat's breed name.

    Returns:
        JSON response with the URL of cat picture or error message.
    """
    url = f"https://api.thecatapi.com/v1/images/search?limit=1&breed_ids={breed}&api_key={KEY}"
    try:
        app.logger.info(f"Fetching cat picture for breed: {breed} from {url}")
        response = request.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()
        if data and "url" in data[0]:
            cat_pic_url = data[0]["url"]
            app.logger.info(f"Fetched cat picture URL: {cat_pic_url}")
            return make_response(jsonify({'status': 'success', 'cat_picture_url': cat_pic_url}), 200)
        else:
            app.logger.error("Data received from TheCatAPI not received.")
            return make_response(jsonify({'error': 'Data received from TheCatAPI not received.'}), 500)

    except request.exceptions.Timeout:
        app.logger.error("Request to TheCatAPI timed out.")
        return make_response(jsonify({'error': 'Request to TheCatAPI timed out.'}), 504)

    except request.exceptions.RequestException as e:
        app.logger.error(f"Request to TheCatAPI failed: {e}")
        return make_response(jsonify({'error': f'Request to TheCatAPI failed: {e}'}), 502)

    except Exception as e:
        app.logger.error(f"Error retrieving cat picture: {e}")
        return make_response(jsonify({'error': str(e)}), 500)



