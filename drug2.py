import psycopg2

def connect_db():
    return psycopg2.connect(
        host="localhost",
        database="emergency_medical_db",
        user="postgres", 
        password="1234",
        port="5432"
    )

def find_interactions(cursor, drug_name):
    drug_name = drug_name.lower().strip()

    query = """
    SELECT 
        CASE 
            WHEN drug1 = %s THEN drug2
            ELSE drug1
        END AS interacting_drug
    FROM drug_interactions
    WHERE drug1 = %s OR drug2 = %s;
    """

    cursor.execute(query, (drug_name, drug_name, drug_name))
    results = cursor.fetchall()

    if results:
        print(f"\nInteractions for '{drug_name}':")
        for row in set(results):
            print(row[0])
    else:
        print("No interactions found.")

if __name__ == "__main__":
    print("Connecting to database...")

    try:
        conn = connect_db()
        cursor = conn.cursor()
        print("Connected to PostgreSQL!\n")

        while True:
            drug = input("Enter Drug Name (or type 'exit' to quit): ")

            if drug.lower() == 'exit':
                print("Exiting program")
                break

            find_interactions(cursor, drug)

    except Exception as e:
        print("Error:", e)

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()