"""Run the copycat program"""
import logging
import sys

from . import copycat


def main():
    """Run the program"""
    logging.basicConfig(
        level=logging.WARN, format="%(message)s", filename="./copycat.log", filemode="w"
    )

    program, *args = sys.argv
    try:
        if len(args) == 4:
            initial, modified, target = args[:-1]
            iterations = int(args[-1])
        else:
            initial, modified, target = args
            iterations = 1
        answers = copycat.run(initial, modified, target, iterations)
        for answer, values in sorted(answers.items(), key=lambda kv: kv[1]["avgtemp"]):
            average_time = round(values["avgtime"] / 1000.0, 2)
            average_temperature = round(values["avgtemp"], 2)
            print(
                f"{answer}: {values['count']} "
                f"(average time {average_time} seconds, "
                f"average temperature {average_temperature})"
            )
        return 0
    except ValueError:
        print(f"Usage: {program} initial modified target [iterations]", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
