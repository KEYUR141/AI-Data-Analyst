"""Initial planning subset: one SELECT over one dataset; never executes SQL."""

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

SAFE_FUNCTIONS = {
    "SUM",
    "AVG",
    "MIN",
    "MAX",
    "COUNT",
    "ROUND",
    "ABS",
    "COALESCE",
    "DATE_TRUNC",
    "TIMESTAMP_TRUNC",
    "EXTRACT",
    "CAST",
    "TRY_CAST",
}


class InvalidSQL(ValueError):
    pass


def validate_sql(sql, columns):
    try:
        statements = sqlglot.parse(sql, read="duckdb")
    except ParseError as exc:
        raise InvalidSQL("SQL could not be parsed.") from exc
    if len(statements) != 1 or not isinstance(statements[0], exp.Select):
        raise InvalidSQL("Only a single SELECT is supported.")
    query = statements[0]
    if sum(isinstance(node, exp.Select) for node in query.walk()) != 1:
        raise InvalidSQL("Subqueries and CTEs are not supported yet.")
    if any(query.args.get(key) for key in ["with_", "into", "locks", "joins"]):
        raise InvalidSQL("CTEs, joins, SELECT INTO, and locks are not supported.")
    tables = list(query.find_all(exp.Table))
    if len(tables) != 1 or not isinstance(tables[0].this, exp.Identifier):
        raise InvalidSQL("Query the registered dataset table only.")
    table = tables[0]
    if table.name != "dataset" or table.db or table.catalog:
        raise InvalidSQL("Query the registered dataset table only.")
    for function in query.find_all(exp.Func):
        if isinstance(function, exp.Anonymous) or function.sql_name() not in SAFE_FUNCTIONS:
            raise InvalidSQL("Query uses an unsupported function.")
    aliases = {item.alias for item in query.expressions if item.alias}
    for column in query.find_all(exp.Column):
        if column.table and column.table not in {"dataset", table.alias_or_name}:
            raise InvalidSQL("Invalid table qualifier.")
        if isinstance(column.this, exp.Star):
            continue
        output_alias = (
            column.find_ancestor(exp.Order, exp.Group, exp.Having) is not None and not column.table
        )
        if column.name not in columns and not (output_alias and column.name in aliases):
            raise InvalidSQL("Query references an unknown column.")
    return query.sql(dialect="duckdb")
