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
        for answer, d in sorted(answers.items(), key=lambda kv: kv[1]["avgtemp"]):
            average_time = round(d['avgtime'] / 1000.0, 2)
            average_temperature = round(d['avgtemp'], 2)
            print(
                f"{answer}: {d['count']} "
                f"(average time {average_time} seconds, average temperature {average_temperature})"
            )
        return 0
    except ValueError:
        print(f"Usage: {program} initial modified target [iterations]", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
