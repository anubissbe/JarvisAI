from neo4j import GraphDatabase

# Try different passwords
passwords = ["Loebas0128", "neo4j", "password"]

for password in passwords:
    print(f"Trying password: {password}")
    try:
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", password))
        with driver.session() as session:
            result = session.run("RETURN 'Connected!' as message")
            print(result.single()["message"])
        driver.close()
        print("Success!")
        break
    except Exception as e:
        print(f"Failed: {str(e)}")
