# fred-mlambda

`FRED Micro-Lambda DSL` allows defining and execution small functions in a declarative way.

For examples:

```
${COUNT: example}
```
* Output: `7`

```
${RAND: alice, bob, carol}
```
* Output: `alice` or `bob` or `carol`

Nested expressions are also supported:

```
${COUNT: ${RAND: alice, bob}}
```
* Output: `3` or `5`

## Installation

```bash
$ pip install fred-mlambda
```

## How this works

The main entry point is the `MLambdaParser` class, which can be used to parse and execute a micro-lambda expression. A expression is defined as a string that follows the format `${path.to.function: arg1,arg2,kwarg1=value1,...}`. The function can be referenced by its full import path or by an alias defined in the environment variables.

Consider the following pattern:

```
${path.to.function: arg1, arg2, ..., key1=val1, key2=val2, ...}
```

The parser automatically identifies the following components:
* `import_path`: The import path to the function (e.g., `path.to`)
* `function_name`: The name of the function to execute (e.g., `function`)
* `args`: Positional arguments to pass to the function
* `kwargs`: Keyword arguments to pass to the function

Such that the following is possible in general terms:

```python
from path.to import function

result = function(*args, **kwargs)
```

We also allow providing aliases to faciliate quick reference to the functions. An alias can be defined in the following ways:
* Static definition via the catalog (i.e., `MLambdaCatalog` available at `fred.mlambda.catalog`)
* Dynamic definition via the environment variable `FRED_MLAMBDA_ALIASES` in the following format: `alias=import_path`. Multiple aliases can be defined by using a separator, which by default is `;`.

## Examples

```python
from fred.mlambda.parser import MLambdaParser

# Parse and execute a micro-lambda expression by defining the full import path
out1 = MLambdaParser.from_string("${fred.mlambda._count.count: example}").execute()
print(out1)

# Parse and execute a micro-lambda expression by referencing an existing alias
out2 = MLambdaParser.from_string("${rand: alice, bob, carol}").execute()
print(out2)

# Parse and execute a micro-lambda expression with nested expressions
out3 = MLambdaParser.from_string("${COUNT: ${RAND: alice, bob}}").execute()
print(out3)
```

## Type Coercion

The implementation is designed such that the data types will be inferred automatically. However, it is possible to explicitly define the type of an argument by using the `::` syntax. For example:

```
${count: example::str}
```
* Output: 7

```
${rand: alice, bob, carol, k=2::int}
```
* Output example: `['alice', 'carol']`

The available data-types are:

| Type | Description |
|------|-------------|
| `int` | Integer |
| `float` | Float |
| `bool` | Boolean |
| `str` | String |
