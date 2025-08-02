import re
from typing import Dict, List


def extract_criteria(text: str) -> Dict[str, List[str]]:
    # Normalize bullets
    text = text.replace("•", "*")

    # Split into inclusion and exclusion
    inclusion_text, exclusion_text = "", ""
    match = re.split(r"\bExclusion Criteria\b\s*:?", text, flags=re.IGNORECASE)
    if len(match) == 2:
        inclusion_text = match[0]
        exclusion_text = match[1]
    else:
        inclusion_text = text

    def parse_criteria(block: str) -> List[str]:
        lines = block.strip().split("\n")
        criteria = []
        buffer = ""

        for line in lines:
            line = line.strip()

            # Start of a new criterion
            if re.match(r"^[-*•]|\d+\.", line):
                if buffer:
                    criteria.append(buffer.strip())
                    buffer = ""
                buffer = re.sub(r"^[-*•] ?|\d+\.\s*", "", line)
            elif line:  # Continuation of previous line
                if buffer:
                    buffer += " " + line
                else:
                    buffer = line  # In case it starts directly without a bullet
        if buffer:
            criteria.append(buffer.strip())
        return criteria

    return {
        "inclusion_criteria": parse_criteria(inclusion_text),
        "exclusion_criteria": parse_criteria(exclusion_text),
    }


if __name__ == "__main__":
    import psycopg2

    from src.settings import settings

    pg_conn_params = {
        "host": settings.sql_host,
        "port": settings.sql_port,
        "dbname": settings.sql_database_aact,
        "user": settings.sql_username,
        "password": settings.sql_password,
    }
    conn = psycopg2.connect(**pg_conn_params, connect_timeout=300)  # type: ignore
    cursor = conn.cursor()
    query = """
    select criteria from ctgov.eligibilities
    where nct_id='NCT05254184'
    """
    cursor.execute(query)
    result = cursor.fetchone()
    print(extract_criteria(result[0]))
