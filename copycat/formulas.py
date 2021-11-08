import logging
import math
import random

from .temperature import temperature

actual_temperature = Temperature = 100.0


def select_list_position(probabilities):
    total = sum(probabilities)
    logging.info(f"Total of probabilities: {total}")
    r = random.random()
    stop_position = total * r
    logging.info(f"stop_position: {stop_position}")
    total = 0
    i = 0
    for probability in probabilities:
        total += probability
        if total > stop_position:
            return i
        i += 1
    return 0


def weighted_average(values):
    total = 0.0
    total_weights = 0.0
    for value, weight in values:
        total += value * weight
        total_weights += weight
    if not total_weights:
        return 0.0
    return total / total_weights


def log_temperature():
    logging.info(f"Temperature: {Temperature}")


def log_actual_temperature():
    logging.info(f"actual_temperature: {actual_temperature}")


def clamp_actual_temperature(values):
    global actual_temperature
    actual_temperature = 100.0
    log_actual_temperature()


def weigh_actual_temperature(values):
    global actual_temperature
    actual_temperature = weighted_average(values)
    log_actual_temperature()


def temperature_adjusted_value(value):
    log_temperature()
    log_actual_temperature()
    return value ** (((100.0 - Temperature) / 30.0) + 0.5)


def temperature_adjusted_probability(value):
    if not value or value == 0.5 or not temperature.value:
        return value
    if value < 0.5:
        return 1.0 - temperature_adjusted_probability(1.0 - value)
    coldness = 100.0 - temperature.value
    a = math.sqrt(coldness)
    b = 10.0 - a
    c = b / 100
    d = c * (1.0 - (1.0 - value))  # as said the java
    e = (1.0 - value) + d
    f = 1.0 - e
    return max(f, 0.5)


def coin_flip(chance=0.5):
    return random.random() < chance


def blur(value):
    root = math.sqrt(value)
    if coin_flip():
        return value + root
    return value - root


def choose_object_from_list(objects, attribute):
    if not objects:
        return None
    probabilities = []
    for objekt in objects:
        value = getattr(objekt, attribute)
        probability = temperature_adjusted_value(value)
        logging.info(
            f"Object: {objekt}, value: {value}, probability: {probability}"
        )
        probabilities += [probability]
    selected = select_list_position(probabilities)
    logging.info(f"Selected: {selected}")
    return objects[selected]


def choose_relevant_description_by_activation(workspace_object):
    descriptions = workspace_object.relevant_descriptions()
    if not descriptions:
        return None
    activations = [description.descriptor.activation for description in descriptions]
    selected = select_list_position(activations)
    return descriptions[selected]


def similar_property_links(slip_node):
    result = []
    for slip_link in slip_node.property_links:
        association = slip_link.degree_of_association() / 100.0
        probability = temperature_adjusted_probability(association)
        if coin_flip(probability):
            result += [slip_link]
    return result


def choose_slipnode_by_conceptual_depth(slip_nodes):
    if not slip_nodes:
        return None
    depths = [temperature_adjusted_value(n.conceptual_depth) for n in slip_nodes]
    selected = select_list_position(depths)
    return slip_nodes[selected]


def __relevant_category(objekt, slipnode):
    return objekt.right_bond and objekt.right_bond.category == slipnode


def __relevant_direction(objekt, slipnode):
    return objekt.right_bond and objekt.right_bond.direction_category == slipnode


def __local_relevance(string, slipnode, relevance):
    number_of_objects_not_spanning = number_of_matches = 0.0
    logging.info(f"find relevance for a string: {string}")
    for objekt in string.objects:
        if not objekt.spans_string():
            logging.info(f"Non spanner: {objekt}")
            number_of_objects_not_spanning += 1.0
            if relevance(objekt, slipnode):
                number_of_matches += 1.0
    if number_of_objects_not_spanning == 1:
        return 100.0 * number_of_matches
    return 100.0 * number_of_matches / (number_of_objects_not_spanning - 1.0)


def local_bond_category_relevance(string, category):
    if len(string.objects) == 1:
        return 0.0
    return __local_relevance(string, category, __relevant_category)


def local_direction_category_relevance(string, direction):
    return __local_relevance(string, direction, __relevant_direction)


def get_mappings(
    object_from_initial, object_from_target, initial_descriptions, target_descriptions
):
    mappings = []
    from .concept_mapping import ConceptMapping

    for initial in initial_descriptions:
        for target in target_descriptions:
            if initial.description_type == target.description_type:
                if (
                    initial.descriptor == target.descriptor
                    or initial.descriptor.slip_linked(target.descriptor)
                ):
                    mapping = ConceptMapping(
                        initial.description_type,
                        target.description_type,
                        initial.descriptor,
                        target.descriptor,
                        object_from_initial,
                        object_from_target,
                    )
                    mappings += [mapping]
    return mappings
