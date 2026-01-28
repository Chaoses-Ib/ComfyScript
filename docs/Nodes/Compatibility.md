# Node Compatibility
ComfyScript supports all ComfyUI built-in nodes and almost all custom nodes
(except [UI-only JS nodes](#ui-only-js-nodes)).

In fact, built-in nodes and custom nodes are treated in the same way
in ComfyScript.
Both will be loaded on-the-fly and have type stubs (`nodes.pyi`) generated.
Built-in nodes are only specially handled for [global enum](../Runtime.md#global-enums) shorthands.

## UI-only JS nodes
Some nodes you see in the ComfyUI web UI are
not real nodes that will be executed in the server.
They will be removed or converted to other real nodes before
queuing the workflows.

Because these nodes are written in JS and only available in the web UI,
ComfyScript's transpiler and runtime (and all other ComfyUI API-based apps)
cannot access them.
Only some built-in UI nodes are supported by ComfyScript:
`PrimitiveNode`, `Reroute`
(and [`Reroute (rgthree)`](https://github.com/Chaoses-Ib/ComfyScript/issues/42))
and `Note`.

For transpiler, this means some JSON workflows in the web UI format cannot be transpiled to ComfyScript,
you can solve this by:
- Transpiling an image instead.

  Images usually include the API format workflow (if metadata is not disabled).
  If you are transpiling an image, the transpiler will auto fallback to the API format if it fails with the web UI format.

- Exporting the workflow in API format instead.
  
  Load it in the web UI and click `Save (API format)` (enable
  [`Dev Mode` in settings](https://github.com/Chaoses-Ib/ComfyScript/issues/77#issuecomment-2440051129)
  first),
  and try to transpile it instead.

  Note that a few nodes may not support this properly or need some special settings:
  - [chrisgoringe/cg-use-everywhere (UE Nodes) #217](https://github.com/chrisgoringe/cg-use-everywhere/issues/217)
    ([ComfyScript #78](https://github.com/Chaoses-Ib/ComfyScript/issues/78))

    New versions can support `Save (API format)` via some settings.

For runtime, this means those UI-only JS nodes cannot be used.
But most of them won't be useful in Python/ComfyScript anyway.
You can open issues if there are functionalities you miss from JS nodes.
