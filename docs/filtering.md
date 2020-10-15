# Filtering
QueryExpression
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

!!! tip "Using equality operators with Enum fields"
    enum query example

!!! tip "Embedded documents queries"
    enum query example


### Equal

```python linenums="1" hl_lines="9 11 13"
--8<-- "filtering/equal.py"
```

> Filter the trees named "Spruce".

### Not Equal

```python linenums="1" hl_lines="9 11 13"
--8<-- "filtering/not_equal.py"
```
> Filter the trees that are **not** named "Spruce".

### Less than (or equal to)

```python linenums="1" hl_lines="9 11 13 16 18 20"
--8<-- "filtering/lt_e.py"
```

> Filter the trees that have a size that is less than (or equal to)  2.


### Greater than (or equal to)

```python linenums="1" hl_lines="9 11 13 16 18 20"
--8<-- "filtering/gt_e.py"
```

> Filter the trees having a size that is greater than (or equal to) 2.


### Included in

```python linenums="1" hl_lines="9 11"
--8<-- "filtering/in.py"
```
> Filter the trees named either "Spruce" or "Pine".

### Not included in

```python linenums="1" hl_lines="9 11"
--8<-- "filtering/not_in.py"
```
> Filter the trees neither named "Spruce" nor "Pine".

## Evaluation operators

### Match (Regex)

```python linenums="1" hl_lines="8 10"
--8<-- "filtering/match.py"
```
> Filter the trees with a name starting with "Spruce".

## Logical operators

### And

```python linenums="1" hl_lines="9 18"
--8<-- "filtering/and.py"
```

> Filter the trees named Spruce with a size less than 2.

!!! tip "Implicit AND"
    When using [find][odmantic.engine.AIOEngine.find],
    [find_one][odmantic.engine.AIOEngine.find_one] or
    [count][odmantic.engine.AIOEngine.count], you can specify multiple queries as
    positional arguments and those will be implicitly combined with the `AND` operator.

### Or

```python linenums="1" hl_lines="9 11"
--8<-- "filtering/or.py"
```

### Nor

```python linenums="1" hl_lines="9 11"
--8<-- "filtering/nor.py"
```

## Manual filtering
