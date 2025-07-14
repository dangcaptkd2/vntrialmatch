import psycopg2

from src.config import config


def get_criteria_by_nct_id(nct_id: str) -> str:
    """
    Retrieve eligibility criteria for given NCT ID from ctgov.eligibilities table.

    Args:
        nct_ids (str): List of NCT IDs to query

    Returns:
        List[Dict]: List of criteria dictionaries with nct_id and criteria information
    """
    if not nct_id:
        return ""

    try:
        pg_conn_params = {
            "host": config.SQL_HOST,
            "port": config.SQL_PORT,
            "dbname": config.SQL_DATABASE_AACT,
            "user": config.SQL_USERNAME,
            "password": config.SQL_PASSWORD,
        }
        conn = psycopg2.connect(**pg_conn_params, connect_timeout=300)  # type: ignore
        cursor = conn.cursor()

        query = """
            SELECT criteria
            FROM ctgov.eligibilities 
            WHERE nct_id = %s
            LIMIT 1;
        """

        cursor.execute(query, (nct_id,))
        results = cursor.fetchall()

        # Convert result to a string
        criteria_str = results[0][0]

        cursor.close()
        conn.close()

        return criteria_str

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return ""
    except Exception as e:
        print(f"Error retrieving criteria: {e}")
        return ""


def parse_clinical_trial_criteria(criteria_text):
    """
    Parse clinical trial criteria text into a list of criteria strings.

    Args:
        criteria_text (str): The text containing inclusion and exclusion criteria.

    Returns:
        list: A list of criteria strings in format "inclusion: text" or "exclusion: text".
    """
    criteria_list = []
    current_section = "inclusion"  # Default to inclusion

    # Split the text into lines and process each line
    lines = criteria_text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Identify section headers
        if line.lower().startswith("inclusion criteria:"):
            current_section = "inclusion"
            continue
        elif line.lower().startswith("exclusion criteria:"):
            current_section = "exclusion"
            continue

        criteria_text = line.strip()
        if criteria_text:
            criteria_list.append(f"{current_section}: {criteria_text}")

    return criteria_list


if __name__ == "__main__":
    sample_criteria = get_criteria_by_nct_id("NCT05254184")
    print(sample_criteria)
    print(parse_clinical_trial_criteria(sample_criteria))
