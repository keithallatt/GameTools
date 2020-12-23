from NPCSystem.npc_conversation import *
from InventorySystem.inventory import *


class ShopKeeper(NPC):
    def __init__(self, name, item_list: list[Item]):
        super().__init__(name)
        self.inv = InventorySystem(remove_on_0=False)

        for item in item_list:
            self.inv += item

        self.conversation = [
            ("Good day!! How can I help you? "
             "Are you here to buy or sell?", {"b": 1, "s": 2}),
            ("Take a look at what I have!", {"k": 3}),
            ("Sorry, I can't buy anything from you at this moment", {}),
            (self.see_stock, self.buy_stock),
            ("Goodbye!", {})
        ]

    def see_stock(self):
        shop_repr = self.inv.__str__()
        shop_name = "< %s's Shop >" % self.name
        return shop_name + "\n" + shop_repr

    def buy_stock(self):
        response = None
        while True:
            try:
                response = input("What would you like? (1-%d)\n>> " %
                                 self.inv.num_slots())
                response = int(response) - 1
                break
            except ValueError:
                pass

        item = self.inv.get_slots()[response].copy(quantity=1)

        number = None
        while True:
            try:
                number = input(f"How many {item.name.lower()}s would you like?\n>> ")
                number = int(number)
                break
            except ValueError:
                pass
        print(f"So you want {number} {item.name.lower()}{'s' if number != 1 else ''}, huh? (y/n)")
        confirmation = input(">> ")

        while True:
            if confirmation == "y":
                self.sell_item(number * item)
                return 4
            if confirmation == "n":
                return 4
            print(self.confusion)
            confirmation = input(">> ")

    def sell_item(self, item_quantified):
        pass

if __name__ == "__main__":
    it_lst = [
        Item("Apple", quantity=8, price=5),
        Item("Orange", quantity=15, price=7),
        Item("Banana", quantity=10, price=18)
    ]

    shopkeep = ShopKeeper("Moni Spender", it_lst)

    shopkeep.talk()

