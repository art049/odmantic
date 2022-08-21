def define_env(env):
    @env.macro
    def async_sync_snippet(folder: str, filename: str, hl_lines=None, linenums=True):
        return f"""
=== "Async"
    ```python {'linenums="1"' if linenums else ''} {'hl_lines="'+hl_lines+'"' if hl_lines is not None else ''}"
    --8<-- "{folder}/async/{filename}"
    ```

=== "Sync"
    ```python {'linenums="1"' if linenums else ''} {'hl_lines="'+hl_lines+'"' if hl_lines is not None else ''}"
    --8<-- "{folder}/sync/{filename}"
    ```
"""
