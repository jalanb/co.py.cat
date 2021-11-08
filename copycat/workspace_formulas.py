import logging

from . import formulas
from .slipnet import slipnet
from .temperature import temperature
from .workspace import workspace


class WorkspaceFormulas:
    def __init__(self):
        self.clamp_temperature = False

    def update_temperature(self):
        logging.debug("update_temperature")
        workspace.assess_temperature()
        rule_weakness = 100.0
        if workspace.rule:
            workspace.rule.update_strength()
            rule_weakness = 100.0 - workspace.rule.total_strength
        values = ((workspace.total_unhappiness, 0.8), (rule_weakness, 0.2))
        formulas.log_actual_temperature()
        if temperature.clamped:
            formulas.clamp_actual_temperature()
        else:
            formulas.weigh_actual_temperature(values)
        logging.info(
            f"unhappiness: {workspace.total_unhappiness + 0.001}, "
            f"weakness: {rule_weakness + 0.001}"
        )
        temperature.update(formulas.actual_temperature)
        if not self.clamp_temperature:
            formulas.Temperature = formulas.actual_temperature
        temperature.update(formulas.Temperature)


workspace_formulas = WorkspaceFormulas()


def number_of_objects():
    return len(workspace.objects)


def choose_unmodified_object(attribute, in_objects):
    objects = [o for o in in_objects if o.string != workspace.modified]
    if not len(objects):
        logging.error("no objects available in initial or target strings")
    return formulas.choose_object_from_list(objects, attribute)


def choose_neighbour(source):
    objects = []
    for object_ in workspace.objects:
        if object_.string != source.string:
            continue
        if object_.left_index == source.right_index + 1:
            objects += [object_]
        elif source.left_index == object_.right_index + 1:
            objects += [object_]
    return formulas.choose_object_from_list(objects, "intra_string_salience")


def choose_directed_neighbor(source, direction):
    if direction == slipnet.left:
        logging.info("Left")
        return __choose_left_neighbor(source)
    logging.info("Right")
    return __choose_right_neighbor(source)


def __choose_left_neighbor(source):
    objects = []
    for o in workspace.objects:
        if o.string == source.string:
            if source.left_index == o.right_index + 1:
                logging.info(f"{o} is on left of {source}")
                objects += [o]
            else:
                logging.info("{o} is not on left of {source}")
    logging.info(f"Number of left objects: {len(objects)}")
    return formulas.choose_object_from_list(objects, "intra_string_salience")


def __choose_right_neighbor(source):
    objects = [
        o
        for o in workspace.objects
        if o.string == source.string and o.left_index == source.right_index + 1
    ]
    return formulas.choose_object_from_list(objects, "intra_string_salience")


def choose_bond_facet(source, destination):
    source_facets = [
        d.description_type
        for d in source.descriptions
        if d.description_type in slipnet.bond_facets
    ]
    bond_facets = [
        d.description_type
        for d in destination.descriptions
        if d.description_type in source_facets
    ]
    if not bond_facets:
        return None
    supports = [__support_for_description_type(f, source.string) for f in bond_facets]
    i = formulas.select_list_position(supports)
    return bond_facets[i]


def __support_for_description_type(description_type, string):
    string_support = __description_type_support(description_type, string)
    return (description_type.activation + string_support) / 2


def __description_type_support(description_type, string):
    """The proportion of objects in the string with this description_type"""
    described_count = total = 0
    for object_ in workspace.objects:
        if object_.string == string:
            total += 1
            for description in object_.descriptions:
                if description.description_type == description_type:
                    described_count += 1
    return described_count / float(total)


def probability_of_posting(codelet_name):
    if codelet_name == "breaker":
        return 1.0
    if "description" in codelet_name:
        result = (formulas.Temperature / 100.0) ** 2
    else:
        result = workspace.intra_string_unhappiness / 100.0
    if "correspondence" in codelet_name:
        result = workspace.inter_string_unhappiness / 100.0
    if "replacement" in codelet_name:
        if workspace.number_of_unreplaced_objects() > 0:
            return 1.0
        return 0.0
    if "rule" in codelet_name:
        if not workspace.rule:
            return 1.0
        return workspace.rule.total_weakness() / 100.0
    if "translator" in codelet_name:
        if not workspace.rule:
            assert 0
            return 0.0
        assert 0
        return 1.0
    return result


def how_many_to_post(codelet_name):
    if codelet_name == "breaker" or "description" in codelet_name:
        return 1
    if "translator" in codelet_name:
        if not workspace.rule:
            return 0
        return 1
    if "rule" in codelet_name:
        return 2
    if "group" in codelet_name and not workspace.number_of_bonds():
        return 0
    if "replacement" in codelet_name and workspace.rule:
        return 0
    number = 0
    if "bond" in codelet_name:
        number = workspace.number_of_unrelated_objects()
    if "group" in codelet_name:
        number = workspace.number_of_ungrouped_objects()
    if "replacement" in codelet_name:
        number = workspace.number_of_unreplaced_objects()
    if "correspondence" in codelet_name:
        number = workspace.number_of_uncorresponding_objects()
    if number < formulas.blur(2.0):
        return 1
    if number < formulas.blur(4.0):
        return 2
    return 3
