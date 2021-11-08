import logging
import random

from . import formulas
from . import temperature
from .bond import Bond
from .bond import possible_group_bonds
from .coderack import coderack
from .correspondence import Correspondence
from .group import Group
from .letter import Letter
from .replacement import Replacement
from .slipnet import slipnet
from .workspace_formulas import choose_bond_facet
from .workspace_formulas import choose_directed_neighbor
from .workspace_formulas import choose_neighbour
from .workspace_formulas import choose_unmodified_object
from .workspace_formulas import workspace
from .workspace_object import WorkspaceObject


# some methods common to the codelets
def __show_which_string_object_is_from(structure):
    if not structure:
        return "unstructured"
    if isinstance(structure, WorkspaceObject):
        return "target"
    if structure.string == workspace.initial:
        return "initial"
    return "other"


def __get_scout_source(slipnode, relevance_method, type_name):
    initial_relevance = relevance_method(workspace.initial, slipnode)
    target_relevance = relevance_method(workspace.target, slipnode)
    initial_unhappiness = workspace.initial.intra_string_unhappiness
    target_unhappiness = workspace.target.intra_string_unhappiness
    logging.info(
        f"initial : relevance = {initial_relevance}, "
        f"unhappiness = {int(initial_unhappiness)}"
    )
    logging.info(
        f"target : relevance = {target_relevance}, "
        f"unhappiness = {int(target_unhappiness)}"
    )
    string = workspace.initial
    relevances = initial_relevance + target_relevance
    unhappinesses = initial_unhappiness + target_unhappiness
    randomized = random.random() * (relevances + unhappinesses)
    initials = initial_relevance + initial_unhappiness
    if randomized > initials:
        string = workspace.target
        logging.info(f"target string selected: {workspace.target} for {type_name}")
    else:
        logging.info(f"initial string selected: {workspace.initial} for {type_name}")
    source = choose_unmodified_object("intra_string_salience", string.objects)
    return source


def __get_bond_facet(source, destination):
    bond_facet = choose_bond_facet(source, destination)
    assert bond_facet
    return bond_facet


def __get_descriptors(bond_facet, source, destination):
    source_descriptor = source.get_descriptor(bond_facet)
    destination_descriptor = destination.get_descriptor(bond_facet)
    assert source_descriptor
    assert destination_descriptor
    return source_descriptor, destination_descriptor


def __all_opposite_mappings(mappings):
    return len([m for m in mappings if m.label != slipnet.opposite]) == 0


def __structure_versus_structure(structure1, weight1, structure2, weight2):
    structure1.update_strength()
    structure2.update_strength()
    weighted_strength1 = formulas.temperature_adjusted_value(
        structure1.total_strength * weight1
    )
    weighted_strength2 = formulas.temperature_adjusted_value(
        structure2.total_strength * weight2
    )
    rhs = (weighted_strength1 + weighted_strength2) * random.random()
    logging.info(f"{weighted_strength1} > {rhs}: {weighted_strength1 > rhs}")
    return weighted_strength1 > rhs


def __fight(structure, structure_weight, incompatibles, incompatible_weight):
    if not (incompatibles and len(incompatibles)):
        return True
    for incompatible in incompatibles:
        if not __structure_versus_structure(
            structure, structure_weight, incompatible, incompatible_weight
        ):
            logging.info(f"lost fight with {incompatible}")
            return False
        logging.info(f"won fight with {incompatible}")
    return True


def __fight_incompatibles(
    incompatibles, structure, name, structure_weight, incompatible_weight
):
    if len(incompatibles):
        if __fight(structure, structure_weight, incompatibles, incompatible_weight):
            logging.info(f"broke the {name}")
            return True
        logging.info(f"failed to break {name}: Fizzle")
        return False
    logging.info(f"no incompatible {name}")
    return True


def __slippability(concept_mappings):
    for mapping in concept_mappings:
        slippiness = mapping.slippability() / 100.0
        probability_of_slippage = formulas.temperature_adjusted_probability(slippiness)
        if formulas.coin_flip(probability_of_slippage):
            return True
    return False


# start the actual codelets
def breaker():
    probability_of_fizzle = (100.0 - formulas.Temperature) / 100.0
    assert not formulas.coin_flip(probability_of_fizzle)
    # choose a structure at random
    structures = [
        s for s in workspace.structures if isinstance(s, (Group, Bond, Correspondence))
    ]
    assert structures
    structure = random.choice(structures)
    __show_which_string_object_is_from(structure)
    break_objects = [structure]
    if isinstance(structure, Bond):
        if structure.source.group:
            if structure.source.group == structure.destination.group:
                break_objects += [structure.source.group]
    # try to break all objects
    for structure in break_objects:
        break_probability = formulas.temperature_adjusted_probability(
            structure.total_strength / 100.0
        )
        if formulas.coin_flip(break_probability):
            return
    for structure in break_objects:
        structure.break_the_structure()


def bottom_up_description_scout(codelet):
    chosen_object = choose_unmodified_object("total_salience", workspace.objects)
    assert chosen_object
    __show_which_string_object_is_from(chosen_object)
    description = formulas.choose_relevant_description_by_activation(chosen_object)
    assert description
    sliplinks = formulas.similar_property_links(description.descriptor)
    assert sliplinks
    values = [
        sliplink.degree_of_association() * sliplink.destination.activation
        for sliplink in sliplinks
    ]
    i = formulas.select_list_position(values)
    chosen = sliplinks[i]
    chosen_property = chosen.destination
    coderack.propose_description(
        chosen_object, chosen_property.category(), chosen_property, codelet
    )


def top_down_description_scout(codelet):
    description_type = codelet.arguments[0]
    chosen_object = choose_unmodified_object("total_salience", workspace.objects)
    assert chosen_object
    __show_which_string_object_is_from(chosen_object)
    descriptions = chosen_object.get_possible_descriptions(description_type)
    assert descriptions
    values = [n.activation for n in descriptions]
    i = formulas.select_list_position(values)
    chosen_property = descriptions[i]
    coderack.propose_description(
        chosen_object, chosen_property.category(), chosen_property, codelet
    )


def description_strength_tester(codelet):
    description = codelet.arguments[0]
    description.descriptor.buffer = 100.0
    description.update_strength()
    strength = description.total_strength
    probability = formulas.temperature_adjusted_probability(strength / 100.0)
    assert formulas.coin_flip(probability)
    coderack.new_codelet("description-builder", codelet, strength)


def description_builder(codelet):
    description = codelet.arguments[0]
    assert description.object in workspace.objects
    if description.object.described(description.descriptor):
        description.description_type.buffer = 100.0
        description.descriptor.buffer = 100.0
    else:
        description.build()


def bottom_up_bond_scout(codelet):
    source = choose_unmodified_object("intra_string_salience", workspace.objects)
    __show_which_string_object_is_from(source)
    destination = choose_neighbour(source)
    assert destination
    logging.info(f"destination: {destination}")
    bond_facet = __get_bond_facet(source, destination)
    logging.info(f"chosen bond facet: {bond_facet.get_name()}")
    logging.info(f"Source: {source}, destination: {destination}")
    bond_descriptors = __get_descriptors(bond_facet, source, destination)
    source_descriptor, destination_descriptor = bond_descriptors
    logging.info(f"source descriptor: {source_descriptor.name.upper()}")
    logging.info(f"destination descriptor: {destination_descriptor.name.upper()}")
    category = source_descriptor.get_bond_category(destination_descriptor)
    assert category
    if category == slipnet.identity:
        category = slipnet.sameness
    logging.info(f"proposing {category.name} bond ")
    coderack.propose_bond(
        source,
        destination,
        category,
        bond_facet,
        source_descriptor,
        destination_descriptor,
        codelet,
    )


def rule_scout(codelet):
    assert workspace.number_of_unreplaced_objects() == 0
    changed_objects = [o for o in workspace.initial.objects if o.changed]
    # assert len(changed_objects) < 2
    # if there are no changed objects, propose a rule with no changes
    if not changed_objects:
        return coderack.propose_rule(None, None, None, None, codelet)

    changed = changed_objects[-1]
    # generate a list of distinguishing descriptions for the first object
    # ie. string-position (left-,right-most,middle or whole) or letter category
    # if it is the only one of its type in the string
    object_list = []
    position = changed.get_descriptor(slipnet.string_position_category)
    if position:
        object_list += [position]
    letter = changed.get_descriptor(slipnet.letter_category)
    other_objects_of_same_letter = [
        o
        for o in workspace.initial.objects
        if not o != changed and o.get_description_type(letter)
    ]
    if not len(other_objects_of_same_letter):
        object_list += [letter]
    # if this object corresponds to another object in the workspace
    # object_list = the union of this and the distingushing descriptors
    if changed.correspondence:
        target_object = changed.correspondence.object_from_target
        new_list = []
        slippages = workspace.slippages()
        for node in object_list:
            node = node.apply_slippages(slippages)
            if target_object.described(node):
                if target_object.distinguishing_descriptor(node):
                    new_list += [node]
        object_list = new_list  # should this be += ??
    assert object_list
    # use conceptual depth to choose a description
    value_list = []
    for node in object_list:
        depth = node.conceptual_depth
        value = formulas.temperature_adjusted_value(depth)
        value_list += [value]
    i = formulas.select_list_position(value_list)
    descriptor = object_list[i]
    # choose the relation (change the letmost object to "successor" or "d"
    object_list = []
    if changed.replacement.relation:
        object_list += [changed.replacement.relation]
    object_list += [
        changed.replacement.object_from_modified.get_descriptor(slipnet.letter_category)
    ]
    # use conceptual depth to choose a relation
    value_list = []
    for node in object_list:
        depth = node.conceptual_depth
        value = formulas.temperature_adjusted_value(depth)
        value_list += [value]
    i = formulas.select_list_position(value_list)
    relation = object_list[i]
    coderack.propose_rule(
        slipnet.letter_category, descriptor, slipnet.letter, relation, codelet
    )


def rule_strength_tester(codelet):
    rule = codelet.arguments[0]
    rule.update_strength()
    probability = formulas.temperature_adjusted_probability(rule.total_strength / 100.0)
    assert random.random() <= probability
    coderack.new_codelet("rule-builder", codelet, rule.total_strength, rule)


def replacement_finder():
    # choose random letter in initial string
    letters = [o for o in workspace.initial.objects if isinstance(o, Letter)]
    letter_of_initial_string = random.choice(letters)
    logging.info(f"selected letter in initial string = {letter_of_initial_string}")
    if letter_of_initial_string.replacement:
        logging.info(
            f"Replacement already found for {letter_of_initial_string}, so fizzling"
        )
        return
    position = letter_of_initial_string.left_index
    more_letters = [
        o
        for o in workspace.modified.objects
        if isinstance(o, Letter) and o.left_index == position
    ]
    letter_of_modified_string = more_letters and more_letters[0] or None
    assert letter_of_modified_string
    position -= 1
    initial_ascii = ord(workspace.initial_string[position])
    modified_ascii = ord(workspace.modified_string[position])
    diff = initial_ascii - modified_ascii
    if abs(diff) < 2:
        relations = {0: slipnet.sameness, -1: slipnet.successor, 1: slipnet.predecessor}
        relation = relations[diff]
        logging.info(f"Relation found: {relation.name}")
    else:
        relation = None
        logging.info("no relation found")
    letter_of_initial_string.replacement = Replacement(
        letter_of_initial_string, letter_of_modified_string, relation
    )
    if relation != slipnet.sameness:
        letter_of_initial_string.changed = True
        workspace.changed_object = letter_of_initial_string
    logging.info("building replacement")


def top_down_bond_scout__category(codelet):
    logging.info("top_down_bond_scout__category")
    category = codelet.arguments[0]
    source = __get_scout_source(category, formulas.local_bond_category_relevance, "bond")
    destination = choose_neighbour(source)
    logging.info(f"source: {source}, destination: {destination}")
    assert destination
    bond_facet = __get_bond_facet(source, destination)
    source_descriptor, destination_descriptor = __get_descriptors(
        bond_facet, source, destination
    )
    forward_bond = source_descriptor.get_bond_category(destination_descriptor)
    if forward_bond == slipnet.identity:
        forward_bond = slipnet.sameness
        backward_bond = slipnet.sameness
    else:
        backward_bond = destination_descriptor.get_bond_category(source_descriptor)
    assert category in [forward_bond, backward_bond]
    if category == forward_bond:
        coderack.propose_bond(
            source,
            destination,
            category,
            bond_facet,
            source_descriptor,
            destination_descriptor,
            codelet,
        )
    else:
        coderack.propose_bond(
            destination,
            source,
            category,
            bond_facet,
            destination_descriptor,
            source_descriptor,
            codelet,
        )


def top_down_bond_scout__direction(codelet):
    direction = codelet.arguments[0]
    source = __get_scout_source(
        direction, formulas.local_direction_category_relevance, "bond"
    )
    destination = choose_directed_neighbor(source, direction)
    assert destination
    logging.info(f"to object: {destination}")
    bond_facet = __get_bond_facet(source, destination)
    source_descriptor, destination_descriptor = __get_descriptors(
        bond_facet, source, destination
    )
    category = source_descriptor.get_bond_category(destination_descriptor)
    assert category
    if category == slipnet.identity:
        category = slipnet.sameness
    coderack.propose_bond(
        source,
        destination,
        category,
        bond_facet,
        source_descriptor,
        destination_descriptor,
        codelet,
    )


def bond_strength_tester(codelet):
    bond = codelet.arguments[0]
    __show_which_string_object_is_from(bond)
    bond.update_strength()
    strength = bond.total_strength
    probability = formulas.temperature_adjusted_probability(strength / 100.0)
    logging.info(f"bond strength = {strength} for {bond}")
    assert formulas.coin_flip(probability)
    bond.facet.buffer = 100.0
    bond.source_descriptor.buffer = 100.0
    bond.destination_descriptor.buffer = 100.0
    logging.info("succeeded: posting bond-builder")
    coderack.new_codelet("bond-builder", codelet, strength)


def bond_builder(codelet):
    bond = codelet.arguments[0]
    __show_which_string_object_is_from(bond)
    bond.update_strength()
    assert bond.source in workspace.objects or bond.destination in workspace.objects
    for string_bond in bond.string.bonds:
        if bond.same_neighbours(string_bond) and bond.same_categories(string_bond):
            if bond.direction_category:
                bond.direction_category.buffer = 100.0
            bond.category.buffer = 100.0
            logging.info("already exists: activate descriptors & Fizzle")
            return
    incompatible_bonds = bond.get_incompatible_bonds()
    logging.info(f"number of incompatible_bonds: {len(incompatible_bonds)}")
    if len(incompatible_bonds):
        logging.info(str(incompatible_bonds[0]))
    assert __fight_incompatibles(incompatible_bonds, bond, "bonds", 1.0, 1.0)
    incompatible_groups = bond.source.get_common_groups(bond.destination)
    assert __fight_incompatibles(incompatible_groups, bond, "groups", 1.0, 1.0)
    # fight all incompatible correspondences
    incompatible_correspondences = []
    if bond.left_object.leftmost or bond.right_object.rightmost:
        if bond.direction_category:
            incompatible_correspondences = bond.get_incompatible_correspondences()
            if incompatible_correspondences:
                logging.info("trying to break incompatible correspondences")
                assert __fight(bond, 2.0, incompatible_correspondences, 3.0)
    for incompatible in incompatible_bonds:
        incompatible.break_the_structure()
    for incompatible in incompatible_groups:
        incompatible.break_the_structure()
    for incompatible in incompatible_correspondences:
        incompatible.break_the_structure()
    logging.info(f"building bond {bond}")
    bond.build_bond()


# pylint: disable=too-many-branches
# pylint: disable=too-many-statements
def top_down_group_scout__category(codelet):
    group_category = codelet.arguments[0]
    category = group_category.get_related_node(slipnet.bond_category)
    assert category
    source = __get_scout_source(category, formulas.local_bond_category_relevance, "group")
    assert source
    assert not source.spans_string()
    if source.leftmost:
        direction = slipnet.right
    elif source.rightmost:
        direction = slipnet.left
    else:
        activations = [slipnet.left.activation]
        activations += [slipnet.right.activation]
        if not formulas.select_list_position(activations):
            direction = slipnet.left
        else:
            direction = slipnet.right
    if direction == slipnet.left:
        first_bond = source.left_bond
    else:
        first_bond = source.right_bond
    if not first_bond or first_bond.category != category:
        # check the other side of object
        if direction == slipnet.right:
            first_bond = source.left_bond
        else:
            first_bond = source.right_bond
        if not first_bond or first_bond.category != category:
            if category == slipnet.sameness and isinstance(source, Letter):
                group = Group(
                    source.string,
                    slipnet.sameness_group,
                    None,
                    slipnet.letter_category,
                    [source],
                    [],
                )
                probability = group.single_letter_group_probability()
                assert random.random() >= probability
                coderack.propose_single_letter_group(source, codelet)
        return
    direction = first_bond.direction_category
    search = True
    bond_facet = None
    # find leftmost object in group with these bonds
    while search:
        search = False
        if not source.left_bond:
            continue
        if source.left_bond.category != category:
            continue
        if source.left_bond.direction_category != direction:
            if source.left_bond.direction_category:
                continue
        if not bond_facet or bond_facet == source.left_bond.facet:
            bond_facet = source.left_bond.facet
            direction = source.left_bond.direction_category
            source = source.left_bond.left_object
            search = True
    # find rightmost object in group with these bonds
    search = True
    destination = source
    while search:
        search = False
        if not destination.right_bond:
            continue
        if destination.right_bond.category != category:
            continue
        if destination.right_bond.direction_category != direction:
            if destination.right_bond.direction_category:
                continue
        if not bond_facet or bond_facet == destination.right_bond.facet:
            bond_facet = destination.right_bond.facet
            direction = source.right_bond.direction_category
            destination = destination.right_bond.right_object
            search = True
    assert destination != source
    objects = [source]
    bonds = []
    while source != destination:
        bonds += [source.right_bond]
        objects += [source.right_bond.right_object]
        source = source.right_bond.right_object
    coderack.propose_group(objects, bonds, group_category, direction, bond_facet, codelet)


def top_down_group_scout__direction(codelet):
    direction = codelet.arguments[0]
    source = __get_scout_source(
        direction, formulas.local_direction_category_relevance, "direction"
    )
    logging.info(f"source chosen = {source}")
    assert not source.spans_string()
    if source.leftmost:
        mydirection = slipnet.right
    elif source.rightmost:
        mydirection = slipnet.left
    else:
        activations = [slipnet.left.activation]
        activations += [slipnet.right.activation]
        if not formulas.select_list_position(activations):
            mydirection = slipnet.left
        else:
            mydirection = slipnet.right
    if mydirection == slipnet.left:
        first_bond = source.left_bond
    else:
        first_bond = source.right_bond
    if not first_bond:
        logging.info("no first_bond")
    else:
        logging.info(f"first_bond: {first_bond}")
    if first_bond and not first_bond.direction_category:
        direction = None
    if not first_bond or first_bond.direction_category != direction:
        if mydirection == slipnet.right:
            first_bond = source.left_bond
        else:
            first_bond = source.right_bond
        if not first_bond:
            logging.info("no first_bond2")
        else:
            logging.info(f"first_bond2: {first_bond}")
        if first_bond and not first_bond.direction_category:
            direction = None
        assert first_bond
        assert first_bond.direction_category == direction
    logging.info(f"possible group: {first_bond}")
    category = first_bond.category
    assert category
    group_category = category.get_related_node(slipnet.group_category)
    logging.info(f"trying from {source} to {category.name}")
    bond_facet = None
    # find leftmost object in group with these bonds
    search = True
    while search:
        search = False
        if not source.left_bond:
            continue
        if source.left_bond.category != category:
            continue
        if source.left_bond.direction_category != direction:
            if source.left_bond.direction_category:
                continue
        if not bond_facet or bond_facet == source.left_bond.facet:
            bond_facet = source.left_bond.facet
            direction = source.left_bond.direction_category
            source = source.left_bond.left_object
            search = True
    destination = source
    search = True
    while search:
        search = False
        if not destination.right_bond:
            continue
        if destination.right_bond.category != category:
            continue
        if destination.right_bond.direction_category != direction:
            if destination.right_bond.direction_category:
                continue
        if not bond_facet or bond_facet == destination.right_bond.facet:
            bond_facet = destination.right_bond.facet
            direction = source.right_bond.direction_category
            destination = destination.right_bond.right_object
            search = True
    assert destination != source
    logging.info(f"proposing group from {source} to {destination}")
    objects = [source]
    bonds = []
    while source != destination:
        bonds += [source.right_bond]
        objects += [source.right_bond.right_object]
        source = source.right_bond.right_object
    coderack.propose_group(objects, bonds, group_category, direction, bond_facet, codelet)


# noinspection PyStringFormat
def group_scout__whole_string(codelet):
    string = workspace.initial
    if random.random() > 0.5:
        string = workspace.target
        logging.info(f"target string selected: {workspace.target}")
    else:
        logging.info(f"initial string selected: {workspace.initial}")
    # find leftmost object & the highest group to which it belongs
    leftmost = None
    for objekt in string.objects:
        if objekt.leftmost:
            leftmost = objekt
    while leftmost.group and leftmost.group.bond_category == slipnet.sameness:
        leftmost = leftmost.group
    if leftmost.spans_string():
        # the object already spans the string - propose this object
        group = leftmost
        coderack.propose_group(
            group.object_list,
            group.bond_list,
            group.group_category,
            group.direction_category,
            group.facet,
            codelet,
        )
        return
    bonds = []
    objects = [leftmost]
    while leftmost.right_bond:
        bonds += [leftmost.right_bond]
        leftmost = leftmost.right_bond.right_object
        objects += [leftmost]
    assert leftmost.rightmost
    # choose a random bond from list
    chosen_bond = random.choice(bonds)
    category = chosen_bond.category
    direction_category = chosen_bond.direction_category
    bond_facet = chosen_bond.facet
    bonds = possible_group_bonds(category, direction_category, bond_facet, bonds)
    assert bonds
    group_category = category.get_related_node(slipnet.group_category)
    coderack.propose_group(
        objects, bonds, group_category, direction_category, bond_facet, codelet
    )


def group_strength_tester(codelet):
    # update strength value of the group
    group = codelet.arguments[0]
    __show_which_string_object_is_from(group)
    group.update_strength()
    strength = group.total_strength
    probability = formulas.temperature_adjusted_probability(strength / 100.0)
    assert random.random() <= probability
    # it is strong enough - post builder  & activate nodes
    group.group_category.get_related_node(slipnet.bond_category).buffer = 100.0
    if group.direction_category:
        group.direction_category.buffer = 100.0
    coderack.new_codelet("group-builder", codelet, strength)


def group_builder(codelet):
    # update strength value of the group
    group = codelet.arguments[0]
    __show_which_string_object_is_from(group)
    equivalent = group.string.equivalent_group(group)
    if equivalent:
        logging.info("already exists...activate descriptors & fizzle")
        group.activate_descriptions()
        equivalent.add_descriptions(group.descriptions)
        return
    # check to see if all objects are still there
    for o in group.object_list:
        assert o in workspace.objects
    # check to see if bonds are there of the same direction
    incompatible_bonds = []  # incompatible bond list
    if len(group.object_list) > 1:
        previous = group.object_list[0]
        for objekt in group.object_list[1:]:
            left_bond = objekt.left_bond
            if left_bond:
                if left_bond.left_object == previous:
                    continue
                if left_bond.direction_category == group.direction_category:
                    continue
                incompatible_bonds += [left_bond]
            previous = objekt
        next_object = group.object_list[-1]
        for objekt in reversed(group.object_list[:-1]):
            right_bond = objekt.right_bond
            if right_bond:
                if right_bond.right_object == next_object:
                    continue
                if right_bond.direction_category == group.direction_category:
                    continue
                incompatible_bonds += [right_bond]
            next_object = objekt
    # if incompatible bonds exist - fight
    group.update_strength()
    assert __fight_incompatibles(incompatible_bonds, group, "bonds", 1.0, 1.0)
    # fight incompatible groups
    # fight all groups containing these objects
    incompatible_groups = group.get_incompatible_groups()
    assert __fight_incompatibles(incompatible_groups, group, "Groups", 1.0, 1.0)
    for incompatible in incompatible_bonds:
        incompatible.break_the_structure()
    # create new bonds
    group.bond_list = []
    for i in range(1, len(group.object_list)):
        object1 = group.object_list[i - 1]
        object2 = group.object_list[i]
        if not object1.right_bond:
            if group.direction_category == slipnet.right:
                source = object1
                destination = object2
            else:
                source = object2
                destination = object1
            category = group.group_category.get_related_node(slipnet.bond_category)
            facet = group.facet
            new_bond = Bond(
                source,
                destination,
                category,
                facet,
                source.get_descriptor(facet),
                destination.get_descriptor(facet),
            )
            new_bond.build_bond()
        group.bond_list += [object1.right_bond]
    for incompatible in incompatible_groups:
        incompatible.break_the_structure()
    group.build_group()
    group.activate_descriptions()
    logging.info("building group")


def rule_builder(codelet):
    rule = codelet.arguments[0]
    if rule.rule_equal(workspace.rule):
        rule.activate_rule_descriptions()
        return
    rule.update_strength()
    assert rule.total_strength
    # fight against other rules
    if workspace.rule:
        assert __structure_versus_structure(rule, 1.0, workspace.rule, 1.0)
    workspace.build_rule(rule)


def __get_cut_off(density):
    if density > 0.8:
        distribution = [5.0, 150.0, 5.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    elif density > 0.6:
        distribution = [2.0, 5.0, 150.0, 5.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    elif density > 0.4:
        distribution = [1.0, 2.0, 5.0, 150.0, 5.0, 2.0, 1.0, 1.0, 1.0, 1.0]
    elif density > 0.2:
        distribution = [1.0, 1.0, 2.0, 5.0, 150.0, 5.0, 2.0, 1.0, 1.0, 1.0]
    else:
        distribution = [1.0, 1.0, 1.0, 2.0, 5.0, 150.0, 5.0, 2.0, 1.0, 1.0]
    stop = sum(distribution) * random.random()
    total = 0.0
    for i in range(0, len(distribution)):
        total += distribution[i]
        if total >= stop:
            return i + 1
    return len(distribution)


def rule_translator():
    assert workspace.rule
    if len(workspace.initial) == 1 and len(workspace.target) == 1:
        bond_density = 1.0
    else:
        number_of_bonds = len(workspace.initial.bonds) + len(workspace.target.bonds)
        nearly_total_length = len(workspace.initial) + len(workspace.target) - 2
        bond_density = number_of_bonds / nearly_total_length
        if bond_density > 1.0:
            bond_density = 1.0
    cutoff = __get_cut_off(bond_density) * 10.0
    assert cutoff >= formulas.actual_temperature
    if workspace.rule.build_translated_rule():
        workspace.found_answer = True
    else:
        temperature.clamp_time = coderack.codelets_run + 100
        temperature.clamped = True
        formulas.Temperature = 100.0


def bottom_up_correspondence_scout(codelet):
    object_from_initial = choose_unmodified_object(
        "inter_string_salience", workspace.initial.objects
    )
    object_from_target = choose_unmodified_object(
        "inter_string_salience", workspace.target.objects
    )
    assert object_from_initial.spans_string() == object_from_target.spans_string()
    # get the posible concept mappings
    concept_mappings = formulas.get_mappings(
        object_from_initial,
        object_from_target,
        object_from_initial.relevant_descriptions(),
        object_from_target.relevant_descriptions(),
    )
    assert concept_mappings
    assert __slippability(concept_mappings)
    # find out if any are distinguishing
    distinguishing_mappings = [m for m in concept_mappings if m.distinguishing()]
    assert distinguishing_mappings
    # if both objects span the strings, check to see if the
    # string description needs to be flipped
    opposites = [
        m
        for m in distinguishing_mappings
        if m.initial_description_type == slipnet.string_position_category
        and m.initial_description_type != slipnet.bond_facet
    ]
    initial_description_types = [m.initial_description_type for m in opposites]
    flip_target_object = False
    if (
        object_from_initial.spans_string()
        and object_from_target.spans_string()
        and slipnet.direction_category in initial_description_types
        and __all_opposite_mappings(formulas.opposite_mappings)
        and slipnet.opposite.activation != 100.0
    ):
        object_from_target = object_from_target.flipped_version()
        concept_mappings = formulas.get_mappings(
            object_from_initial,
            object_from_target,
            object_from_initial.relevant_descriptions(),
            object_from_target.relevant_descriptions(),
        )
        flip_target_object = True
    coderack.propose_correspondence(
        object_from_initial, object_from_target, concept_mappings, flip_target_object, codelet
    )


def important_object_correspondence_scout(codelet):
    object_from_initial = choose_unmodified_object(
        "relative_importance", workspace.initial.objects
    )
    descriptors = object_from_initial.relevant_distinguishing_descriptors()
    slipnode = formulas.choose_slipnode_by_conceptual_depth(descriptors)
    assert slipnode
    initial_descriptor = slipnode
    for mapping in workspace.slippages():
        if mapping.initial_descriptor == slipnode:
            initial_descriptor = mapping.target_descriptor
    target_candidates = []
    for objekt in workspace.target.objects:
        for description in objekt.relevant_descriptions():
            if description.descriptor == initial_descriptor:
                target_candidates += [objekt]
    assert target_candidates
    object_from_target = choose_unmodified_object("inter_string_salience", target_candidates)
    assert object_from_initial.spans_string() == object_from_target.spans_string()
    # get the posible concept mappings
    concept_mappings = formulas.get_mappings(
        object_from_initial,
        object_from_target,
        object_from_initial.relevant_descriptions(),
        object_from_target.relevant_descriptions(),
    )
    assert concept_mappings
    assert __slippability(concept_mappings)
    # find out if any are distinguishing
    distinguishing_mappings = [m for m in concept_mappings if m.distinguishing()]
    assert distinguishing_mappings
    # if both objects span the strings, check to see if the
    # string description needs to be flipped
    opposites = [
        m
        for m in distinguishing_mappings
        if m.initial_description_type == slipnet.string_position_category
        and m.initial_description_type != slipnet.bond_facet
    ]
    initial_description_types = [m.initial_description_type for m in opposites]
    flip_target_object = False
    if (
        object_from_initial.spans_string()
        and object_from_target.spans_string()
        and slipnet.direction_category in initial_description_types
        and __all_opposite_mappings(formulas.opposite_mappings)
        and slipnet.opposite.activation != 100.0
    ):
        object_from_target = object_from_target.flipped_version()
        concept_mappings = formulas.get_mappings(
            object_from_initial,
            object_from_target,
            object_from_initial.relevant_descriptions(),
            object_from_target.relevant_descriptions(),
        )
        flip_target_object = True
    coderack.propose_correspondence(
        object_from_initial, object_from_target, concept_mappings, flip_target_object, codelet
    )


def correspondence_strength_tester(codelet):
    correspondence = codelet.arguments[0]
    object_from_initial = correspondence.object_from_initial
    object_from_target = correspondence.object_from_target
    assert object_from_initial in workspace.objects
    assert (
        object_from_target in workspace.objects
        or correspondence.flip_target_object
        and not workspace.target.equivalent_group(object_from_target.flipped_version())
    )
    correspondence.update_strength()
    strength = correspondence.total_strength
    probability = formulas.temperature_adjusted_probability(strength / 100.0)
    assert random.random() <= probability
    # activate some concepts
    for mapping in correspondence.concept_mappings:
        mapping.initial_description_type.buffer = 100.0
        mapping.initial_descriptor.buffer = 100.0
        mapping.target_description_type.buffer = 100.0
        mapping.target_descriptor.buffer = 100.0
    coderack.new_codelet("correspondence-builder", codelet, strength, correspondence)


def correspondence_builder(codelet):
    correspondence = codelet.arguments[0]
    object_from_initial = correspondence.object_from_initial
    object_from_target = correspondence.object_from_target
    want_flip = correspondence.flip_target_object
    if want_flip:
        flipper = object_from_target.flipped_version()
        target_not_flipped = not workspace.target.equivalent_group(flipper)
    else:
        target_not_flipped = False
    initial_in_objects = object_from_initial in workspace.objects
    target_in_objects = object_from_target in workspace.objects
    assert initial_in_objects or (
        not target_in_objects and (not (want_flip and target_not_flipped))
    )
    if correspondence.reflexive():
        # if the correspondence exists, activate concept mappings
        # and add new ones to the existing corr.
        existing = correspondence.object_from_initial.correspondence
        for mapping in correspondence.concept_mappings:
            if mapping.label:
                mapping.label.buffer = 100.0
            if not mapping.is_contained_by(existing.concept_mappings):
                existing.concept_mappings += [mapping]
        return
    incompatibles = correspondence.get_incompatible_correspondences()
    # fight against all correspondences
    if incompatibles:
        correspondence_spans = (
            correspondence.object_from_initial.letter_span()
            + correspondence.object_from_target.letter_span()
        )
        for incompatible in incompatibles:
            incompatible_spans = (
                incompatible.object_from_initial.letter_span()
                + incompatible.object_from_target.letter_span()
            )
            assert __structure_versus_structure(
                correspondence, correspondence_spans, incompatible, incompatible_spans
            )
    incompatible_bond = None
    incompatible_group = None
    # if there is an incompatible bond then fight against it
    initial = correspondence.object_from_initial
    target = correspondence.object_from_target
    if initial.leftmost or initial.rightmost and target.leftmost or target.rightmost:
        # search for the incompatible bond
        incompatible_bond = correspondence.get_incompatible_bond()
        if incompatible_bond:
            # bond found - fight against it
            assert __structure_versus_structure(correspondence, 3.0, incompatible_bond, 2.0)
            # won against incompatible bond
            incompatible_group = target.group
            if incompatible_group:
                assert __structure_versus_structure(
                    correspondence, 1.0, incompatible_group, 1.0
                )
    # if there is an incompatible rule, fight against it
    incompatible_rule = None
    if workspace.rule:
        if workspace.rule.incompatible_rule_correspondence(correspondence):
            incompatible_rule = workspace.rule
            assert __structure_versus_structure(correspondence, 1.0, incompatible_rule, 1.0)
    for incompatible in incompatibles:
        incompatible.break_the_structure()
    # break incompatible group and bond if they exist
    if incompatible_bond:
        incompatible_bond.break_the_structure()
    if incompatible_group:
        incompatible_group.break_the_structure()
    if incompatible_rule:
        workspace.break_rule()
    correspondence.build_correspondence()
