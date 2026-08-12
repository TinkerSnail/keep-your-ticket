extends Node

## The people who have to be the same person twice, autoloaded as `ParkGuests`.
##
## A section's crowd is generated, anonymous and thrown away with the section.
## That is right for almost everybody: the plaza's cast exists to be dense, to
## be walked around and to be photographed once, and nothing is lost when it is
## discarded at the seam. `scenes/npc/crowd.gd` keeps its own `_roster` of the
## bodies it is holding, and that list dies with it.
##
## This is the other kind. `documentation/design.md` asks the player to offer a
## copy rather than to ask permission, and a yes puts the photograph into the
## park's system — a print on the wall and a claim ticket in somebody's pocket.
## That somebody has to survive being walked away from. They have to survive the
## plaza being unloaded while they are still in it, and they have to be
## recognisable an hour later, in a different section, with a different crowd
## standing around them.
##
## So the roster holds identities, never nodes. A person here is a seed, an
## itinerary and a debt. When a crowd comes up it asks who is in its section
## this hour and binds those identities onto bodies it was going to build
## anyway; when it goes down it lets go, and nothing is lost, because there was
## never anything in the body worth keeping.
##
## It is deliberately small. Identity is only worth paying for where the player
## might meet the same face twice, and at plaza density that is a couple of
## dozen people out of hundreds. Everybody else is crowd, and should be.

## Somebody was promised a copy. The park's side of that — the print reaching
## the wall after a delay — hangs off this.
signal print_owed(person: int)

## Somebody collected. The end of the only errand in the game that the player
## does not have to be told about.
signal print_claimed(person: int)

## How many people carry an identity. Small on purpose: see above. Twenty-four
## is about a day's worth of people you could plausibly photograph, be asked by,
## and run into again, without any of them becoming a face the player is sick of.
const ROSTER_SIZE := 24

## Fixed, for the same reason `crowd.gd` fixes its own: a park the player is
## meant to learn should not deal a different set of people every launch, and a
## harness measuring the day cannot say anything about a day that is different
## every run. A different number from the crowd's so the two streams do not
## walk in step.
const ROSTER_SEED := 0x7A1E

## How long a visit runs, in hours. Nobody here is at the park for the whole
## twelve — a person who is present from open to close is a fixture, and a
## fixture is a different design problem than a guest.
const VISIT_HOURS := Vector2i(3, 6)

## Ticket numbers start here rather than at one. A park that opened this morning
## and has never printed anything is not what the fiction says; the number on
## the stub should read as one of many.
const FIRST_TICKET := 1840

var _people: Dictionary = {}
var _order: Array[int] = []
var _next_ticket := FIRST_TICKET
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	_rng.seed = ROSTER_SEED
	_build_roster()


## A person is a seed, where they are, and what they are owed. The seed is the
## whole of their appearance — the crowd generator already builds a body from
## one, so handing it the same number twice is what makes somebody the same
## person twice, and nothing about the body has to be stored or restored.
##
## No names. The player is a photographer on a shift, not somebody being
## introduced to people, and the park's own way of identifying a guest is the
## number on the stub they are carrying.
## Nobody is in the park before it opens or after it shuts, and `ParkClock` is
## the authority on both. Read here rather than mirrored into constants of our
## own: an autoload's constants are not available to a `const` expression, and a
## second copy of the park's hours is a second thing to get wrong.
func _build_roster() -> void:
	var spokes := _built_sections()
	var first_hour := int(ParkClock.OPEN_HOUR)
	var last_hour := int(ParkClock.CLOSE_HOUR)
	for i in ROSTER_SIZE:
		var arrives := _rng.randi_range(first_hour, last_hour - VISIT_HOURS.x)
		var stays := _rng.randi_range(VISIT_HOURS.x, VISIT_HOURS.y)
		var leaves := mini(arrives + stays, last_hour)
		var person := {
			"id": i,
			"seed": _rng.randi(),
			"arrives": arrives,
			"leaves": leaves,
			"itinerary": _itinerary(arrives, leaves, spokes),
			"ticket": 0,
			"owed": false,
			"photographed": 0,
			"asked": 0,
		}
		_people[i] = person
		_order.append(i)


## Where somebody is, hour by hour, for as long as they are here.
##
## With one section built this is a constant, and that is fine — the shape is
## what matters, and the shape is that a person's whereabouts is a property of
## the person rather than of whichever crowd happens to be standing. The day the
## boardwalk loads, this starts returning two answers and nothing above it
## changes.
func _itinerary(arrives: int, leaves: int, spokes: Array[StringName]) -> Dictionary:
	var plan := {}
	if spokes.is_empty():
		return plan
	# Everybody comes in through the gate, so the first hour is always the hub.
	# After that they move between spokes at a pace that is nobody's idea of a
	# schedule — the point is only that they are somewhere findable, not that the
	# park runs a timetable it never tells the player about.
	var where: StringName = spokes[0]
	for h in range(arrives, leaves):
		plan[h] = where
		if spokes.size() > 1 and _rng.randf() < 0.35:
			where = spokes[_rng.randi_range(0, spokes.size() - 1)]
	return plan


## Only sections that exist. A person cannot be scheduled into a passage that
## bends and stops, and `ParkSections` is the authority on which those are.
func _built_sections() -> Array[StringName]:
	var built: Array[StringName] = []
	for id in ParkSections.SECTIONS:
		var section := StringName(id)
		if ParkSections.is_built(section):
			built.append(section)
	return built


## Who a crowd should be holding, this section, this hour. The crowd calls this
## when it comes up and after the hour turns, and binds what it gets onto bodies
## it was building regardless — so identity costs nothing extra in the plaza.
##
## Nothing guarantees the crowd has room. A section that wants twelve people at
## ten in the morning and is handed fifteen identities binds twelve and drops
## three, and the three are simply not in the park that hour. That is the right
## failure: the roster describes who might be met, and the hour decides how much
## of the park there is to meet them in.
func residents(section: StringName, hour: int = -1) -> Array[int]:
	var h := hour if hour >= 0 else ParkClock.hour()
	var here: Array[int] = []
	for id in _order:
		var record: Dictionary = _people[id]
		var plan: Dictionary = record["itinerary"]
		if plan.get(h, &"") == section:
			here.append(id)
	return here


func person(id: int) -> Dictionary:
	return _people.get(id, {})


## The appearance seed. The one number a crowd needs to build the same body
## twice.
func appearance_seed(id: int) -> int:
	var record: Dictionary = _people.get(id, {})
	return record.get("seed", 0)


## The player offered a copy and was told yes. This is the only thing in the
## game that puts a photograph anywhere except the album — everything else the
## player shoots is theirs and stays theirs.
##
## The ticket number is issued here rather than when the print is collected,
## because the stub is what the guest walks away holding.
func owe_print(id: int) -> int:
	if not _people.has(id):
		return 0
	var record: Dictionary = _people[id]
	if record["owed"]:
		return record["ticket"]
	record["owed"] = true
	record["ticket"] = _next_ticket
	_next_ticket += 1
	print_owed.emit(id)
	return record["ticket"]


func is_owed(id: int) -> bool:
	var record: Dictionary = _people.get(id, {})
	return record.get("owed", false)


func claim(id: int) -> void:
	if not _people.has(id):
		return
	var record: Dictionary = _people[id]
	if not record["owed"]:
		return
	record["owed"] = false
	print_claimed.emit(id)


## Kept because asking is meant to usually fail, and a guest who has already
## said no should not be asked the same question by the same photographer twice
## in an afternoon. Counting is not scoring — nothing reads these back to the
## player and nothing is totalled at the end of the day.
func note_asked(id: int) -> void:
	if _people.has(id):
		_people[id]["asked"] += 1


func note_photographed(id: int) -> void:
	if _people.has(id):
		_people[id]["photographed"] += 1
