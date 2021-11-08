import inspect
import logging
import math
import random
import re

from . import formulas
from . import workspace_formulas
from .codelet import Codelet
from .coderack_pressure import CoderackPressures
from .slipnet import slipnet

NUMBER_OF_BINS = 7
MAX_NUMBER_OF_CODELETS = 100


def get_urgency_bin(urgency):
    i = int(urgency) * NUMBER_OF_BINS / 100
    if i >= NUMBER_OF_BINS:
        return NUMBER_OF_BINS
    return i + 1


class CodeRack:
    def __init__(self):
        self.speed_up_bonds = False
        self.remove_breaker_codelets = False
        self.remove_terraced_scan = False
        self.pressures = CoderackPressures()
        self.pressures.initialise_pressures()
        self.reset()
        self.initial_codelet_names = (
            "bottom-up-bond-scout",
            "replacement-finder",
            "bottom-up-correspondence-scout",
        )
        self.codelet_methods_dir = None
        self.run_codelets = {}
        self.postings = {}

    def reset(self):
        from .temperature import temperature

        self.codelets = []
        self.codelets_run = 0
        temperature.clamped = True
        self.pressures.reset()

    def update_codelets(self):
        if self.codelets_run > 0:
            self.post_top_down_codelets()
            self.post_bottom_up_codelets()

    def post(self, codelet):
        self.postings[codelet.name] = self.postings.get(codelet.name, 0) + 1
        self.pressures.add_codelet(codelet)
        self.codelets += [codelet]
        if len(self.codelets) > 100:
            old_codelet = self.choose_old_codelet()
            self.remove_codelet(old_codelet)

    def post_top_down_codelets(self):
        for node in slipnet.slipnodes:
            logging.info(f"Trying slipnode: {node}")
            if node.activation != 100.0:
                continue
            logging.info(f"Using slipnode: {node}")
            for codelet_name in node.codelets:
                probability = workspace_formulas.probability_of_posting(codelet_name)
                how_many = workspace_formulas.how_many_to_post(codelet_name)
                for _ in range(0, how_many):
                    if random.random() >= probability:
                        continue
                    urgency = get_urgency_bin(
                        node.activation * node.conceptual_depth / 100.0
                    )
                    codelet = Codelet(codelet_name, urgency, self.codelets_run)
                    codelet.arguments += [node]
                    logging.info(f"Post top down: {codelet}, with urgency: {urgency}")
                    self.post(codelet)

    def post_bottom_up_codelets(self):
        logging.info("posting bottom up codelets")
        self.__post_bottom_up_codelets("bottom-up-description-scout")
        self.__post_bottom_up_codelets("bottom-up-bond-scout")
        self.__post_bottom_up_codelets("group-scout--whole-string")
        self.__post_bottom_up_codelets("bottom-up-correspondence-scout")
        self.__post_bottom_up_codelets("important-object-correspondence-scout")
        self.__post_bottom_up_codelets("replacement-finder")
        self.__post_bottom_up_codelets("rule-scout")
        self.__post_bottom_up_codelets("rule-translator")
        if not self.remove_breaker_codelets:
            self.__post_bottom_up_codelets("breaker")

    def __post_bottom_up_codelets(self, codelet_name):
        probability = workspace_formulas.probability_of_posting(codelet_name)
        how_many = workspace_formulas.how_many_to_post(codelet_name)
        if self.speed_up_bonds:
            if "bond" in codelet_name or "group" in codelet_name:
                how_many *= 3
        urgency = 3
        if codelet_name == "breaker":
            urgency = 1
        if formulas.Temperature < 25.0 and "translator" in codelet_name:
            urgency = 5
        for _ in range(0, how_many):
            if random.random() < probability:
                codelet = Codelet(codelet_name, urgency, self.codelets_run)
                self.post(codelet)

    def remove_codelet(self, codelet):
        self.codelets.remove(codelet)
        self.pressures.remove_codelet(codelet)

    def new_codelet(self, name, old_codelet, strength, arguments=None):
        logging.debug(f"Posting new codelet called {name}")
        urgency = get_urgency_bin(strength)
        new_codelet = Codelet(name, urgency, self.codelets_run)
        if arguments:
            new_codelet.arguments = [arguments]
        else:
            new_codelet.arguments = old_codelet.arguments
        new_codelet.pressure = old_codelet.pressure
        self.try_run(new_codelet)

    def propose_rule(self, facet, description, category, relation, old_codelet):
        """Creates a proposed rule, and posts a rule-strength-tester codelet.

        The new codelet has urgency a function of
            the degree of conceptual-depth of the descriptions in the rule
        """
        from .rule import Rule

        rule = Rule(facet, description, category, relation)
        rule.update_strength()
        if description and relation:
            depths = description.conceptual_depth + relation.conceptual_depth
            depths /= 200.0
            urgency = math.sqrt(depths) * 100.0
        else:
            urgency = 0
        self.new_codelet("rule-strength-tester", old_codelet, urgency, rule)

    def propose_correspondence(
        self,
        initial_object,
        target_object,
        concept_mappings,
        flip_target_object,
        old_codelet,
    ):
        from .correspondence import Correspondence

        correspondence = Correspondence(
            initial_object, target_object, concept_mappings, flip_target_object
        )
        for mapping in concept_mappings:
            mapping.initial_description_type.buffer = 100.0
            mapping.initial_descriptor.buffer = 100.0
            mapping.target_description_type.buffer = 100.0
            mapping.target_descriptor.buffer = 100.0
        mappings = correspondence.distinguishing_concept_mappings()
        urgency = sum(mapping.strength() for mapping in mappings)
        number_of_mappings = len(mappings)
        if urgency:
            urgency /= number_of_mappings
        binn = get_urgency_bin(urgency)
        logging.info(f"urgency: {urgency}, number: {number_of_mappings}, bin: {binn}")
        self.new_codelet(
            "correspondence-strength-tester", old_codelet, urgency, correspondence
        )

    def propose_description(self, objekt, type_, descriptor, old_codelet):
        from .description import Description

        description = Description(objekt, type_, descriptor)
        descriptor.buffer = 100.0
        urgency = type_.activation
        self.new_codelet(
            "description-strength-tester", old_codelet, urgency, description
        )

    def propose_single_letter_group(self, source, codelet):
        self.propose_group(
            [source], [], slipnet.sameness_group, None, slipnet.letter_category, codelet
        )

    def propose_group(
        self,
        objects,
        bond_list,
        group_category,
        direction_category,
        bond_facet,
        old_codelet,
    ):
        from .group import Group

        bond_category = group_category.get_related_node(slipnet.bond_category)
        bond_category.buffer = 100.0
        if direction_category:
            direction_category.buffer = 100.0
        group = Group(
            objects[0].string,
            group_category,
            direction_category,
            bond_facet,
            objects,
            bond_list,
        )
        urgency = bond_category.bond_degree_of_association()
        self.new_codelet("group-strength-tester", old_codelet, urgency, group)

    def propose_bond(
        self,
        source,
        destination,
        bond_category,
        bond_facet,
        source_descriptor,
        destination_descriptor,
        old_codelet,
    ):
        from .bond import Bond

        bond_facet.buffer = 100.0
        source_descriptor.buffer = 100.0
        destination_descriptor.buffer = 100.0
        bond = Bond(
            source,
            destination,
            bond_category,
            bond_facet,
            source_descriptor,
            destination_descriptor,
        )
        urgency = bond_category.bond_degree_of_association()
        self.new_codelet("bond-strength-tester", old_codelet, urgency, bond)

    def choose_old_codelet(self):
        # selects an old codelet to remove from the coderack
        # more likely to select lower urgency codelets
        if not len(self.codelets):
            return None
        urgencies = []
        for codelet in self.codelets:
            urgency = (coderack.codelets_run - codelet.timestamp) * (
                7.5 - codelet.urgency
            )
            urgencies += [urgency]
        threshold = random.random() * sum(urgencies)
        sum_of_urgencies = 0.0
        for i in range(0, len(self.codelets)):
            sum_of_urgencies += urgencies[i]
            if sum_of_urgencies > threshold:
                return self.codelets[i]
        return self.codelets[0]

    def post_initial_codelets(self):
        for name in self.initial_codelet_names:
            for _ in range(0, workspace_formulas.number_of_objects()):
                codelet = Codelet(name, 1, self.codelets_run)
                self.post(codelet)
                codelet2 = Codelet(name, 1, self.codelets_run)
                self.post(codelet2)

    def try_run(self, new_codelet):
        if self.remove_terraced_scan:
            self.run(new_codelet)
        else:
            self.post(new_codelet)

    def get_codeletmethods(self):
        from . import codelet_methods

        self.codelet_methods_dir = dir(codelet_methods)
        known_codelet_names = (
            "breaker",
            "bottom-up-description-scout",
            "top-down-description-scout",
            "description-strength-tester",
            "description-builder",
            "bottom-up-bond-scout",
            "top-down-bond-scout--category",
            "top-down-bond-scout--direction",
            "bond-strength-tester",
            "bond-builder",
            "top-down-group-scout--category",
            "top-down-group-scout--direction",
            "group-scout--whole-string",
            "group-strength-tester",
            "group-builder",
            "replacement-finder",
            "rule-scout",
            "rule-strength-tester",
            "rule-builder",
            "rule-translator",
            "bottom-up-correspondence-scout",
            "important-object-correspondence-scout",
            "correspondence-strength-tester",
            "correspondence-builder",
        )
        self.methods = {}
        for codelet_name in known_codelet_names:
            method_name = re.sub("[ -]", "_", codelet_name)
            if method_name not in self.codelet_methods_dir:
                raise NotImplementedError(
                    f"Cannot find {method_name} in codelet_methods"
                )
            method = getattr(codelet_methods, method_name)
            self.methods[method_name] = method

    def choose_and_run_codelet(self):
        if not len(coderack.codelets):
            coderack.post_initial_codelets()
        codelet = self.choose_codelet_to_run()
        if codelet:
            self.run(codelet)

    def choose_codelet_to_run(self):
        if not self.codelets:
            return None
        temp = formulas.Temperature
        scale = (100.0 - temp + 10.0) / 15.0
        urgsum = 0.0
        for codelet in self.codelets:
            urg = codelet.urgency ** scale
            urgsum += urg
        r = random.random()
        threshold = r * urgsum
        chosen = None
        urgency_sum = 0.0
        formulas.log_temperature()
        formulas.log_actual_temperature()
        logging.info("Slipnet:")
        for node in slipnet.slipnodes:
            logging.info(
                f"\tnode {node.get_name()}, activation: {node.activation}, "
                f"buffer: {node.buffer}, depth: {node.conceptual_depth}"
            )
        logging.info("Coderack:")
        for codelet in self.codelets:
            logging.info(f"\t{codelet.name}, {codelet.urgency}")
        from .workspace import workspace

        workspace.initial.log("Initial: ")
        workspace.target.log("Target: ")
        for codelet in self.codelets:
            urgency_sum += codelet.urgency ** scale
            if not chosen and urgency_sum > threshold:
                chosen = codelet
                break
        if not chosen:
            chosen = self.codelets[0]
        self.remove_codelet(chosen)
        logging.info(f"chosen codelet:\n\t{chosen.name}, urgency = {chosen.urgency}")
        return chosen

    def run(self, codelet):
        method_name = re.sub("[ -]", "_", codelet.name)
        self.codelets_run += 1
        self.run_codelets[method_name] = self.run_codelets.get(method_name, 0) + 1

        if not self.codelet_methods_dir:
            self.get_codeletmethods()
        method = self.methods[method_name]
        if not method:
            raise ValueError(
                f"Found {method_name} in codelet_methods, but cannot get it"
            )
        if not callable(method):
            raise RuntimeError(f"Cannot call {method_name}()")
        args, _varargs, _varkw, _defaults = inspect.getargspec(method)
        try:
            if "codelet" in args:
                method(codelet)
            else:
                method()
        except AssertionError:
            pass


coderack = CodeRack()
