from NPCSystem.npc_conversation import NPC
from InventorySystem.inventory import ItemFilter, Item, InventorySystem


class ShopKeeper(NPC):
    """ A vendor or shop keeper, used to sell the player items, and buy unwanted stock """
    def __init__(self, name, item_list: list[Item]):
        """ Build a shop keeper from a name and a list of items they have """
        super().__init__(name)
        self.inv = InventorySystem(remove_on_0=False, item_filter=ItemFilter.FILTER_ACCEPT_ALL)

        for item in item_list:
            self.inv += item

        self.conversation = [
            ("Good day!! How can I help you? "
             "Are you here to buy or sell?", {"b": 2, "s": 1}),
            ("Sorry, I can't buy anything from you at this moment", {}),
            (self.see_stock, self.buy_stock),
            ("Goodbye!", {})
        ]

    def see_stock(self):
        """ Allow the player to see the items in the shop """
        shop_repr = self.inv.__str__()
        shop_name = "< %s's Shop >" % self.name
        return shop_name + "\n" + shop_repr

    def buy_stock(self):
        """ Set up the player to buy items """
        while True:
            try:
                response = input("What would you like? (1-%d)\n>> " %
                                 self.inv.num_slots())
                response = int(response) - 1
                break
            except ValueError:
                pass

        item = self.inv.get_slots()[response].copy(quantity=1)

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
        """ Set up the player to sell items """

        pass


if __name__ == "__main__":
    it_lst = [
        8 * Item("Apple", price=5),
        10 * Item("Orange", price=7),
        15 * Item("Banana", price=18)
    ]

    shop_keep = ShopKeeper("Fruit Vendor", it_lst)

    shop_keep.talk()
