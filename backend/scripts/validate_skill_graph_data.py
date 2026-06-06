from services.skill_graph_dataset_service import validate_skill_graph_dataset


def main() -> None:
    result = validate_skill_graph_dataset()
    print(
        "Skill graph data is valid: "
        f"{result['files']} files, "
        f"{result['skills']} skills, "
        f"{result['aliases']} normalized terms, "
        f"{result['relationships']} skill relationships, "
        f"{result['roles']} roles, "
        f"{result['role_requirements']} role requirements."
    )


if __name__ == "__main__":
    main()
