import islpy as isl
from .visitors import TranslatorIsl
import logging

logger = logging.getLogger(__name__)

def calculate_probability(expression):
    translator = TranslatorIsl()
    translator.visit(expression)

    constraint_list = []
    constraint_str = translator.pop()
    if type(constraint_str) is bool:
        return 1.0 if constraint_str else 0.0
    constraint_list.append(simplify_constraint(constraint_str))

    while constraint_str is not None:
        constraint_str = translator.pop()
        if constraint_str is not None:
            constraint_list.append(simplify_constraint(constraint_str))

    constraint_string = " and ".join(constraint_list)
    variable_string = ", ".join(translator.isl_variables)

    range_string = ""
    for var in translator.isl_variables:
        range_string += "-2147483648 <= " + var + " <= 2147483647 and "

    range_string = range_string[:-5]

    set_string = "{[" + variable_string + "] : " + range_string + "}"
    domain = isl.Set(set_string)
    constraint = "{[" + variable_string + "] : " + constraint_string + "}"
    logger.debug("isl constraint: " + constraint)

    if "bitops" in constraint:
        return 1.0
    domain_str = domain.card().to_str()
    domain_count = int(domain_str[2:-2])

    try:
        constraint_set = isl.Set(constraint).intersect(domain)
        result_str = constraint_set.card().to_str()
        count = int(result_str[2:-2])
    except Exception:
        count = 1

    probability = count / domain_count
    logger.debug("current constraint probability: " + str(probability))

    return probability


def simplify_constraint(constraint_str):
    constraint_str = constraint_str[1:-1]
    if constraint_str[:8] == "NOT (NOT":
        constraint_str = constraint_str[10:-2]

    return constraint_str

