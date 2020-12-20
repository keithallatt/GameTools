
class NPC:
    def __init__(self, name, **kwargs):
        self.name = name
        self.conversation = kwargs.get("conversation", [("...", {})])

        self.goodbye = "Goodbye!"
        self.confusion = "Sorry, I don't know what you mean."

    def talk(self):
        line = 0

        while True:
            prompt, next_options = self.conversation[line]
            if prompt is not None and prompt != "":
                print(prompt, "( " + "/".join(next_options.keys()) + ")"
                      if len(next_options) != 0 else "")
            if len(next_options) != 0:
                response = input("> ")
                if response not in next_options.keys():
                    if response == "leave":
                        print(self.goodbye)
                        break
                    print(self.confusion)
                    continue
                else:
                    line = next_options[response]
            else:
                break


if __name__ == "__main__":
    conversation = [("Yes or no, or repeat?", {"y": 1, "n": 2, "r": 0}),
                    ("You said yes. Again?", {"y": 0, "n": 3}),
                    ("You said no. Again?", {"y": 0, "n": 3}),
                    ("Goodbye!", {})]

    npc = NPC("Character 1", conversation=conversation)
    npc.talk()
