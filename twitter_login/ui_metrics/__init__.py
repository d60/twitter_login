import re

import STPyV8

from .dom import MockDocument

FUNCTION_PATTERN = re.compile(r'function [a-zA-Z]+\(\) ({.+})')


def solve_ui_metrics(ui_metrics: str) -> str:
    match = FUNCTION_PATTERN.search(ui_metrics)
    if not match:
        raise ValueError('No function pattern found in ui_metrics input')
    inner_function = match.group(1)

    with STPyV8.JSContext() as ctxt:
        ctxt.locals.document = MockDocument()
        js = '''
        (() => {
            try {
                return JSON.stringify((() => %s)());
            } catch (e) {
                throw new Error();
            }
        })()
        ''' % inner_function
        return ctxt.eval(js)