import smartpy as sp

class WorldWarTez(sp.Contract):

    def __init__(self, manager_address):
        self.init(
            gladiators = sp.big_map(tkey = sp.TAddress, tvalue = sp.TRecord(strength = sp.TNat, wins = sp.TNat, losses = sp.TNat, ties = sp.TNat, avatar_id = sp.TNat, nickname = sp.TString, last_power_up = sp.TTimestamp, equipment = sp.TString)), 
            manager = sp.address(manager_address), 
            countries = sp.big_map(tkey = sp.TString, tvalue = sp.TRecord(name = sp.TString, description = sp.TString, champion = sp.TAddress)),
            equipment = sp.big_map(tkey = sp.TString, tvalue = sp.TRecord(name = sp.TString, description = sp.TString, power_bonus = sp.TNat, bonus_country = sp.TString, price = sp.TMutez)), 
            avatars = sp.big_map(tkey = sp.TNat, tvalue = sp.TRecord(name = sp.TString, description = sp.TString, image_url = sp.TString, current_owner = sp.TAddress)), 
            avatar_sales = sp.big_map(tkey = sp.TNat, tvalue = sp.TRecord(price = sp.TMutez, seller = sp.TAddress)), 
            current_avatar_id = sp.nat(0),
            user_token_balances = sp.big_map(tkey = sp.TAddress, tvalue = sp.TNat), 
            token_address = sp.address("KT1GaR1CmFoTTjqRwYSE8WdpBuxuviKGbcqs"),
            dex_address = sp.address("KT1GaR1CmFoTTjqRwYSE8WdpBuxuviKGbcqs"),
            token_bonus_divider = sp.nat(1000000),
            power_up_time_limit = sp.int(60),
            metadata = sp.big_map({sp.string(""): sp.utils.bytes_of_string("ipfs://QmZF9t7NHHtZFbpAfVqQvRA2GtvFznEMwaoja46YL2DCG4")}))

    @sp.entry_point
    def change_manager(self, new_manager_address):
        sp.verify(
            self.data.manager == sp.sender, 
            message = "Error: non manager call"
        )
        self.data.manager = new_manager_address

    @sp.entry_point
    def set_metadata(self, json_string_bytes):
        sp.verify(
            self.data.manager == sp.sender, 
            message = "Error: non manager call"
        )
        self.data.metadata[""] = json_string_bytes
        
    @sp.entry_point
    def self_update_nickname(self, new_nickname):
        self.data.gladiators[sp.sender].nickname = new_nickname
        
    @sp.entry_point
    def manager_override_nickname(self, address, new_nickname):
        sp.verify(
            self.data.manager == sp.sender, 
            message = "Error: non manager call"
        )
        self.data.gladiators[address].nickname = new_nickname
        
    @sp.entry_point
    def change_defaults(self, new_token_address, new_dex_address, new_token_bonus_divider, new_power_up_time_limit):
        sp.verify(
            self.data.manager == sp.sender, 
            message = "Error: non manager call"
        )
        sp.if new_dex_address != self.data.dex_address:
            self.data.dex_address = new_dex_address
        sp.if new_token_address != self.data.token_address:
            self.data.token_address = new_token_address
        sp.if new_token_bonus_divider != self.data.token_bonus_divider:
            self.data.token_bonus_divider = new_token_bonus_divider
        sp.if new_power_up_time_limit != self.data.power_up_time_limit:
            self.data.power_up_time_limit = new_power_up_time_limit
    
    @sp.entry_point
    def create_or_reset_gladiator(self, nickname):
        address = sp.sender
        self.data.gladiators[address] = sp.record(
            strength = sp.nat(1),
            wins = sp.nat(0),
            losses = sp.nat(0),
            ties = sp.nat(0),
            avatar_id = sp.nat(0),
            nickname = nickname,
            last_power_up = sp.timestamp_from_utc(2021, 1, 1, 0, 0, 0),
            equipment = "None"
        )
        self.data.user_token_balances[address] = 0
        
    @sp.entry_point
    def add_country(self, name, description):
        sp.verify(
            self.data.manager == sp.sender, 
            message = "Error: non manager call"
        )
        self.data.countries[name] = sp.record(
            name = name,
            description = description,
            champion = self.data.manager
        )

    @sp.entry_point
    def add_avatar(self, name, description, image_url, price):
        sp.verify(
            self.data.manager == sp.sender, 
            message = "Error: non manager call"
        )
        new_id = self.data.current_avatar_id + sp.nat(1)
        self.data.current_avatar_id = new_id
        manager = self.data.manager
        self.data.avatars[self.data.current_avatar_id] = sp.record(name = name, description = description, image_url = image_url, current_owner = manager)
        self.data.avatar_sales[self.data.current_avatar_id] = sp.record(price = sp.utils.nat_to_tez(price), seller = self.data.manager)

    @sp.entry_point
    def add_equipment(self, name, description, power_bonus, bonus_country, price):
        sp.verify(
            self.data.manager == sp.sender, 
            message = "Error: non manager call"
        )
        self.data.equipment[name] = sp.record(name = name, description = description, power_bonus = power_bonus, bonus_country = bonus_country, price = sp.utils.nat_to_tez(price))
        
    @sp.entry_point
    def new_avatar_sale(self, price):
        sp.verify(
            self.data.gladiators[sp.sender].avatar_id > sp.nat(0), 
            message = "You do not own an avatar!"
        )
        sp.verify(
            price >= 100, 
            message = "Minimum price is 100 Tez!"
        )
        avatar_id = self.data.gladiators[sp.sender].avatar_id
        self.data.avatar_sales[avatar_id] = sp.record(price = sp.utils.nat_to_tez(price), seller = sp.sender)
        
    @sp.entry_point
    def cancel_avatar_sale(self):
        avatar_id = self.data.gladiators[sp.sender].avatar_id
        sp.verify(
            avatar_id != 0,
            message = "You don't own an avatar!"
        )
        sp.verify(
            self.data.avatar_sales.contains(avatar_id), 
            message = "You have no pending avatar sale!"
        )
        del self.data.avatar_sales[avatar_id]

    @sp.entry_point
    def transfer_avatar(self, target_address):
        sp.verify(
            self.data.gladiators[sp.sender].avatar_id > sp.nat(0), 
            message = "You do not own an avatar!"
        )
        sp.verify(
            self.data.gladiators[target_address].avatar_id == sp.nat(0), 
            message = "Target already has an avatar!"
        )
        avatar_id = self.data.gladiators[sp.sender].avatar_id
        self.data.gladiators[sp.sender].avatar_id = sp.nat(0)
        self.data.avatars[avatar_id].current_owner = target_address
        self.data.gladiators[target_address].avatar_id = avatar_id
        del self.data.avatar_sales[avatar_id]

    @sp.entry_point
    def manager_transfer_avatar(self, avatar_id, target_address):
        sp.verify(
            self.data.avatars[avatar_id].current_owner == self.data.manager, 
            message = "Manager does not own this avatar!"
        )
        sp.verify(
            self.data.gladiators[target_address].avatar_id == sp.nat(0), 
            message = "Target already has an avatar!"
        )
        self.data.avatars[avatar_id].current_owner = target_address
        self.data.gladiators[target_address].avatar_id = avatar_id
        del self.data.avatar_sales[avatar_id]

    @sp.entry_point
    def purchase_avatar(self, avatar_id):
        sp.verify(
            self.data.gladiators[sp.sender].avatar_id == sp.nat(0), 
            message = "You already own an avatar!"
        )
        sp.verify(
            self.data.avatar_sales.contains(avatar_id), 
            message = "That avatar is not for sale!"
        )
        sp.verify(
            sp.amount == self.data.avatar_sales[avatar_id].price, 
            message = "Incorrect price!"
        )
        sp.send(self.data.dex_address, sp.utils.nat_to_tez(50))
        sp.send(self.data.avatar_sales[avatar_id].seller, self.data.avatar_sales[avatar_id].price - sp.utils.nat_to_tez(50))
        self.data.gladiators[self.data.avatars[avatar_id].current_owner].avatar_id = sp.nat(0)
        self.data.avatars[avatar_id].current_owner = sp.sender
        self.data.gladiators[sp.sender].avatar_id = avatar_id
        del self.data.avatar_sales[avatar_id]

    @sp.entry_point
    def purchase_equipment(self, equipment_name):
        sp.verify(
            self.data.equipment.contains(equipment_name), 
            message = "That equipment doesn't exist!"
        )
        sp.verify(
            sp.amount == self.data.equipment[equipment_name].price, 
            message = "Incorrect price!"
        )
        self.data.gladiators[sp.sender].equipment = equipment_name
        sp.send(self.data.dex_address, sp.amount)
        
    @sp.entry_point
    def power_up(self):
        last_power_up = self.data.gladiators[sp.sender].last_power_up
        seconds_passed = sp.now - last_power_up
        sp.verify(
            seconds_passed > self.data.power_up_time_limit, 
            message = "Error: It is too soon to train again!"
        )
        self.data.gladiators[sp.sender].strength += 1
        self.data.gladiators[sp.sender].last_power_up = sp.now

    @sp.entry_point
    def withdraw(self):
        sp.verify(self.data.manager == sp.sender)
        sp.send(self.data.manager, sp.balance)

    @sp.entry_point
    def fight(self, country_name):
        sp.verify(
            self.data.countries.contains(country_name), 
            message = "Please enter a valid country!"
        )
        sp.verify(
            self.data.countries[country_name].champion != sp.sender, 
            message = "You cannot fight yourself!"
        )
        sp.verify(
            self.data.gladiators.contains(sp.sender),  
            message = "You must create a gladiator first!"
        )
        self.requestBalanceUpdate()

        champion_address = self.data.countries[country_name].champion
        champion_equipment = self.data.gladiators[champion_address].equipment
        champion_equipment_bonus = sp.local("champion_equipment_bonus", sp.nat(0))
        sp.if champion_equipment == "None":
            champion_equipment_bonus.value = sp.nat(0)
        sp.else:
            sp.if self.data.equipment[champion_equipment].bonus_country == country_name:
                champion_equipment_bonus.value = self.data.equipment[champion_equipment].power_bonus
            sp.else:
                champion_equipment_bonus.value = sp.nat(0)

        challenger_address = sp.sender
        challenger_equipment = self.data.gladiators[challenger_address].equipment
        challenger_equipment_bonus = sp.local("challenger_equipment_bonus", sp.nat(0))
        sp.if challenger_equipment == "None":
            challenger_equipment_bonus.value = sp.nat(0)
        sp.else:
            sp.if self.data.equipment[challenger_equipment].bonus_country == country_name:
                challenger_equipment_bonus.value = self.data.equipment[challenger_equipment].power_bonus
            sp.else:
                challenger_equipment_bonus.value = sp.nat(0)

        champion_strength = self.data.gladiators[champion_address].strength + (self.data.user_token_balances[champion_address] / self.data.token_bonus_divider) + champion_equipment_bonus.value
        challenger_strength = self.data.gladiators[challenger_address].strength + (self.data.user_token_balances[challenger_address] / self.data.token_bonus_divider) + challenger_equipment_bonus.value

        sp.if champion_strength < challenger_strength:
            self.data.gladiators[champion_address].losses += 1
            self.data.countries[country_name].champion = challenger_address
            self.data.gladiators[challenger_address].wins += 1
            self.data.gladiators[challenger_address].strength += 1
        sp.else:
            sp.if champion_strength == challenger_strength:
                self.data.gladiators[challenger_address].ties += 1
                self.data.gladiators[champion_address].ties += 1
            sp.else:
                self.data.gladiators[challenger_address].losses += 1
                self.data.gladiators[champion_address].wins += 1
                self.data.gladiators[champion_address].strength += 1

    def requestBalanceUpdate(self):
        contract = sp.contract(
            self.entry_point_type(),
            self.data.token_address,
            entry_point = "balance_of"
        ).open_some(message = "InvalidTokenInterface")

        args = sp.record(
            callback    = sp.self_entry_point("updateAvailableFunds"),
            requests    = [
                sp.record(
                    owner       = sp.sender,
                    token_id    = sp.nat(0),
                )
            ]
        )
        sp.transfer(args, sp.tez(0), contract)

    @sp.entry_point
    def updateAvailableFunds(self, params):
        sp.set_type(params, self.response_type())
        sp.for item in params:
            self.data.user_token_balances[item.request.owner] = item.balance
        
    def request_type(self):
        return sp.TRecord(
            owner = sp.TAddress,
            token_id = sp.TNat).layout(("owner", "token_id"))
    def response_type(self):
        return sp.TList(
            sp.TRecord(
                request = self.request_type(),
                balance = sp.TNat).layout(("request", "balance")))
    def entry_point_type(self):
        return sp.TRecord(
            callback = sp.TContract(self.response_type()),
            requests = sp.TList(self.request_type())
        ).layout(("requests", "callback"))
    
@sp.add_test(name = "Test")
def test():
    scenario = sp.test_scenario()
    
    ## Class Invokation
    my_address = "tz1Znbn9QsszyXBhRqjFocYu56DRwCaimPyB"
    first_name = "Man"
    second_name = "Woman"
    avatar_name = "Taco"
    avatar_description = "Test"
    avatar_price = 100
    avatar_url = "https://test.com"
    test_bot =  WorldWarTez(manager_address = my_address)
    
    ## Testing contract
    scenario += test_bot
    enemy_address = sp.address("tz2Cs4EeVPy9L12QoQ3ovQGFb5zuATJPXU1x")
    scenario += test_bot.set_metadata(sp.utils.bytes_of_string("ipfs://QmUAKLPLTh5rPG3m9gLb36d1HL4qtj9YqBqKFRoMtZQEhS")).run(sender = sp.address(my_address))
    scenario += test_bot.create_or_reset_gladiator(first_name).run(sender = sp.address(my_address))
    scenario += test_bot.create_or_reset_gladiator(second_name).run(sender = enemy_address)
    scenario += test_bot.power_up().run(sender = enemy_address, now = sp.timestamp_from_utc(2021, 1, 1, 1, 1, 1))
    scenario += test_bot.add_country(name = "United States", description = "Leader of the Free World").run(sender = sp.address(my_address))
    scenario += test_bot.fight("United States").run(sender = enemy_address)
    scenario += test_bot.add_avatar(name = avatar_name, description = avatar_description, price = avatar_price, image_url = avatar_url).run(sender = sp.address(my_address))
    scenario += test_bot.add_equipment(name = avatar_name, description = avatar_description, price = avatar_price, bonus_country = "United States", power_bonus = 5).run(sender = sp.address(my_address))
    scenario += test_bot.purchase_avatar(1).run(sender = enemy_address, amount = sp.tez(100))
    scenario += test_bot.new_avatar_sale(100).run(sender = enemy_address)
    scenario += test_bot.cancel_avatar_sale().run(sender = enemy_address)
    scenario += test_bot.change_defaults(new_token_address = sp.address("KT1XBpuUgqbiDgGGxF2aw5k9E8vQkZNnY9db"), new_dex_address = sp.address("KT1XBpuUgqbiDgGGxF2aw5k9E8vQkZNnY9db"), new_token_bonus_divider = sp.nat(10), new_power_up_time_limit = sp.int(120)).run(sender = sp.address(my_address))
    scenario += test_bot.change_defaults(new_token_address = sp.address("KT1TiJ1Nn41cLUuRLMHMAoR9TSBvcKt7acsC"), new_dex_address = sp.address("KT18naCbXtcmuNVQDbK6R4DNj5vtB4p1vj5b"), new_token_bonus_divider = sp.nat(1), new_power_up_time_limit = sp.int(60)).run(sender = sp.address(my_address))
    scenario += test_bot.power_up().run(sender = sp.address(my_address), now = sp.timestamp_from_utc(2021, 2, 1, 1, 1, 1))
    scenario += test_bot.power_up().run(sender = sp.address(my_address), now = sp.timestamp_from_utc(2021, 3, 1, 1, 1, 1))
    scenario += test_bot.power_up().run(sender = sp.address(my_address), now = sp.timestamp_from_utc(2021, 4, 1, 1, 1, 1))
    scenario += test_bot.fight("United States").run(sender = sp.address(my_address))
    scenario += test_bot.purchase_equipment("Taco").run(sender = enemy_address, amount = sp.tez(100))
    scenario += test_bot.fight("United States").run(sender = enemy_address)
    
