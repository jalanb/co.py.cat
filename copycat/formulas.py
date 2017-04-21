import math
import logging
import random

from temperature import temperature

actualTemperature = Temperature = 100.0


def selectListPosition(probabilities):
    total = sum(probabilities)
    logging.info('total: %s', total)
    r = random.random()
    stopPosition = total * r
    logging.info('stopPosition: %s', stopPosition)
    total = 0
    i = 0
    for probability in probabilities:
        total += probability
        if total > stopPosition:
            return i
        i += 1
    return 0


def weightedAverage(values):
    total = 0.0
    totalWeights = 0.0
    for value, weight in values:
        total += value * weight
        totalWeights += weight
    if not totalWeights:
        return 0.0
    return total / totalWeights


def temperatureAdjustedValue(value):
    logging.info('Temperature: %s', Temperature)
    logging.info('actualTemperature: %s', actualTemperature)
    return value ** (((100.0 - Temperature) / 30.0) + 0.5)


def temperatureAdjustedProbability(value):
    if not value or value == 0.5 or not temperature.value:
        return value
    if value < 0.5:
        return 1.0 - temperatureAdjustedProbability(1.0 - value)
    coldness = 100.0 - temperature.value
    a = math.sqrt(coldness)
    b = 10.0 - a
    c = b / 100
    d = c * (1.0 - (1.0 - value))  # as said the java
    e = (1.0 - value) + d
    f = 1.0 - e
    return max(f, 0.5)


def coinFlip(chance=0.5):
    return random.random() < chance


def blur(value):
    root = math.sqrt(value)
    if coinFlip():
        return value + root
    return value - root


def chooseObjectFromList(objects, attribute):
    if not objects:
        return None
    probabilities = []
    for objekt in objects:
        value = getattr(objekt, attribute)
        probability = temperatureAdjustedValue(value)
        logging.info('Object: %s, value: %d, probability: %d',
                     objekt, value, probability)
        probabilities += [probability]
    i = selectListPosition(probabilities)
    logging.info('Selected: %d', i)
    return objects[i]


def chooseRelevantDescriptionByActivation(workspaceObject):
    descriptions = workspaceObject.relevantDescriptions()
    if not descriptions:
        return None
    activations = [description.descriptor.activation
                   for description in descriptions]
    i = selectListPosition(activations)
    return descriptions[i]


def similarPropertyLinks(slip_node):
    result = []
    for slip_link in slip_node.propertyLinks:
        association = slip_link.degreeOfAssociation() / 100.0
        probability = temperatureAdjustedProbability(association)
        if coinFlip(probability):
            result += [slip_link]
    return result


def chooseSlipnodeByConceptualDepth(slip_nodes):
    if not slip_nodes:
        return None
    depths = [temperatureAdjustedValue(n.conceptualDepth) for n in slip_nodes]
    i = selectListPosition(depths)
    return slip_nodes[i]


def __relevantCategory(objekt, slipnode):
    return objekt.rightBond and objekt.rightBond.category == slipnode


def __relevantDirection(objekt, slipnode):
    return objekt.rightBond and objekt.rightBond.directionCategory == slipnode


def __localRelevance(string, slipnode, relevance):
    numberOfObjectsNotSpanning = numberOfMatches = 0.0
    logging.info("find relevance for a string: %s", string)
    for objekt in string.objects:
        if not objekt.spansString():
            logging.info('non spanner: %s', objekt)
            numberOfObjectsNotSpanning += 1.0
            if relevance(objekt, slipnode):
                numberOfMatches += 1.0
    if numberOfObjectsNotSpanning == 1:
        return 100.0 * numberOfMatches
    return 100.0 * numberOfMatches / (numberOfObjectsNotSpanning - 1.0)


def localBondCategoryRelevance(string, category):
    if len(string.objects) == 1:
        return 0.0
    return __localRelevance(string, category, __relevantCategory)


def localDirectionCategoryRelevance(string, direction):
    return __localRelevance(string, direction, __relevantDirection)


def getMappings(objectFromInitial, objectFromTarget,
                initialDescriptions, targetDescriptions):
    mappings = []
    from conceptMapping import ConceptMapping
    for initial in initialDescriptions:
        for target in targetDescriptions:
            if initial.descriptionType == target.descriptionType:
                if (initial.descriptor == target.descriptor or
                        initial.descriptor.slipLinked(target.descriptor)):
                    mapping = ConceptMapping(
                        initial.descriptionType,
                        target.descriptionType,
                        initial.descriptor,
                        target.descriptor,
                        objectFromInitial,
                        objectFromTarget
                    )
                    mappings += [mapping]
    return mappings
