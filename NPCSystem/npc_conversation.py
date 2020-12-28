
class NPC:
    """ Represents a generic Non Player Character """
    def __init__(self, name, **kwargs):
        """ Create a basic npc with a rudimentary conversation system """
        self.name = name
        self.conversation = kwargs.get("conversation", [("...", {})])

        self.goodbye = kwargs.get("goodbye", "Goodbye!")
        self.confusion = kwargs.get("confusion", "Sorry, I don't know what you mean.")

    def talk(self):
        """ Start a conversation with the NPC """
        line = 0

        while True:
            prompt, next_options = self.conversation[line]
            if prompt is not None and prompt != "":
                print(prompt if type(prompt) == str
                      else prompt(),
                      "(" + "/".join(next_options.keys()) + ")"
                      if type(next_options) is dict and len(next_options) != 0
                      else "")
            if type(next_options) is dict:
                if len(next_options) != 0:
                    response = input(">> ")
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
            elif callable(next_options):
                # next option is a function
                line = next_options()


if __name__ == "__main__":
    npc = NPC("Mary")
    npc.talk()
