from database.neo4j import close_neo4j_driver
from services.neo4j_skill_graph_service import initialize_skill_graph


def main() -> None:
    try:
        result = initialize_skill_graph()
        print(
            "Neo4j skill graph seeded: "
            f"{len(result['source_files'])} source files, "
            f"{result['skill_count']} skills, "
            f"{result['alias_count']} aliases, "
            f"{result['relationship_count']} skill relationships, "
            f"{result['role_count']} roles, "
            f"{result['role_requirement_count']} role requirements."
        )
    finally:
        close_neo4j_driver()


if __name__ == "__main__":
    main()
