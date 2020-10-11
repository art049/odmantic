# Filtering
ODMantic uses [QueryExpression][odmantic.query.QueryExpression] objects to handle filter
expressions. These expressions can be built from the comparison operators. It's then
possible to combine multiple expressions using the logical operators. To support the
wide variety of operators provided by MongoDB, it's possible as well to define the
filter 'manually'.

## Comparison operators

There are multiple ways of building [QueryExpression][odmantic.query.QueryExpression]
objects with comparisons operators:

1. Using python comparison operators between the field of the model and the desired value
:   `==`, `!=`, `<=`, `<`, `>=`, `>`

2. Using the functions provided by the `odmantic.query` module
    - [query.eq][odmantic.query.eq]
    - [query.ne][odmantic.query.ne]
    - [query.gt][odmantic.query.gt]
    - [query.gte][odmantic.query.gte]
    - [query.lt][odmantic.query.lt]
    - [query.lte][odmantic.query.lte]
    - [query.in_][odmantic.query.in_]
    - [query.not_in][odmantic.query.not_in]

3. Using methods of the model's field and the desired value
    - `field.eq`
    - `field.ne`
    - `field.gte`
    - `field.gt`
    - `field.lte`
    - `field.lte`
    - `field.in_`
    - `field.not_in`


!!! note "Type checkers"
    Since there is currently not any type checker plugin, the third usage might create
    some errors with type checkers.

### Equal

Filter the trees named "Spruce":
```python linenums="1" hl_lines="9 11 13"
--8<-- "filtering/equal.py"
```
Equivalent raw MongoDB filter:
```json
{"name": "Spruce"}
```

!!! tip "Using equality operators with Enum fields"
    Building filters using `Enum` fields is possible as well.

    ???+example "Example of filter built on an Enum field"
        Filter the 'small' trees:
        ```python linenums="1" hl_lines="6-8 14 17 19 21"
        --8<-- "filtering/enum.py"
        ```
        Equivalent raw MongoDB filter:
        ```json
        {'kind': 'small'}
        ```

    [More details](fields.md#enum-fields) about Enum fields.

### Not Equal

Filter the trees that are **not** named "Spruce":
```python linenums="1" hl_lines="9 11 13"
--8<-- "filtering/not_equal.py"
```
Equivalent raw MongoDB filter:
```json
{"name": {"$ne": "Spruce"}}
```
### Less than (or equal to)

Filter the trees that have a size that is less than (or equal to) 2:
```python linenums="1" hl_lines="9 11 13 16 18 20"
--8<-- "filtering/lt_e.py"
```
Equivalent raw MongoDB filter (less than):
```json
{"average_size": {"$lt": 2}}
```
Equivalent raw MongoDB filter (less than or equal to):
```json
{"average_size": {"$lte": 2}}
```

### Greater than (or equal to)

Filter the trees having a size that is greater than (or equal to) 2:
```python linenums="1" hl_lines="9 11 13 16 18 20"
--8<-- "filtering/gt_e.py"
```
Equivalent raw MongoDB filter (greater than):
```json
{"average_size": {"$gt": 2}}
```
Equivalent raw MongoDB filter (greater than or equal to):
```json
{"average_size": {"$gte": 2}}
```



### Included in

Filter the trees named either "Spruce" or "Pine":
```python linenums="1" hl_lines="9 11"
--8<-- "filtering/in.py"
```
Equivalent raw MongoDB filter:
```json
{"name": {"$in": ["Spruce", "Pine"]}}
```


### Not included in

Filter the trees neither named "Spruce" nor "Pine":
```python linenums="1" hl_lines="9 11"
--8<-- "filtering/not_in.py"
```

Equivalent raw MongoDB filter:
```json
{"name": {"$nin": ["Spruce", "Pine"]}}
```
## Evaluation operators

### Match (Regex)

Filter the trees with a name starting with 'Spruce':
```python linenums="1" hl_lines="8 10"
--8<-- "filtering/match.py"
```

Equivalent raw MongoDB filter:
```json
{"name": {"$regex": "^Spruce"}}
```
## Logical operators
There are two ways of combining [QueryExpression][odmantic.query.QueryExpression]
objects with logical operators:

1. Using python 'bitwise' operators between the field of the model and the desired value
:   `&`, `|`

2. Using the functions provided by the `odmantic.query` module
    - [query.and_][odmantic.query.and_]
    - [query.or_][odmantic.query.or_]
    - [query.nor_][odmantic.query.nor_]

### And

Filter the trees named Spruce (**AND**) with a size less than 2:
```python linenums="1" hl_lines="9 18"
--8<-- "filtering/and.py"
```
Equivalent raw MongoDB filter:
```json
{"name": "Spruce", "size": {"$lte": 2}}}
```

!!! tip "Implicit AND"
    When using [find][odmantic.engine.AIOEngine.find],
    [find_one][odmantic.engine.AIOEngine.find_one] or
    [count][odmantic.engine.AIOEngine.count], you can specify multiple queries as
    positional arguments and those will be implicitly combined with the `AND` operator.

### Or
Filter the trees named Spruce **OR** the trees with a size greater than 2:

```python linenums="1" hl_lines="9 18"
--8<-- "filtering/or.py"
```
Equivalent raw MongoDB filter:
```json
{
  "$or":[
    {"name":"Spruce"},
    {"size":{"$gt":2}}
  ]
}
```
### Nor

Filter the trees neither named Spruce **NOR** bigger than 2 (size):
```python linenums="1" hl_lines="9"
--8<-- "filtering/nor.py"
```
Equivalent raw MongoDB filter:
```json
{
  "$nor":[
    {"name":"Spruce"},
    {"size":{"$gt":2}}
  ]
}
```

!!! tip "NOR Equivalence"
    The following logical expressions are equivalent:

    - A NOR B NOR C
    - NOT(A OR B OR C)
    - NOT(A) AND NOT(B) AND NOT(C)

!!! info "`query.nor_` operator naming"
    [query.and_][odmantic.query.and_] and [query.or_][odmantic.query.or_] require to add
    an extra underscore to avoid overlapping with the python keywords.
    While it could've been possible to name the NOR operator query.nor, the extra underscore has been kept for consistency in the naming of the logical operators.


## Manual filtering
Raw MongoDB filter expressions can be used as well with the
[find][odmantic.engine.AIOEngine.find], [find_one][odmantic.engine.AIOEngine.find_one]
or [count][odmantic.engine.AIOEngine.count] methods.

You can find more details about building raw query filters using the Model in the [Raw
query usage](raw_query_usage.md) section.

## Embedded documents filters

It's possible to build filter based on the content of embedded documents.

```python linenums="1" hl_lines="4 9 12 15 17"
--8<-- "filtering/embedded.py"
```
Equivalent raw MongoDB filters:
```json
{"capital_city.name": {"$eq": "Paris"}}
```
```json
{"capital_city.population": {"$gt": 1000000}}
```


!!! warning "Filtering across References"
    Currently, it is not possible to build filter based on referenced objects.
