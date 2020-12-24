from typing import Set


class Skill:
    def __init__(self, name: str, level: int = 0):
        self.name = name
        self.level = level

    def __str__(self):
        return "[" + " ".join([self.name, "-", "Lvl", str(self.level)]) + "]"


class SkillSet(Set[Skill]):
    def __init__(self, *args: Set[Skill]):
        super().__init__(*args)

    def __str__(self):
        return "{" + ", ".join([str(skill) for skill in self]) + "}"


class PlayerSystem:
    """ Represents a playable character """
    def __init__(self, base_skills: list[str] = None):
        self.skills = SkillSet()

        if base_skills is None:
            base_skills = []
        for skill in base_skills:
            self.skills.add(Skill(skill))


if __name__ == "__main__":
    ps = PlayerSystem(["Strength", "Dexterity", "Intelligence", "Wisdom", "Charisma"])
    print(ps.skills)