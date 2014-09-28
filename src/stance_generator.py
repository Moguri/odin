
import bisect
import itertools
import random
import json


from stats import *


def accumulate(iterable):
	it = iter(iterable)
	total = next(it)
	yield total
	for element in it:
		total += element
		yield total


def weighted_choice(choices, weights):
	cumdist = list(accumulate(weights))
	x = random.random() * cumdist[-1]
	return choices[bisect.bisect(cumdist, x)]


def weighted_sample(choices, weights, n):
	sample = set()
	while len(sample) < n:
		c = weighted_choice(choices, weights)
		sample.add(c)
	return list(sample)


def stances_to_json(stance_list):
	class StanceEncoder(json.JSONEncoder):
		STANCE_ATTRIBS = [
			"name",
			"benefit_vector",
			"cost_vector",
		]

		def default(self, obj):
			if isinstance(obj, Stance):
				return {i: getattr(obj, i) for i in self.STANCE_ATTRIBS}
			return json.JSONEncoder.default(self, obj)

	return StanceEncoder().encode(stance_list)


class Stance(object):
	def __init__(self):
		self.name = "Stance"
		self.level = 1
		self.cost_factor = 0.0
		self.benefit_vector = [0.0 for i in range(6)]
		self.cost_vector = [0.0 for i in range(6)]

	def __str__(self):
		s = self.name + "(%.2f)" % self.cost_factor + "\n"
		s += "\t" + str([self.movement, self.range, self.damage, self.defense, self.regen, self.speed]) + "\n"
		return s

	def _calculate_effect(self, stat_index):
		cost_factor = self.level * self.cost_factor
		benefit_factor = self.level + self.level * self.cost_factor
		benefit = self.benefit_vector[stat_index]
		cost = self.cost_vector[stat_index]

		factor = benefit_factor * benefit - cost_factor * cost

		return factor

	def to_dna(self):
		dna = StanceDNA()
		dna.cost_factor = self.cost_factor
		dna.benefits = self.benefit_vector
		dna.costs = self.cost_vector

		return dna

	@property
	def movement(self):
		return self._calculate_effect(STAT_MOVEMENT)

	@property
	def range(self):
		return self._calculate_effect(STAT_RANGE)

	@property
	def damage(self):
		return self._calculate_effect(STAT_DAMAGE)

	@property
	def defense(self):
		return self._calculate_effect(STAT_DEFENSE)

	@property
	def regen(self):
		return self._calculate_effect(STAT_REGEN)

	@property
	def speed(self):
		return self._calculate_effect(STAT_SPEED)


class StanceDNA(object):
	__slots__ = ["benefits", "costs", "cost_factor", "fitness"]

	def __init__(self):
		self.benefits = [0 for i in range(6)]
		self.costs = [0 for i in range(6)]
		self.cost_factor = 0
		self.fitness = 0

	@classmethod
	def generate(cls):
		"""Create StanceDNA with random values"""

		dna = StanceDNA()
		dna.cost_factor = random.random()

		for i in range(len(dna.benefits)):
			dna.benefits[i] = random.random()
		for i in range(len(dna.costs)):
			dna.costs[i] = random.random()

		dna.normalize()

		return dna

	@classmethod
	def crossover(cls, parents):
		"""Create StanceDNA by mixing elements from parents"""

		dna = StanceDNA()

		for i in range(len(dna.benefits)):
			dna.benefits[i] = random.choice(parents).benefits[i]
		for i in range(len(dna.costs)):
			dna.costs[i] = random.choice(parents).costs[i]
		dna.cost_factor = random.choice(parents).cost_factor

		dna.normalize()

		return dna

	def to_stance(self):
		stance = Stance()
		stance.benefit_vector = self.benefits
		stance.cost_vector = self.costs
		stance.cost_factor = self.cost_factor
		stance.name = "Generated"

		return stance

	def normalize(self):
		"""One normalizes the benefit and cost vectors"""

		norm = sum(self.benefits)
		for i in range(len(self.benefits)):
			self.benefits[i] /= norm

		norm = sum(self.costs)
		for i in range(len(self.costs)):
			self.costs[i] /= norm

	def mutate(self, rate):
		"""Randomly change some elements based on rate"""

		# Mutate benefits
		for i in range(len(self.benefits)):
			if random.random() < rate:
				self.benefits[i] = random.uniform(0, 2*self.benefits[i])

		# Mutate costs
		for i in range(len(self.costs)):
			if random.random() < rate:
				self.costs[i] = random.uniform(0, 2*self.costs[i])

		# Mutate cost_factor
		if random.random() < rate:
			self.cost_factor = random.uniform(0, 2* self.cost_factor)
			if self.cost_factor > 1.0:
				self.cost_factor = 1.0

		self.normalize()

	def update_fitness(self, pool):
		"""Determine a new fitness value based on a pool of dna objects"""

		self.fitness = 0

		for sample in pool:
			benefit_fitness = 0
			for i in range(len(self.benefits)):
				benefit_fitness = self.benefits[i] * sample.benefits[i]
			cost_fitness = 0
			for i in range(len(self.costs)):
				cost_fitness = self.costs[i] * sample.costs[i]

			self.fitness = benefit_fitness + cost_fitness


class StanceGenerator(object):
	@classmethod
	def n_random(cls, n):
		stances = []

		for i in range(n):
			dna = StanceDNA.generate()
			stances.append(dna.to_stance())

		return stances

	@classmethod
	def n_from_pool(cls, n, pool, iterations=3, rate=0.5):
		pop = [StanceDNA.generate() for i in range(n)]
		pool_dna = [stance.to_dna() for stance in pool]

		for i in range(iterations):
			for dna in pop:
				dna.update_fitness(pool_dna)

			new_pop = [StanceDNA.crossover(weighted_sample(pop, [d.fitness for d in pop], 3)) for i in range(n)]
			for dna in new_pop:
				dna.mutate(rate)

			pop = new_pop

		return [dna.to_stance() for dna in pop]
