import logging

from .coderack import coderack
from .coderack_pressure import coderack_pressures
from .slipnet import slipnet
from .temperature import temperature
from .workspace import workspace
from .workspace_formulas import workspace_formulas


def update_everything():
    workspace.update_everything()
    coderack.update_codelets()
    slipnet.update()
    workspace_formulas.update_temperature()
    coderack_pressures.calculate_pressures()


def main_loop(last_update):
    temperature.try_unclamp()
    result = last_update
    if not coderack.codelets_run:
        update_everything()
        result = coderack.codelets_run
    elif coderack.codelets_run - last_update >= slipnet.time_step_ength:
        update_everything()
        result = coderack.codelets_run
    logging.debug(f"Number of codelets: {len(coderack.codelets)}")
    coderack.choose_and_run_codelet()
    return result


def run_trial(answers):
    """Run a trial of the copycat algorithm"""
    slipnet.reset()
    workspace.reset()
    coderack.reset()
    last_update = 0
    while not workspace.found_answer:
        last_update = main_loop(last_update)
    if workspace.rule:
        answer = workspace.rule.final_answer
    else:
        answer = None
    final_temperature = temperature.value
    final_time = coderack.codelets_run
    logging.info(
        f"Answered {answer} (time {final_time}, final temperature {final_temperature})"
    )
    answers[answer] = answers.get(answer, {"count": 0, "tempsum": 0, "timesum": 0})
    answers[answer]["count"] += 1
    answers[answer]["tempsum"] += final_temperature
    answers[answer]["timesum"] += final_time


def run(initial, modified, target, iterations):
    workspace.set_strings(initial, modified, target)
    answers = {}
    for _ in range(iterations):
        run_trial(answers)
    for _, d in answers.items():
        d["avgtemp"] = d.pop("tempsum") / d["count"]
        d["avgtime"] = d.pop("timesum") / d["count"]
    return answers
