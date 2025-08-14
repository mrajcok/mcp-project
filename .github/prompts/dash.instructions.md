
---
applyTo: "**/*.py"
---
# Dash Callbacks Best Practices

- **Dash Callbacks Best Practices**: When generating Dash (Plotly) code, always ensure that each component-property pair (e.g., Output('my-graph', 'figure')) is used as an output in exactly ONE callback. Duplicate outputs across multiple callbacks will cause errors like "Duplicate callback outputs". If multiple callbacks need to affect the same property, consolidate them into a single callback using `dash.callback_context` (or `ctx`) to check which input triggered the update via `ctx.triggered_id` or `ctx.triggered`.

- **Handle Initial Callback Execution**: Use `prevent_initial_call=True` in `@callback` decorators to avoid running callbacks on app load unless explicitly needed. This prevents unwanted initial updates, especially for components like buttons or inputs that start with default values.

- **Error Handling in Callbacks**: Raise `dash.exceptions.PreventUpdate` to skip updating all outputs in a callback (e.g., if inputs are invalid or None). Use `dash.no_update` to skip updating specific outputs while updating others (return it in place of a value for that output).

- **Determine Triggering Input**: In callbacks with multiple inputs, always import and use `dash.callback_context` (as `ctx`) to inspect `ctx.triggered_id`, `ctx.triggered`, or `ctx.inputs` to handle logic based on which input changed. This avoids race conditions or incorrect assumptions.

- **Circular Callbacks**: Only use circular callbacks (where a callback updates an input of itself) if synchronizing components (e.g., slider and text input). Limit to a single callback for the chain; multi-callback circular chains are not supported.

- **No Outputs or Direct Updates**: For callbacks without outputs (e.g., side effects like saving data), omit the Output in the decorator and avoid return statements. Use `set_props(component_id, {'property': value})` to update properties directly without declaring them as outputs, but prefer outputs for clarity and debugging.

- **Performance and Async**: For expensive computations, use memoization with `@functools.lru_cache`. For async/await in callbacks, add `pip install "dash[async]"` and ensure the server supports it (e.g., gunicorn with gthread workers). Avoid blocking operations; use `asyncio.gather` for parallel async tasks.

- **Optional Inputs/States**: If components might not exist (e.g., conditionally rendered), use `allow_optional=True` for Inputs/States to receive `None` instead of errors.

- **Running State**: Use the `running` parameter in `@callback` to disable/enable components (e.g., buttons) during execution, like `running=[(Output('button', 'disabled'), True, False)]`.

- **Validate Callback Signatures**: Ensure callback function arguments match the order of Inputs/States in the decorator. Use type hints or comments for clarity. Test for common errors like mismatched input/output counts.
