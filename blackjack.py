import random
import math

def play(decks, penetration, num_players, bankroll_input):
	bankroll = bankroll_input
	shoe = fill_shoe(decks)
	random.shuffle(shoe)

	starting_number_of_cards = len(shoe)

	count = 0
	pnl = 0

	while (float(len(shoe)) / float(starting_number_of_cards)) > (1 - penetration):

		bet_amnt = get_bet_amount(count, shoe, bankroll)
		#print 'base bet amount: ', bet_amnt
		players_hands = [{'hand':[],'bet_amnt':bet_amnt}]
		players_hands, dealer_hand, count = deal_round(shoe, players_hands, count)
		#print 'RC: ',count
		outcome, count = play_round(shoe, players_hands, dealer_hand, count, bet_amnt)
		#print 'RC: ',count
		pnl += outcome
		bankroll += outcome

		"""
		print 'player_hands: '
		for hand in players_hands:
			print 'hand:', hand['hand']
			player_current_total, softhard_player, splittable = get_current_total(hand['hand'])
			print 'player hand total: ', player_current_total
		print 'dealer_hand: ', dealer_hand
		dealer_current_total, softhard_dealer, splittable = get_current_total(dealer_hand)
		print 'dealer total: ', dealer_current_total
		print ''
		print 'count: ',count
		print 'outcome: ', outcome
		print 'cumulative pnl: ', pnl
		print ''
		"""
	return pnl

def play_round(shoe, players_hands, dealer_hand, count, bet_amnt):	
	dealer_up_card = dealer_hand[0][0]
	dealer_down_card = dealer_hand[1][0]

	outcome = 0 #net win/loss after each round. need this variable to account for insurance
	split_count = 0 #to make sure we dont split more than twice
	splits_indicies = [] #so we can pull the right hands out of the player's hand list once they're split
	aces_split = False #so we only get 1 more card after splitting aces

	for player_hand in players_hands:
		if aces_split == True: #ie only 1 more card after split aces
			break

		true_count = get_true_count(count, shoe)
		round_count = 0 #need this to keep track of whether we're on the first 2 cards or not
		while True:
			#print dealer_up_card, 'vs', player_hand['hand']
			decision, insurance = get_decision(dealer_up_card, player_hand['hand'], true_count, split_count, round_count)
			#print 'decision: ', decision

			dealer_has_bj = False
			if dealer_up_card == 'A' and (dealer_down_card == 'T' or dealer_down_card == 'J' or dealer_down_card == 'Q' or dealer_down_card == 'K'):
				dealer_has_bj = True
			elif dealer_down_card == 'A' and (dealer_up_card == 'T' or dealer_up_card == 'J' or dealer_up_card == 'Q' or dealer_up_card == 'K'):
				dealer_has_bj = True
			
			if insurance:
				if decision == 'blackjack': #take even money
					count = count_this_card(dealer_down_card, count)
					return bet_amnt, count
				elif dealer_has_bj: #and player doesnt have BJ
					count = count_this_card(dealer_down_card, count)
					return 0, count
				else: #neither have BJ
					outcome -= (bet_amnt / 2.0)
			elif dealer_has_bj:
				count = count_this_card(dealer_down_card, count)
				if decision == 'blackjack':
					return 0, count
				else:
					return -bet_amnt, count
			elif decision == 'blackjack':
				count = count_this_card(dealer_down_card, count)
				return (bet_amnt * 1.5), count


			if decision == 'split':
				split_count += 1
				splits_indicies.append(players_hands.index(player_hand))
				if player_hand['hand'][0][0] == 'A':
					aces_split = True
				next_card = get_card(shoe)
				count = count_this_card(next_card, count)
				players_hands.append({'hand':[player_hand['hand'][0], next_card],'bet_amnt':bet_amnt})
				next_card = get_card(shoe)
				count = count_this_card(next_card, count)
				players_hands.append({'hand':[player_hand['hand'][1], next_card],'bet_amnt':bet_amnt})
				break
			elif decision == 'double':
				if round_count > 0:
					#just hit
					#print 'not first 2 card; hitting instead'
					next_card = get_card(shoe)
					count = count_this_card(next_card, count)
					player_hand['hand'].append(next_card)
					player_current_total, softhard_player, splittable = get_current_total(player_hand['hand'])
					if player_current_total > 21:
						break
				else:
					next_card = get_card(shoe)
					count = count_this_card(next_card, count)
					player_hand['hand'].append(next_card)
					player_hand['bet_amnt'] += bet_amnt
					break
			elif decision == 'hit':
				next_card = get_card(shoe)
				count = count_this_card(next_card, count)
				player_hand['hand'].append(next_card)
				player_current_total, softhard_player, splittable = get_current_total(player_hand['hand'])
				round_count += 1
				if player_current_total > 21:
					break
			elif decision == 'surrender':
				if round_count > 0:
					#just hit
					#print 'not first 2 card; hitting instead'
					#print 'CANT SURRENDER'
					next_card = get_card(shoe)
					count = count_this_card(next_card, count)
					player_hand['hand'].append(next_card)
					player_current_total, softhard_player, splittable = get_current_total(player_hand['hand'])
					if player_current_total > 21:
						break
				else:
					#cut bet amount in half, treat it as a bust by adding a fake 10 to their hand
					#print 'SURRENDER'
					player_hand['bet_amnt'] -= bet_amnt * 0.5
					player_hand['hand'].append('Tx')
					break
				
			elif decision == 'stand':
				break
		
	for index in reversed(splits_indicies): #remove the hands that were split
		#print 'removing splits'
		players_hands.pop(index)

	dealer_hand, count = play_dealer_hand(dealer_hand, shoe, count)
	this_round_outcome = round_outcome(players_hands, dealer_hand)
	outcome += this_round_outcome

	return outcome, count
			
def play_dealer_hand(dealer_hand, shoe, count):
	count = count_this_card(dealer_hand[1], count)
	while True:
		dealer_current_total, softhard_dealer, splittable = get_current_total(dealer_hand)
		#if (dealer_current_total < 17) or (dealer_current_total == 17 and softhard_dealer == 'soft'):
		if (dealer_current_total < 17):
			next_card = get_card(shoe)
			count = count_this_card(next_card, count)
			dealer_hand.append(next_card)
		else:
			break
	return dealer_hand, count

def round_outcome(players_hands, dealer_hand):
	outcome = 0
	for player_hand in players_hands:
		player_current_total, softhard_player, splittable = get_current_total(player_hand['hand'])
		dealer_current_total, softhard_dealer, splittable = get_current_total(dealer_hand)
		if player_current_total > 21:
			outcome -= player_hand['bet_amnt']
		elif player_current_total > dealer_current_total or (dealer_current_total > 21):
			outcome += player_hand['bet_amnt']
		elif player_current_total == dealer_current_total:
			continue
		elif player_current_total < dealer_current_total:
			outcome -= player_hand['bet_amnt']
	return outcome

## H17 ##
"""
#form: splits_table[player_card_pair][dealer_card]
splits_table = {'2': {'2':'Y','3':'Y','4':'Y','5':'Y','6':'Y','7':'Y','8':'N','9':'N','T':'N','J':'N','Q':'N','K':'N','A':'N'},
			    '3': {'2':'Y','3':'Y','4':'Y','5':'Y','6':'Y','7':'Y','8':'N','9':'N','T':'N','J':'N','Q':'N','K':'N','A':'N'},
			    '4': {'2':'N','3':'N','4':'N','5':'Y','6':'Y','7':'N','8':'N','9':'N','T':'N','J':'N','Q':'N','K':'N','A':'N'},
			    '5': {'2':'N','3':'N','4':'N','5':'N','6':'N','7':'N','8':'N','9':'N','T':'N','J':'N','Q':'N','K':'N','A':'N'},
			    '6': {'2':'Y','3':'Y','4':'Y','5':'Y','6':'Y','7':'N','8':'N','9':'N','T':'N','J':'N','Q':'N','K':'N','A':'N'},
			    '7': {'2':'Y','3':'Y','4':'Y','5':'Y','6':'Y','7':'Y','8':'N','9':'N','T':'N','J':'N','Q':'N','K':'N','A':'N'},
			    '8': {'2':'Y','3':'Y','4':'Y','5':'Y','6':'Y','7':'Y','8':'Y','9':'Y','T':'Y','J':'Y','Q':'Y','K':'Y','A':'Y'},
			    '9': {'2':'Y','3':'Y','4':'Y','5':'Y','6':'Y','7':'N','8':'Y','9':'Y','T':'N','J':'N','Q':'N','K':'N','A':'N'},
			    'T': {'2':'N','3':'N','4':'N','5':'N','6':'N','7':'N','8':'N','9':'N','T':'N','J':'N','Q':'N','K':'N','A':'N'},
			    'J': {'2':'N','3':'N','4':'N','5':'N','6':'N','7':'N','8':'N','9':'N','T':'N','J':'N','Q':'N','K':'N','A':'N'},
			    'Q': {'2':'N','3':'N','4':'N','5':'N','6':'N','7':'N','8':'N','9':'N','T':'N','J':'N','Q':'N','K':'N','A':'N'},
			    'K': {'2':'N','3':'N','4':'N','5':'N','6':'N','7':'N','8':'N','9':'N','T':'N','J':'N','Q':'N','K':'N','A':'N'},
			    'A': {'2':'Y','3':'Y','4':'Y','5':'Y','6':'Y','7':'Y','8':'Y','9':'Y','T':'Y','J':'Y','Q':'Y','K':'Y','A':'Y'}}

#form: softs_table[player_value][dealer_up_card]
softs_table = {13: {'2':'hit','3':'hit','4':'hit','5':'double','6':'double','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    14: {'2':'hit','3':'hit','4':'hit','5':'double','6':'double','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    15: {'2':'hit','3':'hit','4':'double','5':'double','6':'double','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    16: {'2':'hit','3':'hit','4':'double','5':'double','6':'double','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    17: {'2':'hit','3':'double','4':'double','5':'double','6':'double','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    18: {'2':'double','3':'double','4':'double','5':'double','6':'double','7':'stand','8':'stand','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    19: {'2':'stand','3':'stand','4':'stand','5':'stand','6':'double','7':'stand','8':'stand','9':'stand','T':'stand','J':'stand','Q':'stand','K':'stand','A':'stand'},
			    20: {'2':'stand','3':'stand','4':'stand','5':'stand','6':'stand','7':'stand','8':'stand','9':'stand','T':'stand','J':'stand','Q':'stand','K':'stand','A':'stand'},
			    21: {'2':'stand','3':'stand','4':'stand','5':'stand','6':'stand','7':'stand','8':'stand','9':'stand','T':'stand','J':'stand','Q':'stand','K':'stand','A':'stand'}}

#form: softs_table[player_value][dealer_up_card]
hards_table = {2: {'2':'hit','3':'hit','4':'hit','5':'hit','6':'hit','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    3: {'2':'hit','3':'hit','4':'hit','5':'hit','6':'hit','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    4: {'2':'hit','3':'hit','4':'hit','5':'hit','6':'hit','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    5: {'2':'hit','3':'hit','4':'hit','5':'hit','6':'hit','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    6: {'2':'hit','3':'hit','4':'hit','5':'hit','6':'hit','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    7: {'2':'hit','3':'hit','4':'hit','5':'hit','6':'hit','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    8: {'2':'hit','3':'hit','4':'hit','5':'hit','6':'hit','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    9: {'2':'hit','3':'double','4':'double','5':'double','6':'double','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    10: {'2':'double','3':'double','4':'double','5':'double','6':'double','7':'double','8':'double','9':'double','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    11: {'2':'double','3':'double','4':'double','5':'double','6':'double','7':'double','8':'double','9':'double','T':'double','J':'double','Q':'double','K':'double','A':'double'},
			    12: {'2':'hit','3':'hit','4':'stand','5':'stand','6':'stand','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    13: {'2':'stand','3':'stand','4':'stand','5':'stand','6':'stand','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    14: {'2':'stand','3':'stand','4':'stand','5':'stand','6':'stand','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    15: {'2':'stand','3':'stand','4':'stand','5':'stand','6':'stand','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    16: {'2':'stand','3':'stand','4':'stand','5':'stand','6':'stand','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    17: {'2':'stand','3':'stand','4':'stand','5':'stand','6':'stand','7':'stand','8':'stand','9':'stand','T':'stand','J':'stand','Q':'stand','K':'stand','A':'stand'},
			    18: {'2':'stand','3':'stand','4':'stand','5':'stand','6':'stand','7':'stand','8':'stand','9':'stand','T':'stand','J':'stand','Q':'stand','K':'stand','A':'stand'},
			    19: {'2':'stand','3':'stand','4':'stand','5':'stand','6':'stand','7':'stand','8':'stand','9':'stand','T':'stand','J':'stand','Q':'stand','K':'stand','A':'stand'},
			    20: {'2':'stand','3':'stand','4':'stand','5':'stand','6':'stand','7':'stand','8':'stand','9':'stand','T':'stand','J':'stand','Q':'stand','K':'stand','A':'stand'},
			    21: {'2':'stand','3':'stand','4':'stand','5':'stand','6':'stand','7':'stand','8':'stand','9':'stand','T':'stand','J':'stand','Q':'stand','K':'stand','A':'stand'}}
"""
## S17, SURRENDER ##
#form: splits_table[player_card_pair][dealer_card]
splits_table = {'2': {'2':'Y','3':'Y','4':'Y','5':'Y','6':'Y','7':'Y','8':'N','9':'N','T':'N','J':'N','Q':'N','K':'N','A':'N'},
			    '3': {'2':'Y','3':'Y','4':'Y','5':'Y','6':'Y','7':'Y','8':'N','9':'N','T':'N','J':'N','Q':'N','K':'N','A':'N'},
			    '4': {'2':'N','3':'N','4':'N','5':'Y','6':'Y','7':'N','8':'N','9':'N','T':'N','J':'N','Q':'N','K':'N','A':'N'},
			    '5': {'2':'N','3':'N','4':'N','5':'N','6':'N','7':'N','8':'N','9':'N','T':'N','J':'N','Q':'N','K':'N','A':'N'},
			    '6': {'2':'Y','3':'Y','4':'Y','5':'Y','6':'Y','7':'N','8':'N','9':'N','T':'N','J':'N','Q':'N','K':'N','A':'N'},
			    '7': {'2':'Y','3':'Y','4':'Y','5':'Y','6':'Y','7':'Y','8':'N','9':'N','T':'N','J':'N','Q':'N','K':'N','A':'N'},
			    '8': {'2':'Y','3':'Y','4':'Y','5':'Y','6':'Y','7':'Y','8':'Y','9':'Y','T':'Y','J':'Y','Q':'Y','K':'Y','A':'Y'},
			    '9': {'2':'Y','3':'Y','4':'Y','5':'Y','6':'Y','7':'N','8':'Y','9':'Y','T':'N','J':'N','Q':'N','K':'N','A':'N'},
			    'T': {'2':'N','3':'N','4':'N','5':'N','6':'N','7':'N','8':'N','9':'N','T':'N','J':'N','Q':'N','K':'N','A':'N'},
			    'J': {'2':'N','3':'N','4':'N','5':'N','6':'N','7':'N','8':'N','9':'N','T':'N','J':'N','Q':'N','K':'N','A':'N'},
			    'Q': {'2':'N','3':'N','4':'N','5':'N','6':'N','7':'N','8':'N','9':'N','T':'N','J':'N','Q':'N','K':'N','A':'N'},
			    'K': {'2':'N','3':'N','4':'N','5':'N','6':'N','7':'N','8':'N','9':'N','T':'N','J':'N','Q':'N','K':'N','A':'N'},
			    'A': {'2':'Y','3':'Y','4':'Y','5':'Y','6':'Y','7':'Y','8':'Y','9':'Y','T':'Y','J':'Y','Q':'Y','K':'Y','A':'Y'}}

#form: softs_table[player_value][dealer_up_card]
softs_table = {13: {'2':'hit','3':'hit','4':'hit','5':'double','6':'double','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    14: {'2':'hit','3':'hit','4':'hit','5':'double','6':'double','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    15: {'2':'hit','3':'hit','4':'double','5':'double','6':'double','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    16: {'2':'hit','3':'hit','4':'double','5':'double','6':'double','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    17: {'2':'hit','3':'double','4':'double','5':'double','6':'double','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    18: {'2':'stand','3':'double','4':'double','5':'double','6':'double','7':'stand','8':'stand','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    19: {'2':'stand','3':'stand','4':'stand','5':'stand','6':'stand','7':'stand','8':'stand','9':'stand','T':'stand','J':'stand','Q':'stand','K':'stand','A':'stand'},
			    20: {'2':'stand','3':'stand','4':'stand','5':'stand','6':'stand','7':'stand','8':'stand','9':'stand','T':'stand','J':'stand','Q':'stand','K':'stand','A':'stand'},
			    21: {'2':'stand','3':'stand','4':'stand','5':'stand','6':'stand','7':'stand','8':'stand','9':'stand','T':'stand','J':'stand','Q':'stand','K':'stand','A':'stand'}}

#form: softs_table[player_value][dealer_up_card]
hards_table = {2: {'2':'hit','3':'hit','4':'hit','5':'hit','6':'hit','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    3: {'2':'hit','3':'hit','4':'hit','5':'hit','6':'hit','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    4: {'2':'hit','3':'hit','4':'hit','5':'hit','6':'hit','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    5: {'2':'hit','3':'hit','4':'hit','5':'hit','6':'hit','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    6: {'2':'hit','3':'hit','4':'hit','5':'hit','6':'hit','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    7: {'2':'hit','3':'hit','4':'hit','5':'hit','6':'hit','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    8: {'2':'hit','3':'hit','4':'hit','5':'hit','6':'hit','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    9: {'2':'hit','3':'double','4':'double','5':'double','6':'double','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    10: {'2':'double','3':'double','4':'double','5':'double','6':'double','7':'double','8':'double','9':'double','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    11: {'2':'double','3':'double','4':'double','5':'double','6':'double','7':'double','8':'double','9':'double','T':'double','J':'double','Q':'double','K':'double','A':'hit'},
			    12: {'2':'hit','3':'hit','4':'stand','5':'stand','6':'stand','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    13: {'2':'stand','3':'stand','4':'stand','5':'stand','6':'stand','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    14: {'2':'stand','3':'stand','4':'stand','5':'stand','6':'stand','7':'hit','8':'hit','9':'hit','T':'hit','J':'hit','Q':'hit','K':'hit','A':'hit'},
			    15: {'2':'stand','3':'stand','4':'stand','5':'stand','6':'stand','7':'hit','8':'hit','9':'hit','T':'surrender','J':'surrender','Q':'surrender','K':'surrender','A':'hit'},
			    16: {'2':'stand','3':'stand','4':'stand','5':'stand','6':'stand','7':'hit','8':'hit','9':'surrender','T':'surrender','J':'surrender','Q':'surrender','K':'surrender','A':'surrender'},
			    17: {'2':'stand','3':'stand','4':'stand','5':'stand','6':'stand','7':'stand','8':'stand','9':'stand','T':'stand','J':'stand','Q':'stand','K':'stand','A':'stand'},
			    18: {'2':'stand','3':'stand','4':'stand','5':'stand','6':'stand','7':'stand','8':'stand','9':'stand','T':'stand','J':'stand','Q':'stand','K':'stand','A':'stand'},
			    19: {'2':'stand','3':'stand','4':'stand','5':'stand','6':'stand','7':'stand','8':'stand','9':'stand','T':'stand','J':'stand','Q':'stand','K':'stand','A':'stand'},
			    20: {'2':'stand','3':'stand','4':'stand','5':'stand','6':'stand','7':'stand','8':'stand','9':'stand','T':'stand','J':'stand','Q':'stand','K':'stand','A':'stand'},
			    21: {'2':'stand','3':'stand','4':'stand','5':'stand','6':'stand','7':'stand','8':'stand','9':'stand','T':'stand','J':'stand','Q':'stand','K':'stand','A':'stand'}}


def get_decision(dealer_up_card, player_hand, true_count, split_count, round_count):
	player_current_total, softhard_player, splittable = get_current_total(player_hand)
	#print player_current_total

	insurance = False
	if round_count == 0:
		#check insurance
		if dealer_up_card == 'A' and true_count >= 3.0: 
			insurance = True

		if player_current_total == 21:
			return 'blackjack', insurance

	#check split
	if splittable and split_count < 2:
		#print 'SPLITTABLE'
		pair_value = player_hand[0][0]
		split_or_not = splits_table[pair_value][dealer_up_card]
		#print pair_value
		#print dealer_up_card
		#print split_or_not
		if split_or_not == 'Y':
			return 'split', insurance
		elif (pair_value == 'T' or pair_value == 'J' or pair_value == 'Q' or pair_value == 'K'):
			if dealer_up_card == '4' and true_count >= 6.0:
				return 'split', insurance
			elif dealer_up_card == '5' and true_count >= 5.0:
				return 'split', insurance
			elif dealer_up_card == '6' and true_count >= 4.0:
				return 'split', insurance

	
	#strategy adjustments based on count
	if true_count <= 0:
		if player_current_total == 12 and dealer_up_card == '4':
			return 'hit', insurance
		elif softhard_player == 'soft' and player_current_total == 19:
			return 'stand', insurance
		if true_count <= -1.0:
			if player_current_total == 13 and dealer_up_card == '2':
				return 'hit', insurance
	elif true_count > 0.0:
		if player_current_total == 16 and (dealer_up_card == 'T' or dealer_up_card == 'J' or dealer_up_card == 'Q' or dealer_up_card == 'K'):
			return 'stand', insurance
		if true_count >= 1.0:
			if (softhard_player == 'soft' and player_current_total == 19) and dealer_up_card == 5:
				return 'double', insurance
			elif (softhard_player == 'soft' and player_current_total == 17) and dealer_up_card == 2:
				return 'double', insurance
			elif player_current_total == 9 and dealer_up_card == '2':
				return 'double', insurance
			if true_count >= 2.0:
				if player_current_total == 12 and dealer_up_card == '3':
					return 'stand', insurance
				elif player_current_total == 8 and dealer_up_card == '6':
					return 'double', insurance
				if true_count >= 3.0:
					if (softhard_player == 'soft' and player_current_total == 19) and dealer_up_card == 4:
						return 'double', insurance
					elif player_current_total == 16 and dealer_up_card == 'A':
						return 'stand', insurance
					elif player_current_total == 12 and dealer_up_card == '2':
						return 'stand', insurance
					elif player_current_total == 10 and dealer_up_card == 'A':
						return 'double', insurance
					elif player_current_total == 9 and dealer_up_card == '7':
						return 'double', insurance
					if true_count >= 4.0:
						if player_current_total == 16 and dealer_up_card == '9':
								return 'stand', insurance
						elif player_current_total == 15 and (dealer_up_card == 'T' or dealer_up_card == 'J' or dealer_up_card == 'Q' or dealer_up_card == 'K'):
							return 'stand', insurance
						elif player_current_total == 10 and (dealer_up_card == 'T' or dealer_up_card == 'J' or dealer_up_card == 'Q' or dealer_up_card == 'K'):
							return 'double', insurance
						if true_count >= 5.0:
							if player_current_total == 15 and dealer_up_card == 'A':
								return 'stand', insurance	
	

	#if no splitting or adjustment should be made based on count, play basic strategy:
	if softhard_player == 'soft':
		return softs_table[player_current_total][dealer_up_card], insurance
	elif softhard_player == 'hard':
		return hards_table[player_current_total][dealer_up_card], insurance



def get_current_total(player_hand):
	softhard = 'hard'
	ace_count = 0
	value = 0
	for card in player_hand:
		card_val = card[0]
		if card_val == 'A':
			value += 11
			softhard = 'soft'
			ace_count += 1			
		elif card_val == 'K' or card_val == 'Q' or card_val == 'J' or card_val == 'T':
			value += 10
		else:
			this_val = int(card_val)
			value += this_val

	non_soft_value = value
	for x in range(0,ace_count):
		if value > 21 and softhard == 'soft':
			value -= 10
		non_soft_value -= 10
	if non_soft_value >= 11 and softhard == 'soft':
		softhard = 'hard'
	

	splittable = False
	if player_hand[0][0] == player_hand[1][0]:
		splittable = True
	return value, softhard, splittable


def get_true_count(count, shoe):
	decks_remaining = float(len(shoe)) / 52.0
	return float(count) / decks_remaining

def deal_round(shoe, players_hands, count):
	for player_hand in players_hands:
		next_card = get_card(shoe)
		count = count_this_card(next_card, count)
		player_hand['hand'].append(next_card)
		next_card = get_card(shoe)
		count = count_this_card(next_card, count)
		player_hand['hand'].append(next_card)

	dealer_hand = []
	next_card = get_card(shoe)
	dealer_hand.append(next_card)
	count = count_this_card(next_card, count)
	next_card = get_card(shoe)
	dealer_hand.append(next_card)
	#dont count this card yet - player cant see it

	return players_hands, dealer_hand, count

def count_this_card(card, count):
	#hi-low system
	card_val = card[0]

	if card_val == 'A' or card_val == 'K' or card_val == 'Q' or card_val == 'J' or card_val == 'T':
		#print 'count - 1'
		return count - 1 
	elif card_val == '6' or card_val == '5' or card_val == '4' or card_val == '3' or card_val == '2':
		#print 'count + 1'
		return count + 1
	else:
		#print 'count 0'
		return count

	
def fill_shoe(decks):
	new_deck = ['As','2s','3s','4s','5s','6s','7s','8s','9s','Ts','Js','Qs','Ks',
			'Ah','2h','3h','4h','5h','6h','7h','8h','9h','Th','Jh','Qh','Kh',
			'Ad','2d','3d','4d','5d','6d','7d','8d','9d','Td','Jd','Qd','Kd',
			'Ac','2c','3c','4c','5c','6c','7c','8c','9c','Tc','Jc','Qc','Kc']
	shoe = []
	for x in range(0,decks):
		shoe.extend(new_deck)
	return shoe

def get_card(shoe):
	if len(shoe) > 0:
		#index = random.randrange(len(shoe))
		#return shoe.pop(index)
		return shoe.pop(0)
	else:
		return None

	

def get_bet_amount(count, shoe, bankroll):
	true_count = get_true_count(count, shoe)
	#print 'true_count: ', true_count
	#assume each true count point is 1% edge, starting with 2
	#if true_count >= 1.0:
		#unrounded_bet_amnt = (math.floor(true_count) / 200.0) * bankroll #full kelly
		#unrounded_bet_amnt = math.floor(true_count) * 100.0 #50 base, 100 units on positive
		#unrounded_bet_amnt = 25.0 + (math.floor(true_count) - 1) * 50.0 #25 base, 50 units on positive
		#unrounded_bet_amnt = math.floor(true_count) * 50.0
		#unrounded_bet_amnt = 25
	if true_count > 1.0:
		if true_count >= 2.0:
			unrounded_bet_amnt = (math.floor(true_count) - 1) * 50.0
		else:
			unrounded_bet_amnt = 25.0
	else:
		#unrounded_bet_amnt = 0.005 * bankroll #full kelly
		#unrounded_bet_amnt = 50 #50 base, 100 units on positive
		unrounded_bet_amnt = 10.0 #25 base, 50 units on positive
	#print 'unrounded_bet_amnt: ', unrounded_bet_amnt
	#rounded_bet_amnt = unrounded_bet_amnt - (unrounded_bet_amnt % 5) #round down to the nearest 5
	#print 'rounded_bet_amnt: ', rounded_bet_amnt
	return unrounded_bet_amnt

pnl_sets = []

for y in range(0,10000): #play x shoes y times
	cumulative_pnl = 0
	bankroll = 10000.0
	for x in range(0,30): #play x shoes
		pnl = play(decks=8, penetration=0.75, num_players=1, bankroll_input=bankroll)
		cumulative_pnl += pnl
		bankroll += pnl
		#print 'bankroll: ', bankroll
	#print 'cumulative_pnl: ', cumulative_pnl
	pnl_sets.append(cumulative_pnl)

#print 'pnl_sets: '
f = open('results.txt','w')
for pnl in pnl_sets:
	#print pnl 
	f.write(str(pnl))
	f.write('\n')
f.close()
